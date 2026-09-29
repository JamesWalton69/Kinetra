"""
Render pipeline test ensuring pygame surfaces, perspective projection,
HUD, Main Menu, Game Over, and Debug Overlay render without exceptions.
"""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
import numpy as np

from config.settings import SCREEN_WIDTH, SCREEN_HEIGHT
from game.engine import GameEngine, GameState
from ui.menu import MainMenuUI
from ui.hud import GameHUD
from ui.game_over import GameOverUI
from ui.debug_overlay import DebugOverlay
from gestures.state import GestureStateResult
from gestures.detector import GestureType
from pose.landmarks import PoseLandmarks, LandmarkPoint

def test_full_render_pipeline():
    print(">>> Testing Full Render Pipeline (Headless)...")
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    engine = GameEngine()
    menu_ui = MainMenuUI()
    hud_ui = GameHUD()
    game_over_ui = GameOverUI()
    debug_overlay = DebugOverlay()

    mock_landmarks = PoseLandmarks(
        nose=LandmarkPoint(0.5, 0.2),
        left_shoulder=LandmarkPoint(0.4, 0.35),
        right_shoulder=LandmarkPoint(0.6, 0.35),
        left_hip=LandmarkPoint(0.42, 0.7),
        right_hip=LandmarkPoint(0.58, 0.7),
        raw_landmarks=[LandmarkPoint(0.5, 0.5) for _ in range(33)],
        is_detected=True,
        confidence=0.88,
    )
    mock_gesture_res = GestureStateResult(
        active_gesture=GestureType.NEUTRAL,
        is_calibrated=True,
        delta_x=0.01,
        delta_y=-0.02,
    )
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    # 1. Test Menu Rendering
    engine.render_world(screen)
    menu_ui.draw(screen, camera_available=True, gesture_result=mock_gesture_res)
    pygame.display.flip()
    print("[PASS] Main Menu rendering verified.")

    # 2. Test HUD Rendering (Playing State)
    engine.state = GameState.PLAYING
    engine.render_world(screen)
    hud_ui.draw(
        surface=screen,
        score=1250.0,
        distance=450.0,
        current_lane=0,
        gesture_result=mock_gesture_res,
        debug_mode=True,
    )
    pygame.display.flip()
    print("[PASS] HUD rendering verified.")

    # 3. Test Game Over Rendering
    engine.state = GameState.GAME_OVER
    engine.render_world(screen)
    game_over_ui.draw(
        surface=screen,
        final_score=1250.0,
        high_score=2500.0,
        distance=450.0,
    )
    pygame.display.flip()
    print("[PASS] Game Over rendering verified.")

    # 4. Test Debug Overlay Rendering
    debug_overlay.draw(
        surface=screen,
        webcam_frame_bgr=dummy_frame,
        landmarks=mock_landmarks,
        gesture_result=mock_gesture_res,
        player=engine.player,
        game_fps=60.0,
        pose_fps=30.0,
        camera_available=True,
    )
    pygame.display.flip()
    print("[PASS] Debug Overlay rendering verified.")

    pygame.quit()
    print("\n[ALL RENDER TESTS PASSED SUCCESSFULLY!]")

if __name__ == "__main__":
    test_full_render_pipeline()
