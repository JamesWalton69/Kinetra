"""
Debug overlay rendering.
Displays real-time picture-in-picture webcam feed, skeleton landmarks,
detected gesture, FPS counters, player state, and confidence metrics.
"""

from typing import Optional, Tuple
import cv2
import numpy as np
import pygame

from config.settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    DEBUG_PIP_WIDTH,
    DEBUG_PIP_HEIGHT,
    DEBUG_PIP_MARGIN,
    COLOR_SKELETON_JOINT,
    COLOR_SKELETON_BONE,
    LEAN_LEFT_THRESHOLD,
    LEAN_RIGHT_THRESHOLD,
    JUMP_THRESHOLD,
    SLIDE_THRESHOLD,
)
from gestures.detector import GestureType
from gestures.state import GestureStateResult
from pose.landmarks import PoseLandmarks
from game.player import Player


class DebugOverlay:
    """Renders diagnostic information and live camera skeleton tracking."""

    # Key landmark connection pairs for skeleton visualization
    SKELETON_CONNECTIONS = [
        # Torso
        (11, 12),  # Left shoulder to right shoulder
        (11, 23),  # Left shoulder to left hip
        (12, 24),  # Right shoulder to right hip
        (23, 24),  # Left hip to right hip
        # Arms
        (11, 13), (13, 15),  # Left arm
        (12, 14), (14, 16),  # Right arm
        # Legs
        (23, 25), (25, 27),  # Left leg
        (24, 26), (26, 28),  # Right leg
        # Head
        (0, 11), (0, 12),   # Nose to shoulders
    ]

    def __init__(self):
        self._font_header = pygame.font.SysFont("Consolas", 14, bold=True)
        self._font_mono = pygame.font.SysFont("Consolas", 12)

    def draw(
        self,
        surface: pygame.Surface,
        webcam_frame_bgr: Optional[np.ndarray],
        landmarks: PoseLandmarks,
        gesture_result: GestureStateResult,
        player: Player,
        game_fps: float,
        pose_fps: float,
        camera_available: bool,
    ) -> None:
        """Render debug window and diagnostic metrics onto game surface."""
        pip_w = DEBUG_PIP_WIDTH
        pip_h = DEBUG_PIP_HEIGHT
        pip_x = SCREEN_WIDTH - pip_w - DEBUG_PIP_MARGIN
        pip_y = 52  # Below top HUD

        # 1. Webcam Frame & Skeleton Rendering
        if webcam_frame_bgr is not None:
            # Resize frame for PIP box
            resized = cv2.resize(webcam_frame_bgr, (pip_w, pip_h), interpolation=cv2.INTER_LINEAR)
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            cam_surface = pygame.image.frombuffer(rgb.tobytes(), (pip_w, pip_h), "RGB")

            # Draw skeleton overlay on the camera surface
            if landmarks.is_detected and landmarks.raw_landmarks:
                raws = landmarks.raw_landmarks

                # Draw connection bones
                for idx1, idx2 in self.SKELETON_CONNECTIONS:
                    if idx1 < len(raws) and idx2 < len(raws):
                        lm1, lm2 = raws[idx1], raws[idx2]
                        if lm1.visibility > 0.4 and lm2.visibility > 0.4:
                            p1 = (int(lm1.x * pip_w), int(lm1.y * pip_h))
                            p2 = (int(lm2.x * pip_w), int(lm2.y * pip_h))
                            pygame.draw.line(cam_surface, COLOR_SKELETON_BONE, p1, p2, 2)

                # Draw joint dots
                for idx in [0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]:
                    if idx < len(raws):
                        lm = raws[idx]
                        if lm.visibility > 0.4:
                            pt = (int(lm.x * pip_w), int(lm.y * pip_h))
                            pygame.draw.circle(cam_surface, COLOR_SKELETON_JOINT, pt, 3)

                # Draw torso center point
                tc = landmarks.torso_center
                if tc:
                    tc_pt = (int(tc[0] * pip_w), int(tc[1] * pip_h))
                    pygame.draw.circle(cam_surface, (255, 50, 50), tc_pt, 4)

            # Blit camera feed to main screen
            surface.blit(cam_surface, (pip_x, pip_y))

            # Border around camera PIP
            border_color = (60, 220, 100) if landmarks.is_detected else (220, 70, 70)
            pygame.draw.rect(surface, border_color, pygame.Rect(pip_x, pip_y, pip_w, pip_h), 2)

        else:
            # Placeholder if camera feed is unavailable
            pip_rect = pygame.Rect(pip_x, pip_y, pip_w, pip_h)
            pygame.draw.rect(surface, (25, 30, 40), pip_rect)
            pygame.draw.rect(surface, (180, 50, 50), pip_rect, 2)
            msg = self._font_mono.render("Camera Unavailable", True, (200, 100, 100))
            surface.blit(msg, msg.get_rect(center=pip_rect.center))

        # 2. Diagnostic Statistics Box (Below camera preview)
        stats_w = pip_w
        stats_h = 240
        stats_x = pip_x
        stats_y = pip_y + pip_h + 8

        panel_surf = pygame.Surface((stats_w, stats_h), pygame.SRCALPHA)
        panel_surf.fill((15, 20, 30, 225))
        surface.blit(panel_surf, (stats_x, stats_y))
        pygame.draw.rect(surface, (50, 65, 85), pygame.Rect(stats_x, stats_y, stats_w, stats_h), 1)

        # Title
        title_surf = self._font_header.render("DIAGNOSTICS [DEBUG]", True, (80, 210, 255))
        surface.blit(title_surf, (stats_x + 8, stats_y + 8))

        # Metrics text lines
        conf_str = f"{landmarks.confidence * 100:.0f}%" if landmarks.is_detected else "N/A"
        calib_str = "READY" if gesture_result.is_calibrated else "CALIBRATING..."

        # Color-coded gesture name
        gest_name = gesture_result.active_gesture.name

        lines = [
            f"Game FPS   : {game_fps:5.1f}",
            f"Pose FPS   : {pose_fps:5.1f}",
            f"Webcam     : {'CONNECTED' if camera_available else 'NOT DETECTED'}",
            f"Pose Track : {'DETECTED' if landmarks.is_detected else 'SEARCHING'}",
            f"Confidence : {conf_str}",
            f"Baseline   : {calib_str}",
            f"Delta X    : {gesture_result.delta_x:+6.3f} (±{LEAN_RIGHT_THRESHOLD:.3f})",
            f"Delta Y    : {gesture_result.delta_y:+6.3f} (J:{JUMP_THRESHOLD:.3f})",
            f"Gesture    : {gest_name}",
            f"Lane Pos   : {player.lane:+d} (World: {player.world_x:+4.1f})",
            f"Jumping    : {player.is_jumping} (Vel: {player.velocity_y:+4.1f})",
            f"Sliding    : {player.is_sliding} (H: {player.current_height:.2f})",
        ]

        cur_y = stats_y + 30
        for line in lines:
            line_color = (220, 230, 245)
            if "Gesture" in line:
                line_color = (80, 255, 140) if gest_name != "NEUTRAL" else (180, 190, 205)
            elif "Track" in line and not landmarks.is_detected:
                line_color = (255, 100, 100)
            elif "Baseline" in line and not gesture_result.is_calibrated:
                line_color = (255, 200, 70)

            text_surf = self._font_mono.render(line, True, line_color)
            surface.blit(text_surf, (stats_x + 8, cur_y))
            cur_y += 17
