"""
Kinetra - Local Webcam Endless Runner
Main entry point orchestrating webcam capture, pose estimation, gesture recognition,
gameplay simulation, and UI rendering.
"""

import sys
import time
import pygame

from config.settings import (
    WINDOW_TITLE,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    TARGET_FPS,
)
from pose.webcam import WebcamPoseCapture
from gestures.detector import GestureDetector
from gestures.state import GestureStateManager
from game.engine import GameEngine, GameState
from ui.menu import MainMenuUI
from ui.hud import GameHUD
from ui.game_over import GameOverUI
from ui.debug_overlay import DebugOverlay


def main() -> None:
    """Initialize systems and run the primary application loop."""
    print("========================================")
    print(" KINETRA - Local Webcam Endless Runner ")
    print("========================================")

    # Initialize Pygame subsystems
    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()

    # Initialize Pose & Gesture Subsystems
    print("[Main] Starting webcam capture & local pose estimation thread...")
    webcam_capture = WebcamPoseCapture()
    webcam_capture.start()

    gesture_detector = GestureDetector()
    gesture_state_mgr = GestureStateManager(gesture_detector)

    # Initialize Gameplay Engine & UI Overlays
    engine = GameEngine()
    menu_ui = MainMenuUI()
    hud_ui = GameHUD()
    game_over_ui = GameOverUI()
    debug_overlay = DebugOverlay()

    running = True
    print("[Main] Initialization complete. Game loop running at target 60 FPS.")

    try:
        while running:
            dt = clock.tick(TARGET_FPS) / 1000.0
            # Clamp dt to prevent physics tunneling on large pauses/hiccups
            dt = min(0.05, dt)

            # 1. Event Polling
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            # 2. Retrieve Pose Data
            landmarks = webcam_capture.get_latest_landmarks()
            camera_available = webcam_capture.is_camera_available

            # 3. Process Gestures
            gesture_result = gesture_state_mgr.update(landmarks)

            # Check for manual recalibration request
            if engine.input_handler.recalibrate_requested:
                gesture_state_mgr.reset()
                print("[Main] Recalibrating neutral standing posture...")

            # 4. Advance Game Simulation
            engine.update(dt, events, gesture_result)

            # 5. Render Scene
            engine.render_world(screen)

            # 6. Render State-Specific UI
            if engine.state == GameState.MAIN_MENU:
                menu_ui.draw(screen, camera_available, gesture_result)
            elif engine.state == GameState.PLAYING:
                hud_ui.draw(
                    surface=screen,
                    score=engine.score,
                    distance=engine.distance,
                    current_lane=engine.player.lane,
                    gesture_result=gesture_result,
                    debug_mode=engine.debug_mode,
                )
            elif engine.state == GameState.GAME_OVER:
                game_over_ui.draw(
                    surface=screen,
                    final_score=engine.score,
                    high_score=engine.high_score,
                    distance=engine.distance,
                )

            # 7. Render Debug Diagnostics Overlay (if enabled)
            if engine.debug_mode:
                webcam_frame = webcam_capture.get_latest_frame_bgr()
                debug_overlay.draw(
                    surface=screen,
                    webcam_frame_bgr=webcam_frame,
                    landmarks=landmarks,
                    gesture_result=gesture_result,
                    player=engine.player,
                    game_fps=clock.get_fps(),
                    pose_fps=webcam_capture.get_pose_fps(),
                    camera_available=camera_available,
                )

            # 8. Present Frame
            pygame.display.flip()

    except KeyboardInterrupt:
        print("[Main] Interrupted by user.")

    finally:
        print("[Main] Shutting down webcam worker thread...")
        webcam_capture.stop()
        pygame.quit()
        print("[Main] Clean shutdown completed.")


if __name__ == "__main__":
    main()
