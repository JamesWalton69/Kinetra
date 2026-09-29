"""
Comprehensive automated verification script testing all Kinetra modules:
- Pose estimation
- Landmark extraction & smoothing
- Gesture detection & state debouncing
- Player movement & physics
- Obstacle spawning & collision
- Game engine state machine
"""

import sys
import numpy as np

print(">>> Testing Module Imports...")
import config.settings as settings
from pose.landmarks import LandmarkPoint, PoseLandmarks, LandmarkSmoother
from pose.estimator import LocalPoseEstimator
from gestures.detector import GestureDetector, GestureType
from gestures.state import GameAction, GestureStateManager
from game.lane import Camera3D, LaneRenderer
from game.player import Player
from game.obstacle import Obstacle, ObstacleType, ObstacleManager
from game.engine import GameEngine, GameState
print("[PASS] All modules imported successfully.")


def test_landmarks_and_smoother():
    print("\n>>> Testing Landmarks & Smoother...")
    smoother = LandmarkSmoother(alpha=0.5)

    # Empty landmarks
    empty = PoseLandmarks(is_detected=False)
    assert not empty.is_detected
    smoothed_empty = smoother.smooth(empty)
    assert not smoothed_empty.is_detected

    # Simulated detected landmarks
    p1 = PoseLandmarks(
        nose=LandmarkPoint(0.5, 0.2, 0.0),
        left_shoulder=LandmarkPoint(0.4, 0.35, 0.0),
        right_shoulder=LandmarkPoint(0.6, 0.35, 0.0),
        left_hip=LandmarkPoint(0.42, 0.7, 0.0),
        right_hip=LandmarkPoint(0.58, 0.7, 0.0),
        is_detected=True,
        confidence=0.9,
    )
    assert p1.shoulder_center == (0.5, 0.35)
    assert p1.hip_center == (0.5, 0.7)
    assert abs(p1.torso_center[0] - 0.5) < 1e-4
    assert abs(p1.torso_center[1] - 0.525) < 1e-4
    assert abs(p1.torso_height - 0.35) < 1e-4

    s1 = smoother.smooth(p1)
    assert s1.is_detected
    assert s1.left_shoulder.x == 0.4

    # Second frame with slight shift
    p2 = PoseLandmarks(
        nose=LandmarkPoint(0.52, 0.2, 0.0),
        left_shoulder=LandmarkPoint(0.42, 0.35, 0.0),
        right_shoulder=LandmarkPoint(0.62, 0.35, 0.0),
        left_hip=LandmarkPoint(0.44, 0.7, 0.0),
        right_hip=LandmarkPoint(0.60, 0.7, 0.0),
        is_detected=True,
        confidence=0.9,
    )
    s2 = smoother.smooth(p2)
    # EMA with alpha=0.5: 0.5 * 0.42 + 0.5 * 0.40 = 0.41
    assert abs(s2.left_shoulder.x - 0.41) < 1e-4
    print("[PASS] Landmarks and Smoother verified.")


def test_pose_estimator():
    print("\n>>> Testing LocalPoseEstimator with model asset...")
    estimator = LocalPoseEstimator()
    dummy_bgr = np.zeros((240, 320, 3), dtype=np.uint8)
    result = estimator.estimate(dummy_bgr)
    assert isinstance(result, PoseLandmarks)
    # Blank frame should report not detected
    assert not result.is_detected
    estimator.close()
    print("[PASS] LocalPoseEstimator verified.")


def test_gesture_detector_and_state():
    print("\n>>> Testing GestureDetector & GestureStateManager...")
    detector = GestureDetector()
    state_mgr = GestureStateManager(detector)

    # Helper to build mock landmarks at torso center (x, y)
    def mock_pose(cx: float, cy: float) -> PoseLandmarks:
        return PoseLandmarks(
            nose=LandmarkPoint(cx, cy - 0.3, 0.0),
            left_shoulder=LandmarkPoint(cx - 0.1, cy - 0.15, 0.0),
            right_shoulder=LandmarkPoint(cx + 0.1, cy - 0.15, 0.0),
            left_hip=LandmarkPoint(cx - 0.08, cy + 0.15, 0.0),
            right_hip=LandmarkPoint(cx + 0.08, cy + 0.15, 0.0),
            is_detected=True,
            confidence=0.95,
        )

    # Feed calibration frames at center (0.5, 0.5)
    for _ in range(settings.CALIBRATION_FRAMES + 2):
        state_mgr.update(mock_pose(0.5, 0.5))

    assert detector.is_calibrated
    assert abs(detector.baseline_x - 0.5) < 0.02
    assert abs(detector.baseline_y - 0.5) < 0.02

    # Neutral pose test
    sim_time = 100.0
    res = state_mgr.update(mock_pose(0.5, 0.5), timestamp=sim_time)
    assert res.active_gesture == GestureType.NEUTRAL

    # Lean Left (x decreases)
    # Debounce requires GESTURE_DEBOUNCE_FRAMES frames
    sim_time += 0.05
    res1 = state_mgr.update(mock_pose(0.40, 0.5), timestamp=sim_time)
    sim_time += 0.05
    res2 = state_mgr.update(mock_pose(0.40, 0.5), timestamp=sim_time)
    assert res2.active_gesture == GestureType.LEFT
    assert GameAction.MOVE_LEFT in res2.triggered_events

    # Next frame should NOT re-trigger MOVE_LEFT immediately (cooldown & re-arm check)
    sim_time += 0.05
    res3 = state_mgr.update(mock_pose(0.40, 0.5), timestamp=sim_time)
    assert GameAction.MOVE_LEFT not in res3.triggered_events

    # Return to center to re-arm and wait for lane change cooldown (0.35s)
    sim_time += 0.5
    state_mgr.update(mock_pose(0.50, 0.5), timestamp=sim_time)
    sim_time += 0.05
    state_mgr.update(mock_pose(0.50, 0.5), timestamp=sim_time)

    # Lean Right (x increases)
    sim_time += 0.05
    res_r1 = state_mgr.update(mock_pose(0.60, 0.5), timestamp=sim_time)
    sim_time += 0.05
    res_r2 = state_mgr.update(mock_pose(0.60, 0.5), timestamp=sim_time)
    assert res_r2.active_gesture == GestureType.RIGHT
    assert GameAction.MOVE_RIGHT in res_r2.triggered_events

    # Return to center and wait for cooldown
    sim_time += 0.5
    state_mgr.update(mock_pose(0.50, 0.5), timestamp=sim_time)
    sim_time += 0.05
    state_mgr.update(mock_pose(0.50, 0.5), timestamp=sim_time)

    # Jump (y decreases)
    sim_time += 0.05
    res_j1 = state_mgr.update(mock_pose(0.50, 0.40), timestamp=sim_time)
    sim_time += 0.05
    res_j2 = state_mgr.update(mock_pose(0.50, 0.40), timestamp=sim_time)
    assert res_j2.active_gesture == GestureType.JUMP
    assert GameAction.JUMP in res_j2.triggered_events

    # Return to center and wait for cooldown
    sim_time += 0.6
    state_mgr.update(mock_pose(0.50, 0.5), timestamp=sim_time)
    sim_time += 0.05
    state_mgr.update(mock_pose(0.50, 0.5), timestamp=sim_time)

    # Slide / Duck (y increases)
    sim_time += 0.05
    res_s1 = state_mgr.update(mock_pose(0.50, 0.60), timestamp=sim_time)
    sim_time += 0.05
    res_s2 = state_mgr.update(mock_pose(0.50, 0.60), timestamp=sim_time)
    assert res_s2.active_gesture == GestureType.SLIDE
    assert res_s2.is_sliding
    print("[PASS] GestureDetector and GestureStateManager verified.")


def test_player_and_obstacles():
    print("\n>>> Testing Player & Obstacle Collision...")
    player = Player()
    assert player.lane == 0

    # Lane shifts
    player.move_left()
    assert player.lane == -1
    player.move_left()  # Boundary clamp
    assert player.lane == -1

    player.move_right()
    assert player.lane == 0
    player.move_right()
    assert player.lane == 1
    player.move_right()  # Boundary clamp
    assert player.lane == 1
    player.move_left()
    assert player.lane == 0

    # Jump physics
    assert player.is_grounded
    player.jump()
    assert not player.is_grounded
    assert player.is_jumping
    assert player.velocity_y == settings.JUMP_VELOCITY

    # Simulate physics steps to land
    for _ in range(60):
        player.update(0.02)
    assert player.is_grounded
    assert not player.is_jumping
    assert player.world_y == 0.0

    # Slide crouch
    player.start_slide(0.5)
    assert player.is_sliding
    assert player.current_height == settings.PLAYER_HEIGHT_SLIDE

    # Collision Tests
    # 1. Hurdle test: Hurdle on center lane at z=0 (player position)
    hurdle = Obstacle(ObstacleType.HURDLE, lane=0, z=0.0)
    player.reset()
    # Standing player collides with hurdle
    assert hurdle.check_collision(player)

    # Jumping player clears hurdle
    player.jump()
    player.world_y = 1.0  # Height above hurdle (0.75m)
    assert not hurdle.check_collision(player)

    # 2. Overhead test: Overhead bar on center lane at z=0
    overhead = Obstacle(ObstacleType.OVERHEAD, lane=0, z=0.0)
    player.reset()
    # Standing player (height 1.6) collides with overhead (clearance 0.85 - 2.2)
    assert overhead.check_collision(player)

    # Sliding player (height 0.7) passes under overhead
    player.start_slide()
    assert not overhead.check_collision(player)

    # 3. Barrier test: Barrier on center lane
    barrier = Obstacle(ObstacleType.BARRIER, lane=0, z=0.0)
    player.reset()
    assert barrier.check_collision(player)
    # Moving to lane -1 avoids center barrier
    player.move_left()
    player.world_x = -settings.LANE_WIDTH
    assert not barrier.check_collision(player)

    print("[PASS] Player physics and Obstacle collisions verified.")


def test_game_engine():
    print("\n>>> Testing GameEngine State Machine...")
    engine = GameEngine()
    assert engine.state == GameState.MAIN_MENU

    # Start game
    engine.start_new_game()
    assert engine.state == GameState.PLAYING
    assert engine.score == 0.0

    # Advance engine
    from gestures.state import GestureStateResult
    dummy_res = GestureStateResult()
    engine.update(0.1, [], dummy_res)
    assert engine.distance > 0.0
    assert engine.score > 0.0

    # Trigger game over via obstacle
    obs = Obstacle(ObstacleType.BARRIER, lane=0, z=0.0)
    engine.obstacle_manager.obstacles.append(obs)
    engine.update(0.01, [], dummy_res)
    assert engine.state == GameState.GAME_OVER

    # Restart
    engine.start_new_game()
    assert engine.state == GameState.PLAYING
    print("[PASS] GameEngine verified.")


if __name__ == "__main__":
    test_landmarks_and_smoother()
    test_pose_estimator()
    test_gesture_detector_and_state()
    test_player_and_obstacles()
    test_game_engine()
    print("\n==============================================")
    print("ALL VERIFICATION SUITES PASSED WITHOUT ERRORS!")
    print("==============================================")
