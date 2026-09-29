"""
In-game HUD rendering.
Displays real-time score, distance, lane position indicator, and gesture feedback.
"""

import pygame

from config.settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    COLOR_UI_TEXT,
    COLOR_UI_MUTED,
    COLOR_UI_ACCENT,
    COLOR_UI_PANEL,
)
from gestures.detector import GestureType
from gestures.state import GestureStateResult


class GameHUD:
    """Renders the in-game heads-up display."""

    def __init__(self):
        self._font_score = pygame.font.SysFont("Arial", 36, bold=True)
        self._font_label = pygame.font.SysFont("Arial", 16)
        self._font_gesture = pygame.font.SysFont("Arial", 20, bold=True)
        self._font_hint = pygame.font.SysFont("Arial", 15)

    def draw(
        self,
        surface: pygame.Surface,
        score: float,
        distance: float,
        current_lane: int,
        gesture_result: GestureStateResult,
        debug_mode: bool,
    ) -> None:
        """Render HUD elements onto game surface."""
        # 1. Score & Distance Panel (Top-Left)
        score_panel = pygame.Rect(20, 16, 200, 68)
        panel_surf = pygame.Surface((score_panel.width, score_panel.height), pygame.SRCALPHA)
        panel_surf.fill(COLOR_UI_PANEL)
        surface.blit(panel_surf, score_panel.topleft)
        pygame.draw.rect(surface, (60, 70, 90), score_panel, 1, border_radius=6)

        score_text = self._font_score.render(f"{int(score):05d}", True, COLOR_UI_TEXT)
        surface.blit(score_text, (score_panel.x + 14, score_panel.y + 8))

        dist_text = self._font_label.render(f"DIST: {distance:.0f}m", True, COLOR_UI_MUTED)
        surface.blit(dist_text, (score_panel.x + 14, score_panel.y + 44))

        # 2. Gesture Feedback Pill (Top-Center)
        gest = gesture_result.active_gesture
        if gest == GestureType.LEFT:
            gest_text = "◀ LEAN LEFT"
            gest_color = (80, 200, 255)
        elif gest == GestureType.RIGHT:
            gest_text = "LEAN RIGHT ▶"
            gest_color = (80, 200, 255)
        elif gest == GestureType.JUMP:
            gest_text = "▲ JUMP"
            gest_color = (80, 255, 140)
        elif gest == GestureType.SLIDE or gesture_result.is_sliding:
            gest_text = "▼ SLIDE / DUCK"
            gest_color = (255, 200, 60)
        elif gest == GestureType.NEUTRAL:
            gest_text = "● NEUTRAL"
            gest_color = (160, 175, 195)
        else:
            gest_text = "○ SEARCHING..."
            gest_color = (130, 140, 155)

        pill_w, pill_h = 200, 36
        pill_rect = pygame.Rect((SCREEN_WIDTH - pill_w) // 2, 20, pill_w, pill_h)
        pill_surf = pygame.Surface((pill_w, pill_h), pygame.SRCALPHA)
        pill_surf.fill(COLOR_UI_PANEL)
        surface.blit(pill_surf, pill_rect.topleft)
        pygame.draw.rect(surface, gest_color, pill_rect, 2, border_radius=18)

        text_surf = self._font_gesture.render(gest_text, True, gest_color)
        text_rect = text_surf.get_rect(center=pill_rect.center)
        surface.blit(text_surf, text_rect)

        # 3. Debug Toggle Hint (Top-Right)
        debug_label = "[Tab] Debug: ON" if debug_mode else "[Tab] Debug: OFF"
        hint_surf = self._font_hint.render(debug_label, True, COLOR_UI_MUTED)
        hint_rect = hint_surf.get_rect(topright=(SCREEN_WIDTH - 20, 20))
        surface.blit(hint_surf, hint_rect)

        # 4. Lane Position Dots (Bottom-Center)
        dot_y = SCREEN_HEIGHT - 32
        lane_x_coords = [
            SCREEN_WIDTH // 2 - 40,  # Left (-1)
            SCREEN_WIDTH // 2,       # Center (0)
            SCREEN_WIDTH // 2 + 40,  # Right (1)
        ]
        lane_indices = [-1, 0, 1]

        for lx, l_idx in zip(lane_x_coords, lane_indices):
            if l_idx == current_lane:
                pygame.draw.circle(surface, COLOR_UI_ACCENT, (lx, dot_y), 9)
                pygame.draw.circle(surface, (255, 255, 255), (lx, dot_y), 5)
            else:
                pygame.draw.circle(surface, (70, 80, 100), (lx, dot_y), 6)
