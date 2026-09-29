"""
Game Over UI screen.
Displays final score, high score, distance survived, and restart prompt.
"""

import pygame

from config.settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    COLOR_UI_TEXT,
    COLOR_UI_MUTED,
    COLOR_UI_ACCENT,
    COLOR_UI_DANGER,
    COLOR_UI_PANEL,
)


class GameOverUI:
    """Renders the game over screen overlay."""

    def __init__(self):
        self._font_title = pygame.font.SysFont("Arial", 48, bold=True)
        self._font_score = pygame.font.SysFont("Arial", 36, bold=True)
        self._font_label = pygame.font.SysFont("Arial", 22)
        self._font_button = pygame.font.SysFont("Arial", 26, bold=True)
        self._font_hint = pygame.font.SysFont("Arial", 18)

    def draw(
        self,
        surface: pygame.Surface,
        final_score: float,
        high_score: float,
        distance: float,
    ) -> None:
        """Render Game Over overlay onto game surface."""
        # Dimming backdrop overlay
        backdrop = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        backdrop.fill((15, 10, 15, 210))
        surface.blit(backdrop, (0, 0))

        center_x = SCREEN_WIDTH // 2
        card_w, card_h = 420, 360
        card_rect = pygame.Rect(
            center_x - card_w // 2,
            (SCREEN_HEIGHT - card_h) // 2 - 20,
            card_w,
            card_h,
        )

        # Card panel
        panel_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        panel_surf.fill(COLOR_UI_PANEL)
        surface.blit(panel_surf, card_rect.topleft)
        pygame.draw.rect(surface, COLOR_UI_DANGER, card_rect, 2, border_radius=12)

        # Title
        title_surf = self._font_title.render("GAME OVER", True, COLOR_UI_DANGER)
        title_rect = title_surf.get_rect(center=(center_x, card_rect.y + 45))
        surface.blit(title_surf, title_rect)

        # Final Score
        score_val = self._font_score.render(f"{int(final_score):,}", True, COLOR_UI_TEXT)
        score_rect = score_val.get_rect(center=(center_x, card_rect.y + 115))
        surface.blit(score_val, score_rect)

        score_lbl = self._font_label.render("FINAL SCORE", True, COLOR_UI_MUTED)
        lbl_rect = score_lbl.get_rect(center=(center_x, card_rect.y + 150))
        surface.blit(score_lbl, lbl_rect)

        # High Score and Distance Stats
        stats_text = f"High Score: {int(high_score):,}   |   Distance: {distance:.0f}m"
        stats_surf = self._font_label.render(stats_text, True, COLOR_UI_MUTED)
        stats_rect = stats_surf.get_rect(center=(center_x, card_rect.y + 195))
        surface.blit(stats_surf, stats_rect)

        # Restart Button / Prompt
        btn_rect = pygame.Rect(center_x - 140, card_rect.y + 240, 280, 52)
        pygame.draw.rect(surface, (40, 50, 70), btn_rect, border_radius=8)
        pygame.draw.rect(surface, COLOR_UI_ACCENT, btn_rect, 2, border_radius=8)

        btn_surf = self._font_button.render("RESTART", True, COLOR_UI_ACCENT)
        b_rect = btn_surf.get_rect(center=btn_rect.center)
        surface.blit(btn_surf, b_rect)

        # Sub-hint
        hint_surf = self._font_hint.render("Press SPACE, R, or Jump to play again", True, (160, 170, 185))
        hint_rect = hint_surf.get_rect(center=(center_x, card_rect.y + 320))
        surface.blit(hint_surf, hint_rect)
