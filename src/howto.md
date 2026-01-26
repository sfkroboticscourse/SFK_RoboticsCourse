# Mini Pupper Vision Lab - Student Guide

This guide walks you through running 4 vision tasks on the Mini Pupper robot using the OV5647 camera.

---

## Overview

| Task | What It Does | Robot Behavior |
|------|--------------|----------------|
| **1. Color Detection** | Detects colors (red, green, blue, etc.) | Turns toward detected color |
| **2. Shape Detection** | Tracks colored circle stickers | Moves forward/backward + turns to maintain distance |
| **3. Person Detection** | Detects people | Turns to keep person centered in frame |
| **4. Pose Detection** | Reads your arm gestures | You control the robot with arm positions |

---

## What You Need

- Mini Pupper (powered on, connected to WiFi)
- SSH access to Mini Pupper
- Colored objects / circle stickers (for Tasks 1 & 2)

---

## Setup: SSH into Mini Pupper

Open **two terminal windows** on your computer and SSH into the Mini Pupper in both:

```bash
# Terminal 1
ssh ubuntu@<MINI_PUPPER_IP>

# Terminal 2
ssh ubuntu@<MINI_PUPPER_IP>
```

Replace `<MINI_PUPPER_IP>` with your robot's IP address (shown on the Mini Pupper's display).

---

## Running the Vision Tasks

### Step 1: Start the Robot (Terminal 1)

This makes the robot able to walk. Run this first and **leave it running**:

```bash
# Terminal 1 - Robot Bringup
source ~/ros2_ws/install/setup.bash
ros2 launch mini_pupper_bringup bringup.launch.py
```

You should see the robot stand up. **Keep this terminal open.**

---

### Step 2: Start a Vision Task (Terminal 2)

Pick ONE of the following tasks to run:

#### Task 1: Color Detection
```bash
# Terminal 2
source ~/ros2_ws/install/setup.bash
ros2 launch pupper_vision vision.launch.py mode:=color
```
**What happens:** Hold a colored object (red, green, blue, yellow, orange, purple, pink) in front of the camera. The robot will turn toward it. Watch the terminal - it prints which colors are detected.

---

#### Task 2: Shape Detection (Circle Tracking)
```bash
# Terminal 2
source ~/ros2_ws/install/setup.bash
ros2 launch pupper_vision vision.launch.py mode:=shape target_color:=green
```
**What happens:** Hold a GREEN circle sticker in front of the camera. The robot will:
- Turn to center the circle
- Move FORWARD if the circle is too small (too far away)
- Move BACKWARD if the circle is too big (too close)

**To track a different color:**
```bash
ros2 launch pupper_vision vision.launch.py mode:=shape target_color:=red
ros2 launch pupper_vision vision.launch.py mode:=shape target_color:=blue
```

---

#### Task 3: Person Detection
```bash
# Terminal 2
source ~/ros2_ws/install/setup.bash
ros2 launch pupper_vision vision.launch.py mode:=person
```
**What happens:** Stand in front of the robot. It will turn to keep you centered in its view. If you move left, it turns left. If you move right, it turns right.

---

#### Task 4: Pose Detection (Gesture Control)
```bash
# Terminal 2
source ~/ros2_ws/install/setup.bash
ros2 launch pupper_vision vision.launch.py mode:=pose
```
**What happens:** Stand in front of the robot and use arm gestures to control it:

| Your Gesture | Robot Action |
|--------------|--------------|
| Both arms UP ↑↑ | Move forward |
| Left arm UP only ↑○ | Turn left |
| Right arm UP only ○↑ | Turn right |
| Arms DOWN or T-pose | Stop |

---

## Stopping

1. Press `Ctrl+C` in Terminal 2 to stop the vision task
2. Press `Ctrl+C` in Terminal 1 to stop the robot (it will sit down)

---

## Troubleshooting

### "No module named pupper_vision"
Make sure you sourced the workspace:
```bash
source ~/ros2_ws/install/setup.bash
```

### Robot not moving
- Is Terminal 1 still running bringup.launch.py?
- Is the robot standing? (It needs to be standing to move)

### Camera not working
Test the camera directly:
```bash
libcamera-hello --timeout 5000
```

### Colors not being detected
- Make sure there's enough light
- Hold the colored object closer to the camera
- Try a more saturated/bright color

### Person detection not working
- Stand further back (need full upper body visible)
- Make sure there's good lighting
- Try standing against a plain background

---

## Understanding the Output

When running, you'll see log messages like:

**Color Detection:**
```
[INFO] Colors detected: ['red', 'green']
```

**Shape Detection:**
```
[INFO] green circle detected: radius=95px, status=TOO_CLOSE, vx=-0.08, wz=0.12
```
- `radius` = how big the circle appears (bigger = closer)
- `status` = TOO_FAR, OK, or TOO_CLOSE
- `vx` = forward/backward speed (positive = forward)
- `wz` = turning speed (positive = turn left)

**Person Detection:**
```
[INFO] Person detected: conf=0.72, center=(412, 289), yaw_rate=0.35
```
- `conf` = confidence (0-1, higher = more sure it's a person)
- `center` = where the person is in the image
- `yaw_rate` = how fast robot is turning to track

**Pose Detection:**
```
[INFO] Pose detected: BOTH_ARMS_UP_FORWARD, vx=0.15, wz=0.00
```

---

## Quick Reference

```bash
# Always run Terminal 1 first:
ros2 launch mini_pupper_bringup bringup.launch.py

# Then pick ONE for Terminal 2:
ros2 launch pupper_vision vision.launch.py mode:=color      # Task 1
ros2 launch pupper_vision vision.launch.py mode:=shape      # Task 2
ros2 launch pupper_vision vision.launch.py mode:=person     # Task 3
ros2 launch pupper_vision vision.launch.py mode:=pose       # Task 4
```

---

## For Instructors: Visualization Setup

To see what the camera sees (requires Linux PC on same network):

**On Mini Pupper (Terminal 2):**
```bash
ros2 launch pupper_vision vision.launch.py mode:=person visualization:=true
```

**On Linux PC:**
```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=0  # Match Mini Pupper's domain ID if set
ros2 run rqt_image_view rqt_image_view
```
Then select topic: `/vision/visualization`

This shows the camera feed with bounding boxes and detection overlays.

---

*Created for the Baccus Lab Mini Pupper Vision Workshop*
