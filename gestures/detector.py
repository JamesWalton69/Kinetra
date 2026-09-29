"""
Deterministic gesture detection from normalized body landmarks.
Processes smoothed landmark coordinates relative to a calibrated neutral standing baseline.
"""

from enum import Enum, auto
from typing import Optional, Tuple
import numpy as np

from config.settings import (
    CALIBRATION_FRAMES,
    LEAN_LEFT_THRESHOLD,
    LEAN_RIGHT_THRESHOLD,
    JUMP_THRESHOLD,
    SLIDE_THRESHOLD,
)
from pose.landmarks import PoseLandmarks


class GestureType(Enum):
    """Recognized discrete body gestures."""
    UNKNOWN = auto()
    NEUTRAL = auto()
    LEFT = auto()
    RIGHT = auto()
    JUMP = auto()
    SLIDE = auto()


class GestureDetector:
    """
    Consumes normalized landmarks and computes deterministic gestures
    relative to a calibrated standing baseline.
    """

    def __init__(self):
        # Neutral baseline coordinates (calibrated when player is standing)
        self.baseline_x: Optional[float] = None
        self.baseline_y: Optional[float] = None
        self.baseline_torso_h: float = 0.35
        self.is_calibrated: bool = False

        # Calibration accumulator
        self._calib_samples_x: list[float] = []
        self._calib_samples_y: list[float] = []
        self._calib_samples_h: list[float] = []

        # Current normalized offsets from baseline
        self.current_delta_x: float = 0.0
        self.current_delta_y: float = 0.0

    def reset_calibration(self) -> None:
        """Reset calibration so the next frames re-establish neutral baseline."""
        self.baseline_x = None
        self.baseline_y = None
        self.baseline_torso_h = 0.35
        self.is_calibrated = False
        self._calib_samples_x.clear()
        self._calib_samples_y.clear()
        self._calib_samples_h.clear()
        self.current_delta_x = 0.0
        self.current_delta_y = 0.0

    def update_calibration(self, landmarks: PoseLandmarks) -> bool:
        """
        Accumulates standing frames to establish a neutral baseline.
        Returns True when calibration is successfully completed.
        """
        if not landmarks.is_detected:
            return False

        tc = landmarks.torso_center
        if tc is None:
            return False

        self._calib_samples_x.append(tc[0])
        self._calib_samples_y.append(tc[1])
        self._calib_samples_h.append(landmarks.torso_height)

        if len(self._calib_samples_x) >= CALIBRATION_FRAMES:
            self.baseline_x = float(np.median(self._calib_samples_x))
            self.baseline_y = float(np.median(self._calib_samples_y))
            self.baseline_torso_h = max(0.1, float(np.median(self._calib_samples_h)))
            self.is_calibrated = True
            print(f"[GestureDetector] Calibrated baseline: x={self.baseline_x:.3f}, y={self.baseline_y:.3f}, h={self.baseline_torso_h:.3f}")
            return True

        return False

    def detect_raw(self, landmarks: PoseLandmarks) -> Tuple[GestureType, float, float]:
        """
        Classify raw gesture from normalized landmarks.
        Returns (GestureType, delta_x, delta_y).
        """
        if not landmarks.is_detected:
            self.current_delta_x = 0.0
            self.current_delta_y = 0.0
            return GestureType.UNKNOWN, 0.0, 0.0

        tc = landmarks.torso_center
        if tc is None:
            return GestureType.UNKNOWN, 0.0, 0.0

        # Auto-calibrate if not yet calibrated
        if not self.is_calibrated:
            if not self.update_calibration(landmarks):
                return GestureType.NEUTRAL, 0.0, 0.0

        # Scale displacement relative to torso height for camera distance invariance
        scale_factor = 0.35 / max(0.1, self.baseline_torso_h)
        delta_x = (tc[0] - self.baseline_x) * scale_factor
        delta_y = (tc[1] - self.baseline_y) * scale_factor

        self.current_delta_x = delta_x
        self.current_delta_y = delta_y

        # Slow adaptive drift for subtle posture shifts while standing near neutral
        if abs(delta_x) < 0.03 and abs(delta_y) < 0.03:
            drift_rate = 0.005
            self.baseline_x = (1.0 - drift_rate) * self.baseline_x + drift_rate * tc[0]
            self.baseline_y = (1.0 - drift_rate) * self.baseline_y + drift_rate * tc[1]

        # Prioritize vertical actions (Jump / Slide)
        # Note: In webcam coordinate system, Y=0 is top, Y=1 is bottom
        # Upward movement -> delta_y < 0
        # Downward movement -> delta_y > 0
        if delta_y < JUMP_THRESHOLD:
            return GestureType.JUMP, delta_x, delta_y
        elif delta_y > SLIDE_THRESHOLD:
            return GestureType.SLIDE, delta_x, delta_y

        # Horizontal actions (Left / Right)
        if delta_x < LEAN_LEFT_THRESHOLD:
            return GestureType.LEFT, delta_x, delta_y
        elif delta_x > LEAN_RIGHT_THRESHOLD:
            return GestureType.RIGHT, delta_x, delta_y

        return GestureType.NEUTRAL, delta_x, delta_y
