"""
Player entity with 3-lane movement, jump physics, slide crouching, and 3D hitbox.
"""

from typing import Tuple
import pygame

from config.settings import (
    LANE_WIDTH,
    LANE_SWITCH_SPEED,
    JUMP_VELOCITY,
    GRAVITY,
    PLAYER_WIDTH,
    PLAYER_HEIGHT_STAND,
    PLAYER_HEIGHT_SLIDE,
    PLAYER_BASE_Z,
    COLOR_PLAYER,
    COLOR_PLAYER_OUTLINE,
)
from game.lane import Camera3D, draw_projected_box


class Player:
    """
    Runner entity that navigates 3 lanes, jumps over hurdles, and slides under barriers.
    """

    def __init__(self):
        self.lane: int = 0          # Target lane index (-1 = Left, 0 = Center, 1 = Right)
        self.world_x: float = 0.0   # Current interpolated world X
        self.world_y: float = 0.0   # Current vertical height above ground
        self.velocity_y: float = 0.0
        self.z: float = PLAYER_BASE_Z
        self.depth: float = 1.0     # Z depth of player box

        # Movement states
        self.is_grounded: bool = True
        self.is_jumping: bool = False
        self.is_sliding: bool = False
        self.slide_timer: float = 0.0

    def reset(self) -> None:
        """Reset player state for a new game run."""
        self.lane = 0
        self.world_x = 0.0
        self.world_y = 0.0
        self.velocity_y = 0.0
        self.is_grounded = True
        self.is_jumping = False
        self.is_sliding = False
        self.slide_timer = 0.0

    def move_left(self) -> bool:
        """Move one lane to the left if not at left boundary."""
        if self.lane > -1:
            self.lane -= 1
            return True
        return False

    def move_right(self) -> bool:
        """Move one lane to the right if not at right boundary."""
        if self.lane < 1:
            self.lane += 1
            return True
        return False

    def jump(self) -> bool:
        """Trigger upward jump if on the ground."""
        if self.is_grounded and not self.is_sliding:
            self.velocity_y = JUMP_VELOCITY
            self.is_grounded = False
            self.is_jumping = True
            return True
        return False

    def start_slide(self, duration: float = 0.65) -> None:
        """Initiate sliding / ducking crouch."""
        if self.is_grounded:
            self.is_sliding = True
            self.slide_timer = max(self.slide_timer, duration)

    def set_slide_state(self, sliding: bool) -> None:
        """Update continuous sliding state from pose gesture."""
        if self.is_grounded:
            if sliding:
                self.is_sliding = True
            elif self.slide_timer <= 0.0:
                self.is_sliding = False

    def update(self, dt: float) -> None:
        """Advance player physics, lane smoothing, and jump/slide timers."""
        # 1. Smooth horizontal lane movement (exponential lerp)
        target_x = self.lane * LANE_WIDTH
        dx = target_x - self.world_x
        self.world_x += dx * min(1.0, LANE_SWITCH_SPEED * dt)

        # 2. Vertical Jump Physics
        if not self.is_grounded:
            self.world_y += self.velocity_y * dt
            self.velocity_y -= GRAVITY * dt
            if self.world_y <= 0.0:
                self.world_y = 0.0
                self.velocity_y = 0.0
                self.is_grounded = True
                self.is_jumping = False

        # 3. Slide decay timer
        if self.slide_timer > 0.0:
            self.slide_timer -= dt
            if self.slide_timer <= 0.0 and not self.is_sliding:
                self.is_sliding = False

    @property
    def current_height(self) -> float:
        """Dynamic height of player based on standing vs. sliding."""
        return PLAYER_HEIGHT_SLIDE if self.is_sliding else PLAYER_HEIGHT_STAND

    def get_hitbox_bounds(self) -> Tuple[float, float, float, float, float, float]:
        """
        Returns 3D bounding box (min_x, max_x, min_y, max_y, min_z, max_z).
        """
        half_w = PLAYER_WIDTH * 0.45
        min_x = self.world_x - half_w
        max_x = self.world_x + half_w
        min_y = self.world_y
        max_y = self.world_y + self.current_height
        half_d = self.depth * 0.45
        min_z = self.z - half_d
        max_z = self.z + half_d
        return min_x, max_x, min_y, max_y, min_z, max_z

    def draw(self, surface: pygame.Surface, camera: Camera3D) -> None:
        """Render player cuboid in 3D perspective."""
        h = self.current_height
        w = PLAYER_WIDTH
        d = self.depth

        # Dynamic shading based on state
        if self.is_sliding:
            c_front = (40, 210, 240)
            c_top = (100, 240, 255)
            c_side = (25, 170, 200)
        elif self.is_jumping:
            c_front = (70, 220, 160)
            c_top = (130, 255, 200)
            c_side = (40, 180, 130)
        else:
            c_front = COLOR_PLAYER
            c_top = (100, 205, 255)
            c_side = COLOR_PLAYER_OUTLINE

        draw_projected_box(
            surface=surface,
            camera=camera,
            center_x=self.world_x,
            base_y=self.world_y,
            center_z=self.z,
            width=w,
            height=h,
            depth=d,
            color_front=c_front,
            color_top=c_top,
            color_side=c_side,
            shadow=True,
        )
