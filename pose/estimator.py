"""
Local pose estimation wrapper using MediaPipe Tasks PoseLandmarker.
Runs entirely offline without cloud APIs or third-party paid services.
"""

import os
from pathlib import Path
import urllib.request
from typing import Optional, List
import numpy as np

import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    PoseLandmarker,
    PoseLandmarkerOptions,
    RunningMode,
)

from config.settings import POSE_MODEL_PATH, POSE_MODEL_URL
from pose.landmarks import LandmarkPoint, PoseLandmarks


class LocalPoseEstimator:
    """
    Manages the local MediaPipe PoseLandmarker model lifecycle and performs
    inference on video frames.
    """

    # MediaPipe standard landmark indices
    IDX_NOSE = 0
    IDX_LEFT_SHOULDER = 11
    IDX_RIGHT_SHOULDER = 12
    IDX_LEFT_HIP = 23
    IDX_RIGHT_HIP = 24
    IDX_LEFT_KNEE = 25
    IDX_RIGHT_KNEE = 26
    IDX_LEFT_ANKLE = 27
    IDX_RIGHT_ANKLE = 28

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = Path(model_path or POSE_MODEL_PATH)
        self._ensure_model_exists()
        self._landmarker: Optional[PoseLandmarker] = None
        self._init_landmarker()

    def _ensure_model_exists(self) -> None:
        """Verify the model file exists locally, downloading if missing."""
        if not self.model_path.exists():
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"[PoseEstimator] Downloading model to {self.model_path}...")
            urllib.request.urlretrieve(POSE_MODEL_URL, str(self.model_path))
            print("[PoseEstimator] Model downloaded successfully.")

    def _init_landmarker(self) -> None:
        """Initialize the MediaPipe PoseLandmarker."""
        base_options = BaseOptions(model_asset_path=str(self.model_path))
        options = PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._landmarker = PoseLandmarker.create_from_options(options)

    def estimate(self, frame_bgr: np.ndarray) -> PoseLandmarks:
        """
        Perform pose estimation on an OpenCV BGR image frame.
        Returns a PoseLandmarks container with normalized landmarks.
        """
        if self._landmarker is None or frame_bgr is None or frame_bgr.size == 0:
            return PoseLandmarks(is_detected=False)

        # Convert BGR to RGB for MediaPipe
        rgb_frame = np.ascontiguousarray(frame_bgr[:, :, ::-1])
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        result = self._landmarker.detect(mp_image)

        if not result.pose_landmarks or len(result.pose_landmarks) == 0:
            return PoseLandmarks(is_detected=False)

        detected_landmarks = result.pose_landmarks[0]
        raw_list: List[LandmarkPoint] = [
            LandmarkPoint(
                x=float(lm.x),
                y=float(lm.y),
                z=float(lm.z) if hasattr(lm, "z") else 0.0,
                visibility=float(lm.visibility) if hasattr(lm, "visibility") else 1.0,
            )
            for lm in detected_landmarks
        ]

        def _get_lm(idx: int) -> Optional[LandmarkPoint]:
            if 0 <= idx < len(raw_list):
                return raw_list[idx]
            return None

        # Calculate average visibility confidence for core landmarks
        core_indices = [
            self.IDX_NOSE,
            self.IDX_LEFT_SHOULDER,
            self.IDX_RIGHT_SHOULDER,
            self.IDX_LEFT_HIP,
            self.IDX_RIGHT_HIP,
        ]
        confidences = [
            raw_list[i].visibility for i in core_indices if i < len(raw_list)
        ]
        avg_confidence = float(np.mean(confidences)) if confidences else 0.0

        return PoseLandmarks(
            nose=_get_lm(self.IDX_NOSE),
            left_shoulder=_get_lm(self.IDX_LEFT_SHOULDER),
            right_shoulder=_get_lm(self.IDX_RIGHT_SHOULDER),
            left_hip=_get_lm(self.IDX_LEFT_HIP),
            right_hip=_get_lm(self.IDX_RIGHT_HIP),
            left_knee=_get_lm(self.IDX_LEFT_KNEE),
            right_knee=_get_lm(self.IDX_RIGHT_KNEE),
            left_ankle=_get_lm(self.IDX_LEFT_ANKLE),
            right_ankle=_get_lm(self.IDX_RIGHT_ANKLE),
            raw_landmarks=raw_list,
            is_detected=True,
            confidence=avg_confidence,
        )

    def close(self) -> None:
        """Release landmarker resources."""
        if self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None
