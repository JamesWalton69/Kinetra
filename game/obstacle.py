"""
Obstacle definitions, procedural spawner, and 3D collision detection.
Provides Hurdle (jump), Overhead (slide), and Barrier (lane dodge) obstacles.
"""

from enum import Enum, auto
import random
from typing import List, Tuple
import pygame

from config.settings import (
    LANE_WIDTH,
    LANE_INDICES,
    TRACK_LENGTH,
    HURDLE_HEIGHT,
    OVERHEAD_MIN_Y,
    OVERHEAD_MAX_Y,
    BARRIER_HEIGHT,
    MIN_OBSTACLE_Z_SPACING,
    OBSTACLE_SPAWN_INTERVAL_MIN,
    OBSTACLE_SPAWN_INTERVAL_MAX,
    COLOR_OBSTACLE_HURDLE,
    COLOR_OBSTACLE_OVERHEAD,
    COLOR_OBSTACLE_BARRIER,
)
from game.lane import Camera3D, draw_projected_box
from game.player import Player


class ObstacleType(Enum):
    """Primitive obstacle types requiring specific player maneuvers."""
    HURDLE = auto()    # Low obstacle -> must JUMP
    OVERHEAD = auto()  # High banner -> must SLIDE
    BARRIER = auto()   # Full roadblock -> must MOVE LEFT/RIGHT


class Obstacle:
    """A single 3D obstacle stationed in a track lane."""

    def __init__(self, obstacle_type: ObstacleType, lane: int, z: float):
        self.type = obstacle_type
        self.lane = lane
        self.z = z
        self.width = LANE_WIDTH * 0.85
        self.depth = 1.0

        # Define vertical bounds based on archetype
        if self.type == ObstacleType.HURDLE:
            self.base_y = 0.0
            self.height = HURDLE_HEIGHT
            self.color_front = COLOR_OBSTACLE_HURDLE
            self.color_top = (255, 195, 80)
            self.color_side = (200, 130, 20)
        elif self.type == ObstacleType.OVERHEAD:
            self.base_y = OVERHEAD_MIN_Y
            self.height = OVERHEAD_MAX_Y - OVERHEAD_MIN_Y
            self.color_front = COLOR_OBSTACLE_OVERHEAD
            self.color_top = (80, 240, 240)
            self.color_side = (0, 160, 160)
        else:  # ObstacleType.BARRIER
            self.base_y = 0.0
            self.height = BARRIER_HEIGHT
            self.color_front = COLOR_OBSTACLE_BARRIER
            self.color_top = (255, 100, 100)
            self.color_side = (180, 40, 40)

    @property
    def world_x(self) -> float:
        return self.lane * LANE_WIDTH

    def update(self, speed: float, dt: float) -> None:
        """Move obstacle towards the camera."""
        self.z -= speed * dt

    def get_hitbox_bounds(self) -> Tuple[float, float, float, float, float, float]:
        """Returns 3D bounding box (min_x, max_x, min_y, max_y, min_z, max_z)."""
        half_w = self.width * 0.45
        min_x = self.world_x - half_w
        max_x = self.world_x + half_w
        min_y = self.base_y
        max_y = self.base_y + self.height
        half_d = self.depth * 0.45
        min_z = self.z - half_d
        max_z = self.z + half_d
        return min_x, max_x, min_y, max_y, min_z, max_z

    def check_collision(self, player: Player) -> bool:
        """
        Calculates 3D Axis-Aligned Bounding Box (AABB) intersection with player.
        """
        px1, px2, py1, py2, pz1, pz2 = player.get_hitbox_bounds()
        ox1, ox2, oy1, oy2, oz1, oz2 = self.get_hitbox_bounds()

        # Check for non-overlap along any axis
        if px2 < ox1 or px1 > ox2:
            return False
        if py2 < oy1 or py1 > oy2:
            return False
        if pz2 < oz1 or pz1 > oz2:
            return False

        return True

    def draw(self, surface: pygame.Surface, camera: Camera3D) -> None:
        """Render obstacle cuboid in 3D perspective."""
        # For overhead barriers, draw supporting vertical posts down to the ground
        if self.type == ObstacleType.OVERHEAD:
            post_w = 0.15
            half_w = self.width * 0.5
            # Left post
            draw_projected_box(
                surface, camera, self.world_x - half_w, 0.0, self.z,
                post_w, self.base_y, 0.2, (90, 100, 115), (120, 130, 145), (70, 80, 95), shadow=False
            )
            # Right post
            draw_projected_box(
                surface, camera, self.world_x + half_w, 0.0, self.z,
                post_w, self.base_y, 0.2, (90, 100, 115), (120, 130, 145), (70, 80, 95), shadow=False
            )

        draw_projected_box(
            surface=surface,
            camera=camera,
            center_x=self.world_x,
            base_y=self.base_y,
            center_z=self.z,
            width=self.width,
            height=self.height,
            depth=self.depth,
            color_front=self.color_front,
            color_top=self.color_top,
            color_side=self.color_side,
            shadow=(self.type != ObstacleType.OVERHEAD),
        )


class ObstacleManager:
    """
    Manages obstacle spawning intervals, movement updates, pruning,
    and collision checking against the player.
    """

    def __init__(self):
        self.obstacles: List[Obstacle] = []
        self._spawn_timer: float = 1.0

    def reset(self) -> None:
        """Clear all active obstacles and reset timer."""
        self.obstacles.clear()
        self._spawn_timer = 1.5

    def update(self, speed: float, dt: float, player: Player) -> bool:
        """
        Advance obstacles and check collisions.
        Returns True if a collision occurred (Game Over).
        """
        self._spawn_timer -= dt

        # Spawn new obstacle wave
        if self._spawn_timer <= 0.0:
            self._spawn_wave()
            interval = random.uniform(OBSTACLE_SPAWN_INTERVAL_MIN, OBSTACLE_SPAWN_INTERVAL_MAX)
            # Adjust interval as speed increases
            self._spawn_timer = max(0.9, interval * (16.0 / max(16.0, speed)))

        # Update active obstacles and check collision
        collision = False
        remaining: List[Obstacle] = []

        for obs in self.obstacles:
            obs.update(speed, dt)

            # Check collision with player
            if obs.check_collision(player):
                collision = True

            # Keep obstacles that are still in front of camera view
            if obs.z > -4.0:
                remaining.append(obs)

        self.obstacles = remaining
        return collision

    def _spawn_wave(self) -> None:
        """
        Generates 1 or 2 obstacles in random lanes, ensuring at least one
        clear path or traversable action exists.
        """
        # Ensure minimum distance from the furthest existing obstacle
        if self.obstacles:
            furthest_z = max(obs.z for obs in self.obstacles)
            if TRACK_LENGTH - furthest_z < MIN_OBSTACLE_Z_SPACING:
                return

        # Choose 1 or 2 lanes (never block all 3 with impassable barriers)
        available_lanes = LANE_INDICES.copy()
        random.shuffle(available_lanes)
        num_obstacles = 1 if random.random() < 0.65 else 2

        chosen_lanes = available_lanes[:num_obstacles]

        for lane in chosen_lanes:
            # Pick archetype: Hurdle (Jump), Overhead (Slide), Barrier (Dodge)
            r = random.random()
            if r < 0.38:
                obs_type = ObstacleType.HURDLE
            elif r < 0.72:
                obs_type = ObstacleType.OVERHEAD
            else:
                obs_type = ObstacleType.BARRIER

            self.obstacles.append(Obstacle(obs_type, lane, TRACK_LENGTH))

    def draw(self, surface: pygame.Surface, camera: Camera3D) -> None:
        """Draw obstacles in back-to-front depth order."""
        # Sort by distance Z descending so furthest obstacles render first
        sorted_obstacles = sorted(self.obstacles, key=lambda o: o.z, reverse=True)
        for obs in sorted_obstacles:
            obs.draw(surface, camera)
