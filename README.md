# Kinetra

A lightweight, local webcam-controlled 3D endless runner game.

The player automatically runs forward down a three-lane track. A local pose-estimation model observes the player through their laptop webcam, extracts normalized body landmarks, and converts physical movements into deterministic gameplay gestures (**Move Left**, **Move Right**, **Jump**, and **Slide/Duck**).

**100% Local & Offline**:
- No cloud APIs
- No LLMs
- No paid AI services
- No external game engine installation required

---

## Table of Contents

1. [Overview](#overview)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [How to Run](#how-to-run)
5. [Controls & Fallback](#controls--fallback)
6. [Gesture Detection System](#gesture-detection-system)
7. [Configuring Thresholds](#configuring-thresholds)
8. [Debug Mode](#debug-mode)
9. [Project Architecture](#project-architecture)
10. [Component Responsibilities](#component-responsibilities)

---

## Overview

Kinetra is built as a modular foundation and prototype for gesture-driven interactive games. The architecture strictly isolates webcam capture, pose inference, deterministic gesture extraction, gameplay logic, and rendering.

- **3 Horizontal Lanes**: Left (-1), Center (0), Right (+1).
- **Physical Gestures**:
  - **Lean Left** $\rightarrow$ Switch one lane left.
  - **Lean Right** $\rightarrow$ Switch one lane right.
  - **Jump Up** $\rightarrow$ Jump over low hurdles.
  - **Duck / Crouch Down** $\rightarrow$ Slide under overhead barriers.
  - **Lane Dodge** $\rightarrow$ Move away from full-height roadblocks.
- **Scoring**: Score accumulates based on survival time and distance traveled.
- **Game States**: `MAIN MENU`, `PLAYING`, `GAME OVER`.

---

## Requirements

- **Operating System**: Windows, macOS, or Linux
- **Python**: 3.10, 3.11, or 3.12
- **Hardware**: Standard laptop webcam (or USB webcam)
- **Dependencies**:
  - `mediapipe` (Google MediaPipe Tasks PoseLandmarker)
  - `opencv-python` (Webcam video stream)
  - `pygame` (Game engine, audio/display, and 3D perspective projection)
  - `numpy` (Array operations and coordinate filtering)

---

## Installation

1. **Clone or Navigate to the Repository**:
   ```bash
   cd E:\Coding\Projects\Kinetra
   ```

2. **Install Dependencies**:
   ```bash
   python -m pip install -r requirements.txt
   ```

3. **Pose Model Asset**:
   The lightweight local model (`pose_landmarker_lite.task`, ~5.7 MB) is stored locally in `assets/models/pose_landmarker_lite.task`. If missing, the pose estimator will automatically download it once from Google's official CDN upon first startup, after which it runs 100% offline.

---

## How to Run

Launch the game with a single command:

```bash
python main.py
```

### Self-Verification Tests
You can also run the headless automated test suite at any time to verify module integrity:

```bash
python test_verification.py
```

---

## Controls & Fallback

The game is designed to be controlled via physical body gestures, but includes a full **keyboard development fallback** so testing is possible without a webcam:

| Action | Physical Gesture | Keyboard Fallback |
| :--- | :--- | :--- |
| **Move Left** | Lean body to your left | `A` or `Left Arrow` |
| **Move Right** | Lean body to your right | `D` or `Right Arrow` |
| **Jump** | Jump upward with feet/hips leaving ground | `Space` |
| **Slide / Duck** | Crouch down / lower upper body | `S` or `Down Arrow` |
| **Start / Restart** | Jump or stand in view | `Space`, `Enter`, or `R` |
| **Toggle Debug Overlay** | — | `Tab` or `F3` |
| **Recalibrate Posture** | — | `C` |
| **Quit Game** | — | `Escape` |

---

## Gesture Detection System

Gesture recognition is completely deterministic and consumes normalized landmark coordinates:

1. **Webcam Mirroring**: The video stream is horizontally mirrored (`cv2.flip(frame, 1)`), so your physical movements correspond directly to mirror reflections on screen.
2. **Exponential Moving Average (EMA) Smoothing**: High-frequency landmark sensor noise is filtered with an EMA filter ($\alpha = 0.40$).
3. **Standing Baseline Calibration**:
   - When standing in view of the webcam, the system samples initial frames to compute your neutral torso center $(x_{baseline}, y_{baseline})$ and torso height.
   - All subsequent physical movements are computed as relative displacements $\Delta x$ and $\Delta y$, normalized by your torso height (ensuring distance invariance from the camera).
4. **Debounce Logic**:
   - Candidate gestures must persist for at least `GESTURE_DEBOUNCE_FRAMES` (default: 2 frames) before confirmation, rejecting transient frame noise.
5. **Event vs. State Logic**:
   - **Jump (Event)**: Detects a significant upward transition ($\Delta y < -0.065$). Fires once as a discrete event and enforces a cooldown (`JUMP_COOLDOWN = 0.50s`). Must return to neutral vertical range to re-arm.
   - **Move Left / Right (Event)**: Detects lateral body lean ($\Delta x < -0.07$ or $\Delta x > +0.07$). Moves the player one lane, then locks until the player returns toward center and cooldown expires (`LANE_CHANGE_COOLDOWN = 0.35s`).
   - **Slide / Duck (State)**: Detects upper body lowering ($\Delta y > +0.075$). The player remains crouching while ducked, with a minimum duration guarantee (`SLIDE_MIN_DURATION = 0.65s`).

---

## Configuring Thresholds

All thresholds and parameters are centralized in [`config/settings.py`](file:///E:/Coding/Projects/Kinetra/config/settings.py):

```python
# Gesture Sensitivity Thresholds (Normalized Screen Units)
LEAN_LEFT_THRESHOLD = -0.07     # Body displacement left of center
LEAN_RIGHT_THRESHOLD = 0.07     # Body displacement right of center
JUMP_THRESHOLD = -0.065         # Upward body displacement
SLIDE_THRESHOLD = 0.075         # Downward body displacement

# Debounce & Cooldown Timers
GESTURE_DEBOUNCE_FRAMES = 2     # Consecutive frames to confirm gesture
LANE_CHANGE_COOLDOWN = 0.35     # Minimum seconds between lane changes
JUMP_COOLDOWN = 0.50            # Minimum seconds between jumps
SLIDE_MIN_DURATION = 0.65       # Minimum sliding time

# Smoothing & Calibration
LANDMARK_SMOOTHING_ALPHA = 0.4  # EMA factor (0 = freeze, 1 = raw)
CALIBRATION_FRAMES = 30         # Standing frames to calibrate baseline
```

---

## Debug Mode

Debug mode provides full transparency into pose tracking without permanently cluttering the gameplay screen:

- **Toggle**: Press `Tab` or `F3` during gameplay or menu.
- **Default State**: Set `DEBUG_MODE = True` or `False` in [`config/settings.py`](file:///E:/Coding/Projects/Kinetra/config/settings.py).
- **Debug Elements Displayed**:
  1. **Picture-in-Picture Webcam Feed**: Live camera view in the top-right corner.
  2. **Pose Skeleton Overlay**: Joint landmarks (green dots) and connecting bones (cyan lines).
  3. **Displacement Vector**: Torso center tracking point against calibrated baseline crosshair.
  4. **Diagnostic Metrics**:
     - Game Engine FPS & Pose Inference FPS
     - Camera status and detection confidence (%)
     - Real-time $\Delta x$ and $\Delta y$ offsets alongside active thresholds
     - Active detected gesture
     - Player state (Lane, Grounded, Jumping velocity, Sliding height)

---

## Project Architecture

```
kinetra/
│
├── assets/
│   └── models/
│       └── pose_landmarker_lite.task   # MediaPipe local model asset (~5.7 MB)
│
├── config/
│   ├── __init__.py
│   └── settings.py                     # All thresholds, dimensions, physics & colors
│
├── pose/
│   ├── __init__.py
│   ├── landmarks.py                    # LandmarkPoint, PoseLandmarks & LandmarkSmoother
│   ├── estimator.py                    # Local MediaPipe Tasks PoseLandmarker wrapper
│   └── webcam.py                       # Background capture & inference worker thread
│
├── gestures/
│   ├── __init__.py
│   ├── detector.py                     # Deterministic gesture classification & baseline
│   └── state.py                        # Debounce state machine, cooldowns & GameActions
│
├── game/
│   ├── __init__.py
│   ├── input_handler.py                # Bridges keyboard fallback & pose gestures
│   ├── lane.py                         # 3D perspective camera & procedural track rendering
│   ├── player.py                       # 3-lane movement, jump physics & slide hitbox
│   ├── obstacle.py                     # Hurdle, Overhead & Barrier spawning + 3D AABB collisions
│   └── engine.py                       # Game loop, state machine, distance & score tracking
│
├── ui/
│   ├── __init__.py
│   ├── menu.py                         # Main Menu overlay & start triggers
│   ├── hud.py                          # In-game score, distance, lane dots & gesture pill
│   ├── game_over.py                    # Game Over screen & restart options
│   └── debug_overlay.py                # PIP camera feed, skeleton & diagnostic metrics
│
├── main.py                             # Main application entry point
├── test_verification.py                # Headless automated verification suite
├── test_render.py                      # Headless render verification suite
├── requirements.txt                    # Project dependencies
└── README.md                           # Documentation
```

---

## Component Responsibilities

| Responsibility | Module | Purpose |
| :--- | :--- | :--- |
| **Pose Detection** | [`pose/`](file:///E:/Coding/Projects/Kinetra/pose/) | Captures webcam video on an asynchronous background thread, mirrors frames, runs local inference using MediaPipe Tasks, and produces normalized landmark coordinates (`nose`, `shoulders`, `hips`, `knees`, `ankles`). |
| **Gesture Recognition** | [`gestures/`](file:///E:/Coding/Projects/Kinetra/gestures/) | Consumes normalized smoothed landmarks, tracks neutral standing baseline, measures scale-invariant displacement, debounces noise, enforces cooldowns, and classifies discrete events vs continuous states. |
| **Game Input** | [`game/input_handler.py`](file:///E:/Coding/Projects/Kinetra/game/input_handler.py) | Unifies physical gestures and keyboard fallback (`A`, `D`, `Space`, `S`) into common `GameAction` commands. |
| **Game Logic** | [`game/`](file:///E:/Coding/Projects/Kinetra/game/) | Manages player physics (jump gravity, lane lerping, slide crouch), obstacle waves (Hurdle, Overhead, Barrier), 3D AABB collision checks, and game states (`MAIN_MENU`, `PLAYING`, `GAME_OVER`). |
| **Rendering** | [`game/lane.py`](file:///E:/Coding/Projects/Kinetra/game/lane.py) & [`ui/`](file:///E:/Coding/Projects/Kinetra/ui/) | Computes 3D-to-2D perspective projection, draws the 3-lane track with moving sleepers, renders placeholder 3D cuboids, and draws HUD, Menu, Game Over, and the live camera Debug Overlay. |
