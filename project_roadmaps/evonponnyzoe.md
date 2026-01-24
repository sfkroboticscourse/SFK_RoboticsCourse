# Forest Trail Hazard Detection - Technical Roadmap
**Team:** Zoe, Ponny, Evon  
**Project:** Autonomous hazard detection system for edges, pits, and water hazards using Mini Pupper 2

---

## Important Notes

**Robot Update Status:** Your robots are NOT yet updated with the latest packages (tracking, navigation). I will update them while you are on your tour tomorrow. When you return, you'll have access to all the packages described in this roadmap.

**GitHub Repository:** All Mini Pupper ROS 2 packages can be found at:
- Main Repository: https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev
- API/LLM Examples: https://github.com/mangdangroboticsclub/apps-md-robots

**How to Study:** Browse these repositories on GitHub to understand the code structure. Read through the files mentioned in each section below. When you have questions about how things work, **ask me**. Understanding these packages is critical before you start modifying them.

---

## Project Overview

Build a hazard detection system where the Mini Pupper 2 autonomously navigates a forest/hiking trail display and detects hazards (edges/cliffs, pits, water). This project has **excellent hardware-to-application fit** since the MP2 already has the sensors you need: 2D LiDAR, RGB camera, and potentially a depth camera (OAK-D).

**Exhibition Vision:** A miniature forest/trail environment where the robot demonstrates autonomous hazard avoidance. This will be visually engaging and technically impressive.

---

## Available Sensors & Their Strengths

### 1. 2D LiDAR (LDLiDAR)
**What you have:** `/scan` topic with distance measurements  
**Best for:** Edge/cliff detection (sudden distance spikes)  
**Difficulty:** EASIEST - Most reliable sensor for this task  
**GitHub Example:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_navigation

### 2. RGB Camera (Raspberry Pi Camera)
**What you have:** Camera images via ROS topics  
**Best for:** Visual hazard classification (water, texture changes)  
**Difficulty:** MEDIUM - Requires computer vision or neural networks  
**GitHub Example:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_tracking

### 3. Depth Camera (OAK-D - if available)
**What you have:** Depth maps showing distance to surfaces  
**Best for:** Ground plane monitoring, pit detection  
**Difficulty:** MEDIUM - Good option if RGB proves challenging  
**Fallback if unavailable:** Use neural network for depth estimation from RGB

---

## Recommended Track Priorities (Revised)

### Priority 1: Track A - 2D LiDAR (START HERE)
**Why first:** Simplest, most reliable, gets you a working demo quickly

### Priority 2: Track B - RGB Camera + Neural Network
**Why second:** More impressive for exhibition, works alongside LiDAR

### Priority 3: Track C - Depth Camera (If Available)
**Why third:** Backup if RGB neural network is challenging

### Priority 4: Track D - Sensor Fusion
**Why last:** Combines successful tracks for robustness

---

## Existing Package Resources

### Packages You'll Use Directly

#### 1. **mini_pupper_navigation** (LiDAR Navigation)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_navigation  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/mini_pupper_navigation/`

**What it provides:**
- LiDAR integration (`/scan` topic)
- Nav2 stack (path planning, obstacle avoidance)
- SLAM Toolbox integration

**Your tasks:**
1. **Study the code** - How does it process LiDAR data?
2. **Run vanilla version** - Test SLAM and navigation
3. **Understand /scan topic** - What data does LiDAR publish?
4. **Your touch** - Create edge detection from scan data
5. **This may be a reach** - Classify hazard types from scan patterns

**Key files to examine:**
```
mini_pupper_navigation/
├── launch/
│   ├── slam.launch.py           # SLAM with LiDAR
│   └── navigation.launch.py     # Nav2 integration
├── config/
│   ├── slam_params.yaml         # SLAM configuration
│   └── nav2_params.yaml         # Navigation parameters
└── rviz/
    └── navigation.rviz          # Visualization
```

**Learning goals:**
- How does `/scan` topic work?
- What are LaserScan messages?
- How to detect distance discontinuities?

---

#### 2. **mini_pupper_tracking** (Camera & Neural Networks)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_tracking  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/mini_pupper_tracking/`

**What it provides:**
- YOLO11n neural network integration
- Camera image processing
- Object detection framework
- ONNX model loading

**Your tasks:**
1. **Study the code** - How does YOLO detection work?
2. **Run vanilla version** - Test person detection
3. **Understand model structure** - How to swap YOLO for different models?
4. **Your touch** - Replace person detection with hazard detection
5. **This may be a reach** - Multi-class hazard detection (water, edge, pit, safe)

**Key files to examine:**
```
mini_pupper_tracking/
├── mini_pupper_tracking/
│   ├── tracking_node.py         # Main detection node
│   ├── yolo_detector.py         # YOLO wrapper
│   └── camera_processor.py      # Image preprocessing
├── models/
│   └── yolov11n.onnx           # Pre-trained model
└── launch/
    └── tracking.launch.py       # Detection launcher
```

**Learning goals:**
- How to use ONNX models in ROS 2?
- How to preprocess camera images?
- How to replace detection models?

---

#### 3. **mini_pupper_bringup** (Hardware Control)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_bringup  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/mini_pupper_bringup/`

**What it provides:**
- Hardware initialization
- Motor control
- Sensor integration

**Your tasks:**
1. **Study the code** - How are sensors initialized?
2. **Run vanilla version** - `ros2 launch mini_pupper_bringup bringup.launch.py`
3. **Understand sensor topics** - Where does camera/LiDAR data come from?
4. **Your touch** - Create custom launch for hazard detection mode
5. **This may be a reach** - Add emergency stop behavior on hazard detection

---

#### 4. **stanford_controller** (Motion Control)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/stanford_controller  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/stanford_controller/`

**What it provides:**
- Quadruped gait control
- Velocity command processing
- Movement primitives

**Your tasks:**
1. **Study the code** - How does motion control work?
2. **Run vanilla version** - Test with teleop
3. **Understand cmd_vel** - How to stop the robot?
4. **Your touch** - Implement emergency stop on hazard
5. **This may be a reach** - Slow approach to edges, cautious gait

---

### Packages for Reference

#### 5. **mini_pupper_interfaces** (Custom Messages)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_interfaces  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/mini_pupper_interfaces/`

**Your tasks:**
1. **Study** - Look at message definitions
2. **Your touch** - Create custom hazard messages:
   - `HazardDetection.msg` - Hazard type, confidence, location
   - `SafetyStatus.msg` - Current safety state
   - `EdgeDistance.msg` - Distance to nearest edge

---

## Phase-by-Phase Implementation Roadmap

### Phase 1: Track A - LiDAR Edge Detection
**Goal:** Detect edges/cliffs using sudden LiDAR distance changes

**Technical Approach:**
LiDAR measures distance to obstacles. When approaching an edge, the LiDAR beam shoots past the edge and hits the floor far below, creating a sudden distance spike.

**Packages to use:**
- `mini_pupper_navigation` - LiDAR access
- `mini_pupper_bringup` - Hardware
- `stanford_controller` - Motion control

**Tasks:**

**Step 1: Understanding LiDAR**
1. Study the `/scan` topic:
```bash
# After bringup, examine LiDAR data
ros2 topic echo /scan

# Visualize in RViz
rviz2
# Add LaserScan display, topic: /scan
```

2. Understand LaserScan message structure:
```python
# LaserScan contains:
# - ranges: array of distance measurements
# - angle_min, angle_max: scan range
# - angle_increment: step between measurements
```

3. Examine existing navigation code:
```bash
# On GitHub, look at:
mini_pupper_navigation/config/nav2_params.yaml
# See how Nav2 uses obstacle detection
```

**Step 2: Edge Detection Implementation**
1. Create edge detector node:
```python
class EdgeDetectorLidar:
    def __init__(self):
        self.scan_sub = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
    def scan_callback(self, scan):
        # Get front-facing ranges (e.g., -30° to +30°)
        front_ranges = self.get_front_ranges(scan)
        
        # Check for edge: sudden distance increase
        if self.detect_edge(front_ranges):
            self.emergency_stop()
    
    def detect_edge(self, ranges):
        # Edge detected if distance > threshold
        # Example: normal floor ~0.3m, edge >2.0m
        edge_threshold = 2.0  # meters
        for distance in ranges:
            if distance > edge_threshold:
                return True
        return False
    
    def emergency_stop(self):
        # Publish zero velocity
        stop_msg = Twist()  # All zeros
        self.cmd_vel_pub.publish(stop_msg)
        print("EDGE DETECTED - EMERGENCY STOP")
```

2. Test on your trail display:
   - Robot approaches edge
   - LiDAR detects distance spike
   - Robot stops before falling

3. Tune parameters:
   - Edge threshold distance
   - Front-facing angle range
   - Stopping distance margin

**Deliverable:** Robot reliably stops at edges using LiDAR

**Success criteria:**
- Detects edges from 0.5m away
- No false positives on flat terrain
- Stops within 10cm of edge

---

### Phase 2: Track B - RGB Hazard Detection with Neural Network
**Goal:** Detect hazards (water, edges, pits) from camera images

**Technical Approach:**
Use computer vision to classify terrain ahead. Start with existing neural network frameworks, then adapt or train for hazards.

**Packages to use:**
- `mini_pupper_tracking` - Neural network framework
- Camera topics from `mini_pupper_bringup`

**Neural Network Options (in order of difficulty):**

**Option B1: Pre-trained Segmentation Network (EASIEST)**
Use existing models trained for terrain/path detection:
- **DeepLabV3** - Scene segmentation
- **MobileNet-SSD** - Object detection adapted for terrain
- Look for pre-trained models on: PyTorch Hub, TensorFlow Hub, ONNX Model Zoo

**Option B2: Depth Estimation Network (IF NO DEPTH CAMERA)**
If depth camera unavailable, use monocular depth estimation:
- **MiDaS** - Monocular depth estimation (converts RGB → depth map)
- **DPT (Dense Prediction Transformer)** - State-of-the-art depth from RGB
- Download ONNX versions for easy integration

**Option B3: Custom Classifier (This may be a reach)**
Train a simple hazard classifier on your specific trail:
- Collect labeled images: water, edge, safe, pit
- Fine-tune MobileNet or EfficientNet
- Export to ONNX for deployment

**Tasks:**

**Step 1: Model Selection & Setup**
1. Study `mini_pupper_tracking` structure:
```bash
# Look at how YOLO model is loaded
mini_pupper_tracking/mini_pupper_tracking/yolo_detector.py

# Understand ONNX runtime usage
# See how images are preprocessed
```

2. Download a pre-trained model:
```bash
# Example: MiDaS for depth estimation
wget https://github.com/isl-org/MiDaS/releases/download/v3_1/midas_v21_small_256.onnx

# Or search ONNX Model Zoo for terrain segmentation
```

3. Test model inference standalone:
```python
import onnxruntime as ort
import cv2
import numpy as np

# Load model
session = ort.InferenceSession("model.onnx")

# Load test image
image = cv2.imread("trail.jpg")
preprocessed = preprocess_image(image)

# Run inference
outputs = session.run(None, {"input": preprocessed})

# Visualize results
show_results(outputs)
```

**Step 2: ROS Integration**
1. Adapt tracking node for hazard detection:
```python
class HazardDetectorRGB:
    def __init__(self):
        # Based on mini_pupper_tracking structure
        self.model = ort.InferenceSession("hazard_model.onnx")
        
        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10)
        
        self.hazard_pub = self.create_publisher(
            HazardDetection, '/hazards', 10)
    
    def image_callback(self, msg):
        # Convert ROS Image to CV2
        cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        
        # Preprocess
        input_tensor = self.preprocess(cv_image)
        
        # Inference
        outputs = self.model.run(None, {"input": input_tensor})
        
        # Post-process
        hazard_type = self.classify_hazard(outputs)
        
        # Publish results
        self.publish_hazard(hazard_type)
```

2. Create hazard classification logic:
```python
def classify_hazard(self, model_output):
    # Example for segmentation model:
    # - Check if ground disappears (edge)
    # - Check for water-like texture/color
    # - Check for depth discontinuities
    
    if is_edge(model_output):
        return "edge"
    elif is_water(model_output):
        return "water"
    elif is_pit(model_output):
        return "pit"
    else:
        return "safe"
```

**Step 3: Integration & Testing**
1. Combine with motion control
2. Test on different hazards in display
3. Tune detection thresholds
4. Add visualization (bounding boxes, hazard labels)

**Deliverable:** Robot detects and classifies hazards from RGB camera

**Success criteria:**
- Detects 3 hazard types: edge, water, safe
- >80% accuracy on your test trail
- Runs in real-time (>10 FPS)

**These may be a reach:**
- Multi-class detection (water AND edge simultaneously)
- Confidence scores for each detection
- Hazard avoidance path planning

---

### Phase 3: Track C - Depth Camera (If Available) OR Depth Estimation Network
**Goal:** Use depth information for pit and edge detection

**Option C1: If you have OAK-D depth camera**

**Tasks:**
1. Study OAK-D integration examples:
```bash
# Look for depthai ROS 2 packages
sudo apt-get install ros-humble-depthai-ros
```

2. Subscribe to depth topics:
```python
class EdgeDetectorDepth:
    def __init__(self):
        self.depth_sub = self.create_subscription(
            Image, '/oakd/depth', self.depth_callback, 10)
    
    def depth_callback(self, msg):
        # Convert depth image
        depth_image = self.bridge.imgmsg_to_cv2(msg, "32FC1")
        
        # Check ground plane region
        ground_region = depth_image[240:480, 320:640]  # Bottom-center
        
        # Detect if ground disappears
        if self.ground_missing(ground_region):
            self.emergency_stop()
    
    def ground_missing(self, region):
        # Check for NaN values or sudden depth increase
        mean_depth = np.nanmean(region)
        return mean_depth > 3.0 or np.isnan(mean_depth)
```

**Option C2: If NO depth camera - Use MiDaS network**

Use RGB→Depth neural network (covered in Track B, Option B2)

**Deliverable:** Depth-based hazard detection working

---

### Phase 4: Track D - Sensor Fusion
**Goal:** Combine multiple sensors for robust detection

**Technical Approach:**
Use voting or weighted combination of sensors.

**Tasks:**
1. Create fusion node:
```python
class HazardFusion:
    def __init__(self):
        # Subscribe to all hazard sources
        self.lidar_sub = self.create_subscription(
            HazardDetection, '/hazards/lidar', self.lidar_callback, 10)
        self.rgb_sub = self.create_subscription(
            HazardDetection, '/hazards/rgb', self.rgb_callback, 10)
        
        self.fused_pub = self.create_publisher(
            HazardDetection, '/hazards/fused', 10)
    
    def fuse_detections(self):
        # Voting: if 2+ sensors agree, that's a hazard
        if (self.lidar_hazard and self.rgb_hazard):
            return True
        
        # Or: weighted confidence
        confidence = (
            0.7 * self.lidar_confidence + 
            0.3 * self.rgb_confidence
        )
        return confidence > 0.8
```

2. Implement emergency stop logic:
```python
# Stop if ANY sensor detects hazard (conservative)
# Or require multiple confirmations (less sensitive)
```

**Deliverable:** Multi-sensor hazard detection system

**AMBITIOUS addition:**
- Sensor health monitoring (detect if LiDAR fails)
- Adaptive fusion weights based on environment
- Hazard location triangulation

---

## Exhibition Display Recommendations

### Physical Setup
**Parallel to coding:** Someone should build the display while others code

**Suggested elements:**
1. **Trail platform** - Elevated board (1-2m long, 0.5m wide)
2. **Edge hazard** - Sharp drop-off at end of trail
3. **Water hazard** - Blue surface/material (foam, paper, fabric)
4. **Pit hazard** - Hole or depression in path
5. **Safe zones** - Clear walking path between hazards
6. **Forest aesthetics** - Small trees, rocks, moss (visual appeal)

**Safety considerations:**
- Edge should have net/barrier to catch robot
- Elevated platform needs stable support
- Robot should be tethered initially

### Demo Flow
1. **Start position** - Robot at beginning of trail
2. **Autonomous walk** - Robot moves forward slowly
3. **Hazard encounter** - Robot approaches edge/water/pit
4. **Detection** - Robot stops, announces hazard
5. **Visualization** - Display shows sensor data (RViz or custom GUI)
6. **Recovery** - Robot backs up or rotates away
7. **Continue** - Resume navigation to next section

**Exhibition enhancements:**
- Screen showing robot's "view" (camera + detections)
- Hazard labels lighting up when detected
- Audio announcements ("Water hazard detected")

---

## Implementation Strategy

### Parallel Work Streams

**Code Team:**
- **Phase 1 (Track A - LiDAR):** Study LiDAR packages, implement edge detection, test on simple edge
- **Phase 2 (Track B - RGB):** Research neural network options, download/test pre-trained models, integrate into ROS node, test hazard classification  
- **Phase 3 (Track C - Depth, if needed):** Implement depth-based detection OR continue improving RGB detection
- **Phase 4 (Track D - Fusion):** Sensor fusion (if multiple sensors work), bug fixes, performance tuning, add visualizations

**Display Team:**
- **Early:** Build basic trail platform, create one edge hazard, test robot positioning
- **Middle:** Add water hazard, add pit hazard, add forest aesthetics, test lighting for camera
- **Late:** Polish display appearance, add signage/labels, test demo flow, practice demo presentation, prepare backup plan

**Key Principle:** Work in parallel. Someone builds the display while others code. Test incrementally on simple setups before the full display is ready.

---

## Code Organization

### Recommended Package Structure

Create your package: `forest_trail_hazard`

```
forest_trail_hazard/
├── forest_trail_hazard/
│   ├── __init__.py
│   ├── edge_detector_lidar.py     # Track A
│   ├── hazard_detector_rgb.py     # Track B
│   ├── hazard_detector_depth.py   # Track C
│   ├── hazard_fusion.py           # Track D
│   └── safety_controller.py       # Emergency stop logic
├── models/
│   ├── hazard_classifier.onnx     # Neural network model
│   └── midas_depth.onnx           # Depth estimation model
├── launch/
│   ├── hazard_detection.launch.py # Main launcher
│   └── test_sensors.launch.py     # Testing launcher
├── config/
│   ├── lidar_params.yaml          # LiDAR thresholds
│   ├── camera_params.yaml         # Camera settings
│   └── fusion_params.yaml         # Fusion weights
├── rviz/
│   └── hazard_viz.rviz           # Visualization config
├── test/
│   ├── test_edge_detection.py
│   └── test_hazard_classifier.py
├── package.xml
└── setup.py
```

---

## Key Learning Resources

### Documentation to Read
1. **ROS 2 sensor processing:**
   - https://docs.ros.org/en/humble/Tutorials.html
   - LaserScan messages
   - Image messages
   - cv_bridge

2. **Mini Pupper packages:**
   - Navigation: https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_navigation
   - Tracking: https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_tracking

3. **Computer vision resources:**
   - ONNX Runtime: https://onnxruntime.ai/docs/
   - OpenCV: https://docs.opencv.org/
   - Pre-trained models: https://github.com/onnx/models

### Code to Study First
```bash
# LiDAR processing
~/ros2_ws/src/mini_pupper_ros/mini_pupper_navigation/

# Neural network integration
~/ros2_ws/src/mini_pupper_ros/mini_pupper_tracking/

# Hardware control
~/ros2_ws/src/mini_pupper_ros/mini_pupper_bringup/
```

---

## Neural Network Resources

### Pre-trained Models for Hazard Detection

**Terrain Segmentation:**
- DeepLabV3-MobileNet: https://pytorch.org/hub/pytorch_vision_deeplabv3_resnet101/
- Semantic segmentation models: https://github.com/onnx/models#image_segmentation

**Depth Estimation (RGB→Depth):**
- MiDaS: https://github.com/isl-org/MiDaS
- DPT: https://github.com/isl-org/DPT

**Path Detection:**
- Search "trail segmentation ONNX" or "path detection model"
- Academic datasets: RUGD (off-road), RELLIS-3D (terrain)

**How to convert models to ONNX:**
```python
# PyTorch to ONNX
import torch
model = torch.load("model.pth")
dummy_input = torch.randn(1, 3, 256, 256)
torch.onnx.export(model, dummy_input, "model.onnx")

# TensorFlow to ONNX
# Use tf2onnx converter
```

---

## Testing Strategy

### Unit Tests (Test each component separately)

**LiDAR edge detection:**
```bash
# Record test data
ros2 bag record /scan

# Replay and verify detection
ros2 bag play test_edge.bag
ros2 topic echo /hazards
```

**RGB hazard detection:**
```bash
# Save test images
ros2 run image_view image_saver image:=/camera/image_raw

# Test model offline
python test_model.py test_image.jpg
```

### Integration Tests

**Full system test:**
1. Launch all nodes
2. Robot approaches each hazard type
3. Verify detection and stop behavior
4. Measure detection distance and accuracy

### Performance Metrics

Track these numbers:
- **Detection distance:** How far away does it detect?
- **Detection rate:** % of hazards caught (aim for 95%+)
- **False positive rate:** % of false alarms (aim for <5%)
- **Processing speed:** Frames per second (aim for 10+ FPS)
- **Stop distance:** How close before stopping? (aim for >10cm margin)

---

## Success Criteria by Phase

### Phase 1 (Track A - LiDAR) - MINIMUM VIABLE DEMO
Robot stops at edges using LiDAR
Detection distance: >0.5m
No false positives on flat terrain
Works in 100% of edge tests

### Phase 2 (Track B - RGB)
Camera detects at least 2 hazard types

### Phase 3 (Track C - Depth, optional)
Depth-based detection working
Detects pits that RGB/LiDAR miss
Complements other sensors

### Phase 4 (Track D - Fusion, optional and I do not reccomend becuase of time constraints)
Multi-sensor fusion implemented
Lower false positive rate than single sensor
Handles sensor failures gracefully

### Exhibition Demo (COMPLETE)
Robot navigates trail autonomously
Detects and stops at hazards
Display looks professional
Demo runs reliably (3+ successful runs)
Team can explain how it works

## Backup Plans

### If LiDAR doesn't work well
- Adjust parameters (threshold, angle range)
- Add filtering (ignore outliers)
- Fallback to manual control with hazard warnings

### If RGB neural network is too hard
- Use simpler color-based detection (e.g., blue = water)
- Use edge detection algorithms (Canny, Sobel)
- Skip RGB, focus on LiDAR + depth camera

### If depth camera unavailable
- Use MiDaS depth estimation network from RGB
- Focus on LiDAR + RGB combination
- Build hazards that LiDAR can detect well

### If nothing works perfectly
- Demo with teleoperation + hazard warnings
- Show individual sensor data visualizations
- Explain what you learned and next steps
