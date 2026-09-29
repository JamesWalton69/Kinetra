"""
Gesture state handling with debouncing, cooldown timers, event firing,
and continuous state tracking.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
import time
from typing import List, Optional

from config.settings import (
    GESTURE_DEBOUNCE_FRAMES,
    LANE_CHANGE_COOLDOWN,
    JUMP_COOLDOWN,
    SLIDE_MIN_DURATION,
    NEUTRAL_RESET_RATIO,
    LEAN_LEFT_THRESHOLD,
    LEAN_RIGHT_THRESHOLD,
    JUMP_THRESHOLD,
    SLIDE_THRESHOLD,
)
from gestures.detector import GestureDetector, GestureType
from pose.landmarks import PoseLandmarks


class GameAction(Enum):
    """Discrete game actions produced by gestures or keyboard fallback."""
    MOVE_LEFT = auto()
    MOVE_RIGHT = auto()
    JUMP = auto()
    SLIDE = auto()


@dataclass
class GestureStateResult:
    """Summary of gesture detection and triggered events for a single frame."""
    active_gesture: GestureType = GestureType.UNKNOWN
    triggered_events: List[GameAction] = field(default_factory=list)
    is_sliding: bool = False
    delta_x: float = 0.0
    delta_y: float = 0.0
    is_calibrated: bool = False


class GestureStateManager:
    """
    Manages debouncing, event triggers, and cooldowns for gestures.
    Ensures single physical movements create clean discrete game actions.
    """

    def __init__(self, detector: GestureDetector):
        self.detector = detector

        # Debounce state
        self._candidate_gesture = GestureType.UNKNOWN
        self._candidate_count = 0
        self._confirmed_gesture = GestureType.UNKNOWN

        # Cooldown timestamps
        self._last_lane_change_time = 0.0
        self._last_jump_time = 0.0
        self._slide_start_time = 0.0

        # Re-arm flags (require returning toward neutral before re-triggering)
        self._left_armed = True
        self._right_armed = True
        self._jump_armed = True

        # Slide continuous state
        self._is_sliding = False

    def reset(self) -> None:
        """Reset state tracking and detector calibration."""
        self.detector.reset_calibration()
        self._candidate_gesture = GestureType.UNKNOWN
        self._candidate_count = 0
        self._confirmed_gesture = GestureType.UNKNOWN
        self._last_lane_change_time = 0.0
        self._last_jump_time = 0.0
        self._slide_start_time = 0.0
        self._left_armed = True
        self._right_armed = True
        self._jump_armed = True
        self._is_sliding = False

    def update(self, landmarks: PoseLandmarks, timestamp: Optional[float] = None) -> GestureStateResult:
        """
        Process current frame landmarks, update state machine,
        and return triggered actions and active states.
        """
        now = timestamp if timestamp is not None else time.time()
        raw_gesture, delta_x, delta_y = self.detector.detect_raw(landmarks)

        # 1. Debounce Logic
        if raw_gesture == self._candidate_gesture:
            self._candidate_count += 1
        else:
            self._candidate_gesture = raw_gesture
            self._candidate_count = 1

        if self._candidate_count >= GESTURE_DEBOUNCE_FRAMES:
            self._confirmed_gesture = self._candidate_gesture

        triggered_actions: List[GameAction] = []

        # 2. Re-arming Checks (Require returning toward neutral)
        neutral_left_reset = LEAN_LEFT_THRESHOLD * NEUTRAL_RESET_RATIO
        neutral_right_reset = LEAN_RIGHT_THRESHOLD * NEUTRAL_RESET_RATIO
        neutral_jump_reset = JUMP_THRESHOLD * NEUTRAL_RESET_RATIO

        if self._confirmed_gesture == GestureType.NEUTRAL:
            if delta_x > neutral_left_reset:
                self._left_armed = True
            if delta_x < neutral_right_reset:
                self._right_armed = True
            if delta_y > neutral_jump_reset:
                self._jump_armed = True

        # 3. Discrete Event Triggers with Cooldowns
        # Move Left
        if (
            self._confirmed_gesture == GestureType.LEFT
            and self._left_armed
            and (now - self._last_lane_change_time >= LANE_CHANGE_COOLDOWN)
        ):
            triggered_actions.append(GameAction.MOVE_LEFT)
            self._last_lane_change_time = now
            self._left_armed = False

        # Move Right
        if (
            self._confirmed_gesture == GestureType.RIGHT
            and self._right_armed
            and (now - self._last_lane_change_time >= LANE_CHANGE_COOLDOWN)
        ):
            triggered_actions.append(GameAction.MOVE_RIGHT)
            self._last_lane_change_time = now
            self._right_armed = False

        # Jump (Event Trigger)
        if (
            self._confirmed_gesture == GestureType.JUMP
            and self._jump_armed
            and (now - self._last_jump_time >= JUMP_COOLDOWN)
        ):
            triggered_actions.append(GameAction.JUMP)
            self._last_jump_time = now
            self._jump_armed = False

        # Slide / Duck (State Handling)
        if self._confirmed_gesture == GestureType.SLIDE:
            if not self._is_sliding:
                triggered_actions.append(GameAction.SLIDE)
                self._slide_start_time = now
            self._is_sliding = True
        else:
            # Check minimum slide duration guarantee
            if self._is_sliding and (now - self._slide_start_time >= SLIDE_MIN_DURATION):
                self._is_sliding = False

        return GestureStateResult(
            active_gesture=self._confirmed_gesture,
            triggered_events=triggered_actions,
            is_sliding=self._is_sliding,
            delta_x=delta_x,
            delta_y=delta_y,
            is_calibrated=self.detector.is_calibrated,
        )
