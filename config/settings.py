"""
Kinetra - Configuration & Settings
Contains all configurable thresholds, display settings, gameplay mechanics,
and debug parameters.
"""

from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
MODELS_DIR = ASSETS_DIR / "models"
POSE_MODEL_PATH = MODELS_DIR / "pose_landmarker_lite.task"
POSE_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"

# Display & Window Settings
WINDOW_TITLE = "Kinetra - Webcam Endless Runner"
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
TARGET_FPS = 60

# Camera & Pose Detection Settings
CAMERA_INDEX = 0
CAMERA_FRAME_WIDTH = 640
CAMERA_FRAME_HEIGHT = 480
CAMERA_FLIP_HORIZONTAL = True  # Mirror mode for natural left/right movement
POSE_INFERENCE_WIDTH = 320     # Downscaled for real-time CPU performance
POSE_INFERENCE_HEIGHT = 240
POSE_CONFIDENCE_THRESHOLD = 0.5
LANDMARK_SMOOTHING_ALPHA = 0.4  # Exponential Moving Average factor (0=freeze, 1=no smoothing)

# Calibration Settings
CALIBRATION_FRAMES = 30         # Frames to calibrate initial standing neutral position
AUTO_RECALIBRATE_ON_RESET = True

# Gesture Detection Thresholds (normalized coordinates relative to neutral baseline)
# In normalized image coordinates:
# X increases to the right [0, 1]
# Y increases downward [0, 1]
LEAN_LEFT_THRESHOLD = -0.07     # Body displacement to the left relative to neutral
LEAN_RIGHT_THRESHOLD = 0.07     # Body displacement to the right relative to neutral
JUMP_THRESHOLD = -0.065         # Body displacement upward (negative delta Y in image coords)
SLIDE_THRESHOLD = 0.075         # Body displacement downward (positive delta Y in image coords)

# Gesture Debounce & Cooldown Settings
GESTURE_DEBOUNCE_FRAMES = 2     # Consecutive frames to confirm a gesture trigger
LANE_CHANGE_COOLDOWN = 0.35     # Minimum seconds between lane changes
JUMP_COOLDOWN = 0.50            # Minimum seconds between jump triggers
SLIDE_MIN_DURATION = 0.65       # Minimum seconds player remains in slide state
NEUTRAL_RESET_RATIO = 0.5       # Return to 50% of threshold required to re-arm lane shifts

# 3D Perspective Projection Settings
CAMERA_HEIGHT = 3.2             # World units above ground
CAMERA_DISTANCE_Z = -5.0        # Camera position along Z behind player
PLAYER_BASE_Z = 0.0             # Player fixed Z position in running view
FIELD_OF_VIEW = 380             # Perspective focal length multiplier
HORIZON_Y_OFFSET = 0.38         # Horizon height on screen (0.0=top, 1.0=bottom)

# Track & Lane Settings
LANE_WIDTH = 2.4                # World distance between lane centers
LANE_COUNT = 3                  # Left (-1), Center (0), Right (1)
LANE_INDICES = [-1, 0, 1]
TRACK_LENGTH = 120.0            # Visible track length ahead in world units

# Player Physics & Movement
PLAYER_RUN_SPEED_INITIAL = 16.0 # World units per second
PLAYER_MAX_SPEED = 28.0         # Max running speed cap
PLAYER_SPEED_ACCELERATION = 0.15 # Speed increase per second survived
LANE_SWITCH_SPEED = 12.0        # Horizontal lerp speed
JUMP_VELOCITY = 9.5             # Initial upward jump velocity
GRAVITY = 22.0                  # Gravity pulling player down
PLAYER_WIDTH = 1.0              # World width
PLAYER_HEIGHT_STAND = 1.6       # Standing world height
PLAYER_HEIGHT_SLIDE = 0.7       # Sliding world height

# Obstacle Settings
OBSTACLE_SPAWN_INTERVAL_MIN = 1.2 # Minimum seconds between spawns
OBSTACLE_SPAWN_INTERVAL_MAX = 2.4 # Maximum seconds between spawns
MIN_OBSTACLE_Z_SPACING = 14.0     # Minimum world distance between successive obstacles
HURDLE_HEIGHT = 0.75            # Low obstacle (jump over)
OVERHEAD_MIN_Y = 0.85           # High obstacle bottom clearance (slide under)
OVERHEAD_MAX_Y = 2.2            # High obstacle top
BARRIER_HEIGHT = 2.0            # Full barrier (must switch lanes)

# Debug Overlay Settings
DEBUG_MODE = True               # Default debug overlay state (toggle with Tab / F3)
DEBUG_PIP_WIDTH = 240           # Width of picture-in-picture webcam feed
DEBUG_PIP_HEIGHT = 180          # Height of picture-in-picture webcam feed
DEBUG_PIP_MARGIN = 16

# Visual Palette (Clean, minimal placeholder styling)
COLOR_SKY_TOP = (15, 20, 35)
COLOR_SKY_BOTTOM = (35, 45, 75)
COLOR_GROUND = (25, 28, 36)
COLOR_TRACK = (40, 44, 58)
COLOR_LANE_LINE = (80, 90, 120)
COLOR_MARKER_MOVING = (100, 115, 155)

COLOR_PLAYER = (50, 180, 255)
COLOR_PLAYER_OUTLINE = (20, 100, 180)
COLOR_PLAYER_SHADOW = (15, 18, 25, 160)

COLOR_OBSTACLE_HURDLE = (245, 166, 35)     # Amber/Orange (Jump)
COLOR_OBSTACLE_OVERHEAD = (0, 210, 210)    # Cyan/Teal (Slide)
COLOR_OBSTACLE_BARRIER = (235, 60, 60)     # Red (Switch lane)

COLOR_UI_TEXT = (240, 240, 245)
COLOR_UI_MUTED = (150, 160, 175)
COLOR_UI_ACCENT = (50, 220, 150)
COLOR_UI_DANGER = (240, 70, 70)
COLOR_UI_PANEL = (20, 24, 34, 210)

COLOR_SKELETON_JOINT = (0, 255, 120)
COLOR_SKELETON_BONE = (0, 200, 255)
