"""
Webcam capture and background pose processing thread.
Runs real-time camera capture and landmark estimation asynchronously so
game rendering stays locked at 60 FPS without stutter.
"""

import threading
import time
from typing import Optional, Tuple
import cv2
import numpy as np

from config.settings import (
    CAMERA_INDEX,
    CAMERA_FRAME_WIDTH,
    CAMERA_FRAME_HEIGHT,
    CAMERA_FLIP_HORIZONTAL,
    POSE_INFERENCE_WIDTH,
    POSE_INFERENCE_HEIGHT,
    LANDMARK_SMOOTHING_ALPHA,
)
from pose.estimator import LocalPoseEstimator
from pose.landmarks import PoseLandmarks, LandmarkSmoother


class WebcamPoseCapture:
    """
    Dedicated background worker managing webcam streaming and local pose estimation.
    """

    def __init__(self, camera_index: int = CAMERA_INDEX):
        self.camera_index = camera_index
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # State outputs
        self._camera_available = False
        self._latest_landmarks = PoseLandmarks(is_detected=False)
        self._latest_frame_bgr: Optional[np.ndarray] = None
        self._pose_fps: float = 0.0

        # Components
        self._estimator: Optional[LocalPoseEstimator] = None
        self._smoother = LandmarkSmoother(alpha=LANDMARK_SMOOTHING_ALPHA)

    @property
    def is_camera_available(self) -> bool:
        with self._lock:
            return self._camera_available

    def start(self) -> None:
        """Start the background capture and inference thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="PoseWorker")
        self._thread.start()

    def stop(self) -> None:
        """Signal worker to stop and wait for completion."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)
        if self._estimator:
            self._estimator.close()
            self._estimator = None

    def get_latest_landmarks(self) -> PoseLandmarks:
        """Thread-safe retrieval of the most recent smoothed landmarks."""
        with self._lock:
            return self._latest_landmarks

    def get_latest_frame_bgr(self) -> Optional[np.ndarray]:
        """Thread-safe retrieval of the most recent webcam frame (for debug PIP)."""
        with self._lock:
            if self._latest_frame_bgr is not None:
                return self._latest_frame_bgr.copy()
            return None

    def get_pose_fps(self) -> float:
        """Return the current pose processing FPS."""
        with self._lock:
            return self._pose_fps

    def _worker_loop(self) -> None:
        """Background thread target: read frame, flip, run pose model, smooth landmarks."""
        # Initialize camera
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_ANY)
        if not cap.isOpened():
            print(f"[WebcamPoseCapture] Warning: Camera index {self.camera_index} not accessible. Falling back to keyboard.")
            with self._lock:
                self._camera_available = False
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_FRAME_HEIGHT)

        with self._lock:
            self._camera_available = True

        # Initialize local pose estimator
        try:
            self._estimator = LocalPoseEstimator()
        except Exception as e:
            print(f"[WebcamPoseCapture] Failed to initialize pose estimator: {e}")
            with self._lock:
                self._camera_available = False
            cap.release()
            return

        prev_time = time.perf_counter()
        fps_smoothing = 0.9

        while self._running:
            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            # Mirror frame for natural interactive control
            if CAMERA_FLIP_HORIZONTAL:
                frame = cv2.flip(frame, 1)

            # Downsample for faster local inference
            inference_frame = cv2.resize(
                frame,
                (POSE_INFERENCE_WIDTH, POSE_INFERENCE_HEIGHT),
                interpolation=cv2.INTER_AREA,
            )

            # Perform local landmark estimation
            raw_landmarks = self._estimator.estimate(inference_frame)
            smoothed_landmarks = self._smoother.smooth(raw_landmarks)

            # Compute processing FPS
            now = time.perf_counter()
            dt = now - prev_time
            prev_time = now
            inst_fps = 1.0 / dt if dt > 0.001 else 30.0
            self._pose_fps = fps_smoothing * self._pose_fps + (1.0 - fps_smoothing) * inst_fps

            # Update shared state
            with self._lock:
                self._latest_landmarks = smoothed_landmarks
                self._latest_frame_bgr = frame

            # Small yield to prevent thread starvation
            time.sleep(0.002)

        cap.release()
