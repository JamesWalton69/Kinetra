"""
Unified input handler consolidating webcam pose gestures and keyboard fallback.
Dispatches discrete game actions and continuous movement states to the game engine.
"""

from typing import List, Tuple
import pygame

from gestures.state import GameAction, GestureStateResult


class InputHandler:
    """
    Combines keyboard events with pose gesture detections.
    Provides uniform controls regardless of whether input arrives via webcam or keyboard.
    """

    def __init__(self):
        self.toggle_debug_requested = False
        self.recalibrate_requested = False
        self.start_or_restart_requested = False

    def process_events(
        self,
        events: List[pygame.event.Event],
        gesture_result: GestureStateResult,
    ) -> Tuple[List[GameAction], bool]:
        """
        Processes pygame window events and merges keyboard fallback with detected gestures.
        Returns:
            (actions_list, is_sliding_state)
        """
        actions: List[GameAction] = []
        keyboard_sliding = False

        self.toggle_debug_requested = False
        self.recalibrate_requested = False
        self.start_or_restart_requested = False

        # Process Pygame keyboard events
        for event in events:
            if event.type == pygame.KEYDOWN:
                # Primary menu / restart triggers
                if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_r):
                    self.start_or_restart_requested = True

                # Debug overlay toggle
                if event.key in (pygame.K_TAB, pygame.K_F3):
                    self.toggle_debug_requested = True

                # Manual posture recalibration
                if event.key == pygame.K_c:
                    self.recalibrate_requested = True

                # Keyboard Fallback Controls:
                # A / Left Arrow = Move Left
                if event.key in (pygame.K_a, pygame.K_LEFT):
                    actions.append(GameAction.MOVE_LEFT)

                # D / Right Arrow = Move Right
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    actions.append(GameAction.MOVE_RIGHT)

                # Space = Jump
                elif event.key == pygame.K_SPACE:
                    actions.append(GameAction.JUMP)

                # S / Down Arrow = Slide
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    actions.append(GameAction.SLIDE)

        # Check continuous keyboard slide hold (S or Down Arrow)
        if pygame.display.get_init():
            keys_pressed = pygame.key.get_pressed()
            if keys_pressed[pygame.K_s] or keys_pressed[pygame.K_DOWN]:
                keyboard_sliding = True

        # Merge pose gesture events
        for gest_action in gesture_result.triggered_events:
            if gest_action not in actions:
                actions.append(gest_action)

        # Combined sliding state (either holding duck pose or holding slide key)
        combined_sliding = gesture_result.is_sliding or keyboard_sliding

        return actions, combined_sliding
