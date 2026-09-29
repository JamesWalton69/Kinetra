"""
Landmark data representation and smoothing for local pose estimation.
Exposes normalized landmark coordinates for downstream gesture processing.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import time


@dataclass
class LandmarkPoint:
    """Normalized 3D landmark coordinate with detection visibility."""
    x: float
    y: float
    z: float = 0.0
    visibility: float = 1.0

    def as_tuple(self) -> Tuple[float, float]:
        return self.x, self.y


class PoseLandmarks:
    """
    Standardized pose representation exposing key body landmarks.
    All coordinates are normalized to [0.0, 1.0] relative to frame dimensions.
    """

    def __init__(
        self,
        nose: Optional[LandmarkPoint] = None,
        left_shoulder: Optional[LandmarkPoint] = None,
        right_shoulder: Optional[LandmarkPoint] = None,
        left_hip: Optional[LandmarkPoint] = None,
        right_hip: Optional[LandmarkPoint] = None,
        left_knee: Optional[LandmarkPoint] = None,
        right_knee: Optional[LandmarkPoint] = None,
        left_ankle: Optional[LandmarkPoint] = None,
        right_ankle: Optional[LandmarkPoint] = None,
        raw_landmarks: Optional[List[LandmarkPoint]] = None,
        is_detected: bool = False,
        confidence: float = 0.0,
        timestamp: float = 0.0,
    ):
        self.nose = nose
        self.left_shoulder = left_shoulder
        self.right_shoulder = right_shoulder
        self.left_hip = left_hip
        self.right_hip = right_hip
        self.left_knee = left_knee
        self.right_knee = right_knee
        self.left_ankle = left_ankle
        self.right_ankle = right_ankle
        self.raw_landmarks = raw_landmarks or []
        self.is_detected = is_detected
        self.confidence = confidence
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> Dict[str, Optional[Tuple[float, float, float]]]:
        """Convert key landmarks to dictionary format."""
        return {
            "nose": (self.nose.x, self.nose.y, self.nose.z) if self.nose else None,
            "left_shoulder": (self.left_shoulder.x, self.left_shoulder.y, self.left_shoulder.z) if self.left_shoulder else None,
            "right_shoulder": (self.right_shoulder.x, self.right_shoulder.y, self.right_shoulder.z) if self.right_shoulder else None,
            "left_hip": (self.left_hip.x, self.left_hip.y, self.left_hip.z) if self.left_hip else None,
            "right_hip": (self.right_hip.x, self.right_hip.y, self.right_hip.z) if self.right_hip else None,
            "left_knee": (self.left_knee.x, self.left_knee.y, self.left_knee.z) if self.left_knee else None,
            "right_knee": (self.right_knee.x, self.right_knee.y, self.right_knee.z) if self.right_knee else None,
            "left_ankle": (self.left_ankle.x, self.left_ankle.y, self.left_ankle.z) if self.left_ankle else None,
            "right_ankle": (self.right_ankle.x, self.right_ankle.y, self.right_ankle.z) if self.right_ankle else None,
        }

    @property
    def shoulder_center(self) -> Optional[Tuple[float, float]]:
        """Midpoint between shoulders in normalized coordinates."""
        if self.left_shoulder and self.right_shoulder:
            return (
                (self.left_shoulder.x + self.right_shoulder.x) * 0.5,
                (self.left_shoulder.y + self.right_shoulder.y) * 0.5,
            )
        return None

    @property
    def hip_center(self) -> Optional[Tuple[float, float]]:
        """Midpoint between hips in normalized coordinates."""
        if self.left_hip and self.right_hip:
            return (
                (self.left_hip.x + self.right_hip.x) * 0.5,
                (self.left_hip.y + self.right_hip.y) * 0.5,
            )
        return None

    @property
    def torso_center(self) -> Optional[Tuple[float, float]]:
        """
        Robust center of the player's upper body.
        Uses shoulder midpoint if hips aren't fully visible, or average of both.
        """
        sc = self.shoulder_center
        hc = self.hip_center
        if sc and hc:
            return ((sc[0] + hc[0]) * 0.5, (sc[1] + hc[1]) * 0.5)
        return sc or hc

    @property
    def torso_height(self) -> float:
        """
        Normalized vertical distance between shoulders and hips.
        Useful for scale-invariant distance measurements.
        """
        sc = self.shoulder_center
        hc = self.hip_center
        if sc and hc:
            return max(0.05, abs(hc[1] - sc[1]))
        return 0.35  # Approximate fallback height for normalized pose


class LandmarkSmoother:
    """
    Applies Exponential Moving Average (EMA) smoothing to landmark coordinates
    to reduce high-frequency webcam sensor jitter.
    """

    def __init__(self, alpha: float = 0.4):
        self.alpha = max(0.01, min(1.0, alpha))
        self._history: Dict[str, LandmarkPoint] = {}

    def reset(self) -> None:
        """Clear smoothing history."""
        self._history.clear()

    def smooth(self, raw: PoseLandmarks) -> PoseLandmarks:
        """Smooth normalized landmarks using EMA."""
        if not raw.is_detected:
            self._history.clear()
            return raw

        def _blend(key: str, pt: Optional[LandmarkPoint]) -> Optional[LandmarkPoint]:
            if pt is None:
                return None
            if key not in self._history:
                self._history[key] = LandmarkPoint(pt.x, pt.y, pt.z, pt.visibility)
                return pt

            prev = self._history[key]
            smooth_x = self.alpha * pt.x + (1.0 - self.alpha) * prev.x
            smooth_y = self.alpha * pt.y + (1.0 - self.alpha) * prev.y
            smooth_z = self.alpha * pt.z + (1.0 - self.alpha) * prev.z
            vis = min(pt.visibility, prev.visibility)

            blended = LandmarkPoint(smooth_x, smooth_y, smooth_z, vis)
            self._history[key] = blended
            return blended

        smoothed = PoseLandmarks(
            nose=_blend("nose", raw.nose),
            left_shoulder=_blend("left_shoulder", raw.left_shoulder),
            right_shoulder=_blend("right_shoulder", raw.right_shoulder),
            left_hip=_blend("left_hip", raw.left_hip),
            right_hip=_blend("right_hip", raw.right_hip),
            left_knee=_blend("left_knee", raw.left_knee),
            right_knee=_blend("right_knee", raw.right_knee),
            left_ankle=_blend("left_ankle", raw.left_ankle),
            right_ankle=_blend("right_ankle", raw.right_ankle),
            raw_landmarks=raw.raw_landmarks,
            is_detected=raw.is_detected,
            confidence=raw.confidence,
            timestamp=raw.timestamp,
        )
        return smoothed
