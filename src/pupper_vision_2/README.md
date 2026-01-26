# pupper_vision - Vision Package for Mini Pupper

A clean, simple ROS2 vision package for Mini Pupper with OV5647 camera. 
Designed for teaching robotics - much simpler than the MangDang implementation!

## Features

This package provides **4 detection modes** that all work out of the box:

| Mode | Description | Control Output |
|------|-------------|----------------|
| **Color** | Detect colors from a dictionary | Turn towards detected color |
| **Shape** | Track colored circle stickers | Forward/backward + turn to maintain distance |
| **Person** | Person detection and tracking | Turn to center person in frame |
| **Pose** | Gesture-based control | Arm positions control movement |

## Hardware Requirements

- Mini Pupper (v1 or v2)
- OV5647 camera module (RPi Camera v1.3)
- Ubuntu 22.04 with ROS2 Humble

## Quick Start

### Installation

```bash
# Clone into your workspace
cd ~/ros2_ws/src
git clone <this-repo> pupper_vision

# Install dependencies
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y

# For pose detection (optional but recommended)
pip3 install mediapipe --break-system-packages

# Build
colcon build --packages-select pupper_vision
source install/setup.bash
```

### Running

```bash
# Terminal 1: Start Mini Pupper bringup (if not already running)
ros2 launch mini_pupper_bringup bringup.launch.py

# Terminal 2: Start vision (pick one mode)

# Task 1: Color Detection
ros2 launch pupper_vision vision.launch.py mode:=color

# Task 2: Shape Detection (track green circles)
ros2 launch pupper_vision vision.launch.py mode:=shape target_color:=green

# Task 3: Person Detection
ros2 launch pupper_vision vision.launch.py mode:=person

# Task 4: Pose Detection
ros2 launch pupper_vision vision.launch.py mode:=pose
```

### With Visualization (for PC viewing)

```bash
# On the Mini Pupper
ros2 launch pupper_vision vision.launch.py mode:=person visualization:=true

# On your PC (same network)
ros2 run rqt_image_view rqt_image_view
# Then select /vision/visualization topic
```

### Simulation Mode (no camera needed)

```bash
# Test on your laptop without camera hardware
ros2 launch pupper_vision vision.launch.py mode:=color simulation:=true visualization:=true
```

## Detailed Mode Descriptions

### Task 1: Color Detection

Detects colors from a predefined dictionary and announces what's detected.

```bash
ros2 launch pupper_vision vision.launch.py mode:=color
```

**Topics Published:**
- `/vision/colors_detected` (std_msgs/String): JSON with detected colors
- `/cmd_vel` (geometry_msgs/Twist): Turn towards largest color region

**Default Colors:** red, orange, yellow, green, blue, purple, pink

**Customize in `config/params.yaml`:**
```yaml
color_detector:
  ros__parameters:
    enabled_colors: [red, green, blue]  # Only these colors
    min_area: 500  # Minimum detection size
```

### Task 2: Shape Detection

Tracks colored circle stickers and moves to maintain a target distance.

```bash
ros2 launch pupper_vision vision.launch.py mode:=shape target_color:=green
```

**Control Logic:**
- Circle too small (far away) → Move forward
- Circle too big (too close) → Move backward
- Circle off-center → Turn to center it

**Parameters:**
- `target_radius`: Target circle size in pixels (default: 80)
- `radius_tolerance`: How close is "good enough" (default: 15)
- `target_color`: Which color sticker to track

### Task 3: Person Detection

Detects people and turns to keep them centered in the frame.

```bash
ros2 launch pupper_vision vision.launch.py mode:=person
```

**Models:**
- `hog`: Built-in OpenCV HOG detector (no model files needed, slower)
- `mobilenet_ssd`: MobileNet SSD (faster, needs model files in `~/models/`)

**Control:** Proportional control to center the largest detected person.

### Task 4: Pose Detection

Uses MediaPipe Pose to detect arm gestures for control.

```bash
ros2 launch pupper_vision vision.launch.py mode:=pose
```

**Gestures:**
| Gesture | Action |
|---------|--------|
| Both arms up ↑↑ | Move forward |
| Left arm up ↑○ | Turn left |
| Right arm up ○↑ | Turn right |
| Arms down / T-pose | Stop |

**Requires:** `pip3 install mediapipe`

## ROS2 Topics

### Subscribed
- `/camera/image_raw` - Camera frames (from camera_node)

### Published
All detection nodes publish:
- `/vision/[mode]_detected` - Detection results (JSON)
- `/vision/visualization` - Annotated image (if enabled)
- `/cmd_vel` - Velocity commands

## Configuration

Edit `config/params.yaml` to tune parameters for your environment:

```yaml
# Adjust camera
camera:
  ros__parameters:
    flip: true  # If camera is upside down
    
# Tune color detection
color_detector:
  ros__parameters:
    min_area: 500  # Increase if getting false positives
    
# Tune person detection
person_detector:
  ros__parameters:
    confidence_threshold: 0.5  # Increase for fewer false positives
    kp: 0.8  # Turning responsiveness
```

## Troubleshooting

### Camera not working
```bash
# Check if picamera2 is installed
python3 -c "from picamera2 import Picamera2; print('OK')"

# Test camera directly
libcamera-hello --timeout 5000
```

### Colors not detected
- Check lighting conditions
- Tune HSV ranges in the code or via dynamic reconfigure
- Increase/decrease `min_area` parameter

### Person detection slow
- Use `model_type: hog` for simplicity
- Reduce frame rate: `fps: 15`
- Reduce resolution: `width: 320, height: 240`

### MediaPipe not working
```bash
pip3 install mediapipe --break-system-packages
# Or for ARM64:
pip3 install mediapipe-silicon  # (if available for your platform)
```

## Architecture

```
┌──────────────────┐
│   camera_node    │ ─────► /camera/image_raw
└──────────────────┘
         │
         ▼
┌──────────────────┐
│ color_detector   │
│ shape_detector   │ ─────► /cmd_vel ──────► Mini Pupper
│ person_detector  │
│ pose_detector    │ ─────► /vision/visualization
└──────────────────┘
```

## Comparison with MangDang Implementation

| Feature | This Package | MangDang mini_pupper_tracking |
|---------|-------------|------------------------------|
| Complexity | ~500 lines | ~2000+ lines |
| Dependencies | opencv, (mediapipe) | YOLO11, Docker, many deps |
| Model Files | Optional | Required |
| Teaching Friendly | ✅ Yes | ❌ Overly complex |
| Works Out of Box | ✅ Yes | ❌ Requires setup |
| Documentation | Clear | Sparse |

## Contributing

This package was created because the official MangDang tracking package was too complex for teaching purposes. Contributions welcome!

## License

MIT License - Use freely for education and research.

---

Created by Baccus Lab for the SpotDMouse project.
Based on the working P1-LetThereBSight implementation.
