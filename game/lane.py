"""
3D perspective projection and lane track rendering.
Provides camera projection math and procedural geometric rendering for lanes and objects.
"""

from typing import List, Optional, Tuple
import pygame

from config.settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    HORIZON_Y_OFFSET,
    CAMERA_HEIGHT,
    CAMERA_DISTANCE_Z,
    FIELD_OF_VIEW,
    LANE_WIDTH,
    TRACK_LENGTH,
    COLOR_SKY_TOP,
    COLOR_SKY_BOTTOM,
    COLOR_GROUND,
    COLOR_TRACK,
    COLOR_LANE_LINE,
    COLOR_MARKER_MOVING,
)


class Camera3D:
    """Calculates 3D to 2D perspective projection onto the screen."""

    def __init__(
        self,
        height: float = CAMERA_HEIGHT,
        distance_z: float = CAMERA_DISTANCE_Z,
        fov: float = FIELD_OF_VIEW,
    ):
        self.height = height
        self.distance_z = distance_z
        self.fov = fov
        self.horizon_y = int(SCREEN_HEIGHT * HORIZON_Y_OFFSET)
        self.center_x = SCREEN_WIDTH // 2

    def project(self, x: float, y: float, z: float) -> Optional[Tuple[int, int, float]]:
        """
        Projects world (x, y, z) to screen (screen_x, screen_y, scale).
        Returns None if behind or at camera plane.
        """
        dz = z - self.distance_z
        if dz <= 0.2:
            return None

        scale = self.fov / dz
        screen_x = int(self.center_x + x * scale)
        screen_y = int(self.horizon_y + (self.height - y) * scale)
        return screen_x, screen_y, scale


class LaneRenderer:
    """Renders the 3D perspective runner track and procedural scenery."""

    def __init__(self, camera: Camera3D):
        self.camera = camera
        self.track_offset = 0.0

    def update(self, speed: float, dt: float) -> None:
        """Update moving track stripes to simulate high-speed forward travel."""
        self.track_offset = (self.track_offset + speed * dt) % 6.0

    def draw_background(self, surface: pygame.Surface) -> None:
        """Draw sky gradient and ground plane."""
        # Sky gradient
        horizon = self.camera.horizon_y
        for y in range(0, horizon):
            t = y / max(1, horizon)
            r = int(COLOR_SKY_TOP[0] * (1.0 - t) + COLOR_SKY_BOTTOM[0] * t)
            g = int(COLOR_SKY_TOP[1] * (1.0 - t) + COLOR_SKY_BOTTOM[1] * t)
            b = int(COLOR_SKY_TOP[2] * (1.0 - t) + COLOR_SKY_BOTTOM[2] * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # Ground plane
        pygame.draw.rect(
            surface,
            COLOR_GROUND,
            pygame.Rect(0, horizon, SCREEN_WIDTH, SCREEN_HEIGHT - horizon),
        )

    def draw_track(self, surface: pygame.Surface) -> None:
        """Draw 3D perspective track with 3 lanes and animated moving markers."""
        track_half_width = (LANE_WIDTH * 3) / 2.0
        z_near = 0.5
        z_far = TRACK_LENGTH

        p_near_left = self.camera.project(-track_half_width, 0.0, z_near)
        p_near_right = self.camera.project(track_half_width, 0.0, z_near)
        p_far_left = self.camera.project(-track_half_width, 0.0, z_far)
        p_far_right = self.camera.project(track_half_width, 0.0, z_far)

        if p_near_left and p_near_right and p_far_left and p_far_right:
            track_poly = [
                (p_near_left[0], p_near_left[1]),
                (p_near_right[0], p_near_right[1]),
                (p_far_right[0], p_far_right[1]),
                (p_far_left[0], p_far_left[1]),
            ]
            pygame.draw.polygon(surface, COLOR_TRACK, track_poly)

        # Draw 4 lane boundary lines
        lane_boundaries = [-1.5 * LANE_WIDTH, -0.5 * LANE_WIDTH, 0.5 * LANE_WIDTH, 1.5 * LANE_WIDTH]
        for bx in lane_boundaries:
            p_n = self.camera.project(bx, 0.0, z_near)
            p_f = self.camera.project(bx, 0.0, z_far)
            if p_n and p_f:
                pygame.draw.line(surface, COLOR_LANE_LINE, (p_n[0], p_n[1]), (p_f[0], p_f[1]), 2)

        # Draw moving perspective track ties/dashes
        step = 4.0
        z_start = (step - self.track_offset) % step
        z = z_start
        while z < TRACK_LENGTH:
            p_l = self.camera.project(-track_half_width, 0.0, z)
            p_r = self.camera.project(track_half_width, 0.0, z)
            if p_l and p_r:
                alpha_factor = max(0.1, 1.0 - (z / TRACK_LENGTH))
                color = (
                    int(COLOR_MARKER_MOVING[0] * alpha_factor),
                    int(COLOR_MARKER_MOVING[1] * alpha_factor),
                    int(COLOR_MARKER_MOVING[2] * alpha_factor),
                )
                line_w = max(1, int(4 * (1.0 - z / TRACK_LENGTH)))
                pygame.draw.line(surface, color, (p_l[0], p_l[1]), (p_r[0], p_r[1]), line_w)
            z += step


def draw_projected_box(
    surface: pygame.Surface,
    camera: Camera3D,
    center_x: float,
    base_y: float,
    center_z: float,
    width: float,
    height: float,
    depth: float,
    color_front: Tuple[int, int, int],
    color_top: Tuple[int, int, int],
    color_side: Tuple[int, int, int],
    shadow: bool = True,
) -> None:
    """
    Renders a 3D rectangular box with front, top, and side faces in perspective.
    """
    x1 = center_x - width * 0.5
    x2 = center_x + width * 0.5
    y1 = base_y
    y2 = base_y + height
    z1 = center_z - depth * 0.5
    z2 = center_z + depth * 0.5

    # Optional ground shadow
    if shadow and z1 > camera.distance_z:
        s_near_l = camera.project(x1, 0.01, z1)
        s_near_r = camera.project(x2, 0.01, z1)
        s_far_r = camera.project(x2, 0.01, z2)
        s_far_l = camera.project(x1, 0.01, z2)
        if s_near_l and s_near_r and s_far_r and s_far_l:
            shadow_poly = [
                (s_near_l[0], s_near_l[1]),
                (s_near_r[0], s_near_r[1]),
                (s_far_r[0], s_far_r[1]),
                (s_far_l[0], s_far_l[1]),
            ]
            shadow_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(shadow_surf, (15, 20, 25, 140), shadow_poly)
            surface.blit(shadow_surf, (0, 0))

    # Project the 8 corners of the box
    c_flb = camera.project(x1, y1, z1)  # front-left-bottom
    c_frb = camera.project(x2, y1, z1)  # front-right-bottom
    c_flt = camera.project(x1, y2, z1)  # front-left-top
    c_frt = camera.project(x2, y2, z1)  # front-right-top

    c_blb = camera.project(x1, y1, z2)  # back-left-bottom
    c_brb = camera.project(x2, y1, z2)  # back-right-bottom
    c_blt = camera.project(x1, y2, z2)  # back-left-top
    c_brt = camera.project(x2, y2, z2)  # back-right-top

    if not all([c_flb, c_frb, c_flt, c_frt]):
        return

    # Top face
    if c_blt and c_brt:
        top_poly = [
            (c_flt[0], c_flt[1]),
            (c_frt[0], c_frt[1]),
            (c_brt[0], c_brt[1]),
            (c_blt[0], c_blt[1]),
        ]
        pygame.draw.polygon(surface, color_top, top_poly)
        pygame.draw.polygon(surface, (30, 30, 40), top_poly, 1)

    # Left face (if camera is to the right of box)
    if center_x < 0 and c_blb and c_blt:
        left_poly = [
            (c_blb[0], c_blb[1]),
            (c_flb[0], c_flb[1]),
            (c_flt[0], c_flt[1]),
            (c_blt[0], c_blt[1]),
        ]
        pygame.draw.polygon(surface, color_side, left_poly)
        pygame.draw.polygon(surface, (30, 30, 40), left_poly, 1)

    # Right face (if camera is to the left of box)
    elif center_x > 0 and c_brb and c_brt:
        right_poly = [
            (c_frb[0], c_frb[1]),
            (c_brb[0], c_brb[1]),
            (c_brt[0], c_brt[1]),
            (c_frt[0], c_frt[1]),
        ]
        pygame.draw.polygon(surface, color_side, right_poly)
        pygame.draw.polygon(surface, (30, 30, 40), right_poly, 1)

    # Front face
    front_poly = [
        (c_flb[0], c_flb[1]),
        (c_frb[0], c_frb[1]),
        (c_frt[0], c_frt[1]),
        (c_flt[0], c_flt[1]),
    ]
    pygame.draw.polygon(surface, color_front, front_poly)
    pygame.draw.polygon(surface, (20, 25, 35), front_poly, 2)
