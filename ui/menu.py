"""
Main menu UI rendering.
Displays title, instructions, camera readiness, and start triggers.
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
from gestures.state import GestureStateResult


class MainMenuUI:
    """Renders the main menu overlay."""

    def __init__(self):
        self._font_title = pygame.font.SysFont("Arial", 52, bold=True)
        self._font_subtitle = pygame.font.SysFont("Arial", 22)
        self._font_button = pygame.font.SysFont("Arial", 32, bold=True)
        self._font_hint = pygame.font.SysFont("Arial", 18)

    def draw(
        self,
        surface: pygame.Surface,
        camera_available: bool,
        gesture_result: GestureStateResult,
    ) -> None:
        """Draw main menu overlay onto surface."""
        # Semi-transparent backdrop overlay
        backdrop = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        backdrop.fill((10, 14, 22, 180))
        surface.blit(backdrop, (0, 0))

        center_x = SCREEN_WIDTH // 2

        # Title & Subtitle
        title_surf = self._font_title.render("KINETRA", True, COLOR_UI_TEXT)
        title_rect = title_surf.get_rect(center=(center_x, SCREEN_HEIGHT // 2 - 140))
        surface.blit(title_surf, title_rect)

        sub_surf = self._font_subtitle.render("Local Webcam Endless Runner", True, COLOR_UI_MUTED)
        sub_rect = sub_surf.get_rect(center=(center_x, SCREEN_HEIGHT // 2 - 90))
        surface.blit(sub_surf, sub_rect)

        # Main Instruction (Required by prompt)
        instr_surf = self._font_button.render("Move your body to control the runner.", True, COLOR_UI_ACCENT)
        instr_rect = instr_surf.get_rect(center=(center_x, SCREEN_HEIGHT // 2 - 20))
        surface.blit(instr_surf, instr_rect)

        # Start Button / Action Prompt
        prompt_panel = pygame.Rect(center_x - 180, SCREEN_HEIGHT // 2 + 35, 360, 60)
        pygame.draw.rect(surface, (30, 40, 55), prompt_panel, border_radius=10)
        pygame.draw.rect(surface, COLOR_UI_ACCENT, prompt_panel, 2, border_radius=10)

        start_text = self._font_button.render("START", True, COLOR_UI_TEXT)
        start_rect = start_text.get_rect(center=prompt_panel.center)
        surface.blit(start_text, start_rect)

        # Sub-hint
        hint_surf = self._font_hint.render("Press SPACE, Enter, or Jump to Start", True, COLOR_UI_MUTED)
        hint_rect = hint_surf.get_rect(center=(center_x, SCREEN_HEIGHT // 2 + 115))
        surface.blit(hint_surf, hint_rect)

        # Camera status pill at bottom
        status_y = SCREEN_HEIGHT - 65
        if camera_available:
            if gesture_result.is_calibrated:
                status_text = "● Webcam Active | Body Calibrated & Ready"
                status_color = COLOR_UI_ACCENT
            else:
                status_text = "● Webcam Active | Stand in view to calibrate..."
                status_color = (255, 200, 60)
        else:
            status_text = "▲ Webcam Not Detected | Using Keyboard Fallback"
            status_color = (240, 100, 100)

        stat_surf = self._font_hint.render(status_text, True, status_color)
        stat_rect = stat_surf.get_rect(center=(center_x, status_y))
        surface.blit(stat_surf, stat_rect)

        # Fallback controls info
        fallback_surf = self._font_hint.render(
            "Keyboard Fallback: A / Left = Left  |  D / Right = Right  |  Space = Jump  |  S / Down = Slide",
            True,
            (130, 140, 155),
        )
        fb_rect = fallback_surf.get_rect(center=(center_x, status_y + 26))
        surface.blit(fallback_surf, fb_rect)
