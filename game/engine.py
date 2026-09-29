"""
Core endless runner game loop, state transitions, scoring, and world updates.
Coordinates player, obstacles, perspective camera, and input handling.
"""

from enum import Enum, auto
from typing import List
import pygame

from config.settings import (
    DEBUG_MODE,
    PLAYER_RUN_SPEED_INITIAL,
    PLAYER_MAX_SPEED,
    PLAYER_SPEED_ACCELERATION,
)
from game.lane import Camera3D, LaneRenderer
from game.player import Player
from game.obstacle import ObstacleManager
from game.input_handler import InputHandler
from gestures.state import GameAction, GestureStateResult


class GameState(Enum):
    """Finite state machine states for the runner."""
    MAIN_MENU = auto()
    PLAYING = auto()
    GAME_OVER = auto()


class GameEngine:
    """
    Coordinates gameplay simulation, world updates, and state transitions.
    """

    def __init__(self):
        self.state = GameState.MAIN_MENU
        self.debug_mode = DEBUG_MODE

        # Scoring & Progress
        self.score: float = 0.0
        self.high_score: float = 0.0
        self.distance: float = 0.0
        self.speed: float = PLAYER_RUN_SPEED_INITIAL

        # Core World Entities
        self.camera = Camera3D()
        self.lane_renderer = LaneRenderer(self.camera)
        self.player = Player()
        self.obstacle_manager = ObstacleManager()
        self.input_handler = InputHandler()

    def start_new_game(self) -> None:
        """Reset world entities and variables for a fresh run."""
        self.score = 0.0
        self.distance = 0.0
        self.speed = PLAYER_RUN_SPEED_INITIAL
        self.player.reset()
        self.obstacle_manager.reset()
        self.state = GameState.PLAYING

    def update(
        self,
        dt: float,
        pygame_events: List[pygame.event.Event],
        gesture_result: GestureStateResult,
    ) -> None:
        """Advance game simulation by dt seconds."""
        # 1. Process inputs from keyboard and gestures
        actions, is_sliding = self.input_handler.process_events(pygame_events, gesture_result)

        # Handle global toggles
        if self.input_handler.toggle_debug_requested:
            self.debug_mode = not self.debug_mode

        # 2. State-specific behavior
        if self.state == GameState.MAIN_MENU:
            if self.input_handler.start_or_restart_requested or GameAction.JUMP in actions:
                self.start_new_game()

        elif self.state == GameState.PLAYING:
            # Dispatch game actions to player
            for action in actions:
                if action == GameAction.MOVE_LEFT:
                    self.player.move_left()
                elif action == GameAction.MOVE_RIGHT:
                    self.player.move_right()
                elif action == GameAction.JUMP:
                    self.player.jump()
                elif action == GameAction.SLIDE:
                    self.player.start_slide()

            # Continuous sliding state (crouching)
            self.player.set_slide_state(is_sliding)

            # Advance player physics
            self.player.update(dt)

            # Gradually increase speed over time
            self.speed = min(
                PLAYER_MAX_SPEED,
                self.speed + PLAYER_SPEED_ACCELERATION * dt,
            )

            # Accumulate distance and score
            self.distance += self.speed * dt
            self.score += self.speed * dt * 0.5

            # Advance track visual motion
            self.lane_renderer.update(self.speed, dt)

            # Advance obstacles and evaluate collision
            collision = self.obstacle_manager.update(self.speed, dt, self.player)
            if collision:
                if self.score > self.high_score:
                    self.high_score = self.score
                self.state = GameState.GAME_OVER

        elif self.state == GameState.GAME_OVER:
            if self.input_handler.start_or_restart_requested or GameAction.JUMP in actions:
                self.start_new_game()

    def render_world(self, surface: pygame.Surface) -> None:
        """Render 3D game scene (sky, track, obstacles, player)."""
        self.lane_renderer.draw_background(surface)
        self.lane_renderer.draw_track(surface)
        self.obstacle_manager.draw(surface, self.camera)
        self.player.draw(surface, self.camera)
