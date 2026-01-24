# Tangerine Orchard Inspection Robot - Technical Roadmap
**Team:** Nick, Yannis  
**Project:** Under-canopy fruit color inspection for tangerine orchards

---

## Important Notes

**Robot Update Status:** Your robots are NOT yet updated with the latest packages (tracking, navigation). I will update them while you are on your tour tomorrow. When you return, you'll have access to all the packages described in this roadmap.

**GitHub Repository:** All Mini Pupper ROS 2 packages can be found at:
- Main Repository: https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev
- API/LLM Examples: https://github.com/mangdangroboticsclub/apps-md-robots

**How to Study:** Browse these repositories on GitHub to understand the code structure. Read through the files mentioned in each section below. When you have questions about how things work, **ask me**. Understanding these packages is critical before you start modifying them.

---

## Project Overview - Simplified Scope

Build an orchard inspection robot that:
- Walks along a path past 5 trees in a simulated orchard
- Uses camera to detect fruit color at each tree
- Compares fruit color to expected values (dictionary-based)
- Reports which trees have incorrect fruit color

**Key Advantage:** Under-canopy inspection from ground level. UAVs cannot operate effectively in dense canopy environments. The Mini Pupper's low profile (< 50cm height) allows it to navigate under branches and inspect lower fruit and leaf surfaces that are not visible from above.

**Exhibition Vision:** A miniature orchard setup where the robot autonomously inspects fruit quality along a row of trees.

---

## Simplified Technical Approach

### Core Functionality
1. **Navigation:** Follow a path past 5 tree stations
2. **Detection:** At each station, capture image of fruit
3. **Analysis:** Check fruit color (orange vs wrong color)
4. **Reporting:** Store results in dictionary, generate report

### Example Expected Values
```python
EXPECTED_FRUIT_COLORS = {
    "tree_1": {"color": "orange", "hsv_range": [(10, 100, 100), (25, 255, 255)]},
    "tree_2": {"color": "orange", "hsv_range": [(10, 100, 100), (25, 255, 255)]},
    "tree_3": {"color": "orange", "hsv_range": [(10, 100, 100), (25, 255, 255)]},
    "tree_4": {"color": "orange", "hsv_range": [(10, 100, 100), (25, 255, 255)]},
    "tree_5": {"color": "orange", "hsv_range": [(10, 100, 100), (25, 255, 255)]},
}

# Example report
INSPECTION_RESULTS = {
    "tree_1": "PASS - Orange detected",
    "tree_2": "PASS - Orange detected", 
    "tree_3": "FAIL - Green detected (unripe)",
    "tree_4": "PASS - Orange detected",
    "tree_5": "FAIL - Brown detected (overripe)",
}
```

---

## Why This Scope is Better

**Original concern:** Your project had many complex modules (SLAM, VLM, anomaly detection, complex terrain navigation) which is ambitious for 2 people in limited time.

**New simplified approach:**
- **No SLAM needed** - Pre-defined path between stations
- **No complex ML** - Simple color detection using OpenCV
- **No rough terrain** - Focus on flat/gentle terrain first
- **Dictionary-based** - Known expected values, simple comparison

**Result:** Achievable, demonstrable, technically sound project that proves the concept.

---

## Available Sensors & Approach

### Sensor Options (Pick ONE to start)

#### Option 1: RGB Camera Only (RECOMMENDED - Simplest)
**What you have:** Raspberry Pi camera  
**Best for:** Color detection, fruit identification  
**Difficulty:** EASIEST  
**Why recommended:** Sufficient for color-based inspection

#### Option 2: OAK-D (RGB + Depth)
**What you have:** RGB + depth camera  
**Best for:** Better fruit detection, distance measurement  
**Difficulty:** MEDIUM  
**When to use:** If RGB struggles with lighting or you want to measure fruit size

#### Option 3: 2D LiDAR + RGB
**What you have:** LiDAR for navigation + RGB for detection  
**Best for:** Reliable navigation + visual inspection  
**Difficulty:** HARDER (two sensors to integrate)  
**When to use:** If navigation proves challenging

**Recommendation:** Start with **Option 1 (RGB only)**. Add depth or LiDAR only if needed.

---

## Existing Package Resources

### Packages You'll Use Directly

#### 1. **mini_pupper_navigation** (Path Following)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_navigation  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/mini_pupper_navigation/`

**What it provides:**
- Nav2 stack for path following
- Waypoint navigation
- Obstacle avoidance (if using LiDAR)

**Your tasks:**
1. **Study the code** - How does waypoint navigation work?
2. **Run vanilla version** - Test navigation
3. **Understand waypoints** - How to define path between trees?
4. **Your touch** - Create simple 5-station path
5. **This may be a reach** - Add obstacle avoidance for rough terrain

**When to use:**
- If you need autonomous path following
- If terrain requires SLAM/mapping

**When NOT to use:**
- If you can teleoperate between stations (simpler)
- If path is straight and clear

---

#### 2. **mini_pupper_tracking** (Visual Detection Framework)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_tracking  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/mini_pupper_tracking/`

**What it provides:**
- Camera image processing
- YOLO detection framework (you won't use YOLO, but framework is useful)
- Image preprocessing utilities

**Your tasks:**
1. **Study the code** - How does camera processing work?
2. **Run vanilla version** - See image pipeline
3. **Understand image topics** - Where do camera images come from?
4. **Your touch** - Replace YOLO with color detection
5. **This may be a reach** - Add fruit counting, size estimation

**Key files to examine:**
```
mini_pupper_tracking/
├── mini_pupper_tracking/
│   ├── tracking_node.py         # Framework reference
│   └── camera_processor.py      # Image preprocessing
└── launch/
    └── tracking.launch.py
```

---

#### 3. **mini_pupper_bringup** (Hardware Control)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_bringup  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/mini_pupper_bringup/`

**What it provides:**
- Camera initialization
- Hardware control
- Basic movement

**Your tasks:**
1. **Study the code** - How to launch camera?
2. **Run vanilla version** - `ros2 launch mini_pupper_bringup bringup.launch.py`
3. **Understand topics** - Camera feed location

---

#### 4. **stanford_controller** (Motion Control)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/stanford_controller  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/stanford_controller/`

**What it provides:**
- Basic walking gaits
- Movement commands
- Velocity control

**Your tasks:**
1. **Study the code** - How does walking work?
2. **Run vanilla version** - Test walking on flat ground
3. **Test terrain** - Try on slight slopes (2-4cm steps)
4. **Your touch** - Slow, stable gait for inspection

**Note on terrain:** I'm working on an improved walking algorithm for rough terrain. The current gait should work for flat/gentle terrain and 2-4cm steps. Avoid 10-30cm drops for now - focus on achievable terrain.

---

## Phase-by-Phase Implementation Roadmap

### Phase 1: Color Detection System
**Goal:** Detect fruit color from camera images

**Why start here:** This is your core functionality. Prove color detection works before adding navigation complexity.

**Packages to use:**
- `mini_pupper_bringup` - Camera access
- OpenCV for color detection

**Tasks:**

**Step 1: Setup Color Detection**
1. Create fruit color detector:
```python
import cv2
import numpy as np
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

class FruitColorDetector:
    def __init__(self):
        self.bridge = CvBridge()
        
        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10)
        
        # Define color ranges in HSV
        self.color_ranges = {
            "orange": {
                "lower": np.array([10, 100, 100]),  # H, S, V
                "upper": np.array([25, 255, 255])
            },
            "green": {  # Unripe fruit
                "lower": np.array([35, 40, 40]),
                "upper": np.array([85, 255, 255])
            },
            "brown": {  # Overripe fruit
                "lower": np.array([10, 50, 20]),
                "upper": np.array([20, 255, 200])
            }
        }
    
    def image_callback(self, msg):
        # Convert ROS image to OpenCV
        cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        
        # Detect fruit color
        detected_color = self.detect_fruit_color(cv_image)
        
        print(f"Detected color: {detected_color}")
    
    def detect_fruit_color(self, image):
        # Convert to HSV color space
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Check each color
        color_scores = {}
        for color_name, color_range in self.color_ranges.items():
            # Create mask for this color
            mask = cv2.inRange(hsv, color_range["lower"], 
                              color_range["upper"])
            
            # Count pixels of this color
            pixel_count = cv2.countNonZero(mask)
            color_scores[color_name] = pixel_count
        
        # Return color with most pixels
        if max(color_scores.values()) > 1000:  # Threshold
            return max(color_scores, key=color_scores.get)
        else:
            return "no_fruit_detected"
    
    def get_expected_color(self, tree_id):
        # From your dictionary
        expected = EXPECTED_FRUIT_COLORS.get(tree_id, {})
        return expected.get("color", "unknown")
    
    def check_fruit_quality(self, tree_id, detected_color):
        expected = self.get_expected_color(tree_id)
        
        if detected_color == expected:
            return "PASS"
        else:
            return f"FAIL - Expected {expected}, got {detected_color}"
```

**Step 2: Test Color Detection**
1. Take test photos of orange objects (tangerines, balls, etc.)
2. Test detection with different lighting:
   - Direct sunlight
   - Shadow
   - Indirect light
3. Tune HSV ranges for reliable detection
4. Test with "wrong" colors (green, brown objects)

**Step 3: Build Inspection Station**
1. Create one test station with:
   - "Tree" (post or stand)
   - Attached fruit (real tangerine or colored ball)
   - Camera position marker
2. Robot approaches station
3. Robot stops at marker
4. Robot captures image
5. Robot analyzes color
6. Robot logs result

**Deliverable:** Reliable fruit color detection at single station

**Success criteria:**
- Correctly identifies orange fruit >90% of time
- Correctly identifies wrong colors (green, brown)
- Works in exhibition lighting
- Results logged to dictionary

---

### Phase 2: Multi-Station Path Navigation
**Goal:** Visit 5 tree stations sequentially

**Packages to use:**
- `stanford_controller` - Movement
- Optional: `mini_pupper_navigation` - Waypoints

**Tasks:**

**Step 1: Define Path Layout**
1. Create physical layout:
```
Start → Tree 1 (1m) → Tree 2 (1m) → Tree 3 (1m) → Tree 4 (1m) → Tree 5 → End
[Total path: ~4-5 meters]
```

2. Mark stations clearly:
   - Tape on ground for stop positions
   - Or: Use colored markers for visual positioning
   - Or: Use waypoints if using Nav2

**Step 2: Implement Simple Path Following**

**Option A: Teleoperation (Simplest)**
```python
# Manual control between stations
# At each station, trigger inspection
# Good for initial testing
```

**Option B: Timed Movement (Simple)**
```python
class SimplePathFollower:
    def __init__(self):
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.stations = [
            {"id": "tree_1", "distance": 1.0},
            {"id": "tree_2", "distance": 1.0},
            {"id": "tree_3", "distance": 1.0},
            {"id": "tree_4", "distance": 1.0},
            {"id": "tree_5", "distance": 1.0},
        ]
        self.current_station = 0
    
    def move_to_next_station(self):
        if self.current_station >= len(self.stations):
            return False  # Done
        
        station = self.stations[self.current_station]
        distance = station["distance"]
        
        # Move forward at slow speed
        # Approximate: 0.2 m/s for distance/0.2 seconds
        duration = distance / 0.2
        
        self.move_forward(duration)
        self.stop()
        
        # Perform inspection
        self.inspect_tree(station["id"])
        
        self.current_station += 1
        return True
    
    def move_forward(self, duration):
        cmd = Twist()
        cmd.linear.x = 0.2  # Slow speed
        
        start_time = self.get_clock().now()
        while (self.get_clock().now() - start_time).nanoseconds / 1e9 < duration:
            self.cmd_vel_pub.publish(cmd)
            time.sleep(0.1)
    
    def stop(self):
        cmd = Twist()  # All zeros
        self.cmd_vel_pub.publish(cmd)
```

**Option C: Nav2 Waypoints (More Complex)**
```python
# If you need precise positioning or obstacles
# Use mini_pupper_navigation package
# Define waypoints for each tree
waypoints = [
    {"x": 1.0, "y": 0.0},  # Tree 1
    {"x": 2.0, "y": 0.0},  # Tree 2
    {"x": 3.0, "y": 0.0},  # Tree 3
    {"x": 4.0, "y": 0.0},  # Tree 4
    {"x": 5.0, "y": 0.0},  # Tree 5
]
```

**Recommendation:** Start with **Option B (timed movement)**. It's simple and reliable for straight paths. Use Nav2 only if needed.

**Step 3: Integration**
1. Combine path following + inspection
2. At each station:
   - Stop
   - Capture image
   - Analyze color
   - Log result
   - Move to next station
3. At end: Generate report

**Deliverable:** Robot inspects all 5 stations autonomously

**Success criteria:**
- Visits all 5 stations in sequence
- Performs inspection at each station
- Completes full path without manual intervention
- Generates complete inspection report

---

### Phase 3: Reporting System
**Goal:** Generate inspection report with results

**Tasks:**

**Step 1: Create Data Logger**
```python
class OrchardInspector:
    def __init__(self):
        self.inspection_results = {}
        self.expected_colors = EXPECTED_FRUIT_COLORS
        
        self.detector = FruitColorDetector()
        self.path_follower = SimplePathFollower()
    
    def inspect_tree(self, tree_id):
        # Capture and analyze
        detected_color = self.detector.detect_fruit_color_sync()
        expected_color = self.expected_colors[tree_id]["color"]
        
        # Check result
        if detected_color == expected_color:
            result = "PASS"
            message = f"Correct color detected: {detected_color}"
        else:
            result = "FAIL"
            message = f"Wrong color - Expected: {expected_color}, Got: {detected_color}"
        
        # Log result
        self.inspection_results[tree_id] = {
            "result": result,
            "detected": detected_color,
            "expected": expected_color,
            "message": message,
            "timestamp": self.get_clock().now()
        }
        
        print(f"{tree_id}: {message}")
    
    def generate_report(self):
        print("\n=== ORCHARD INSPECTION REPORT ===")
        
        total_trees = len(self.inspection_results)
        passed = sum(1 for r in self.inspection_results.values() 
                    if r["result"] == "PASS")
        failed = total_trees - passed
        
        print(f"Total trees inspected: {total_trees}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Pass rate: {passed/total_trees*100:.1f}%\n")
        
        print("Detailed Results:")
        for tree_id, result in self.inspection_results.items():
            status = "✓" if result["result"] == "PASS" else "✗"
            print(f"{status} {tree_id}: {result['message']}")
        
        # Save to file
        self.save_report_to_file()
    
    def save_report_to_file(self):
        with open('inspection_report.txt', 'w') as f:
            f.write("ORCHARD INSPECTION REPORT\n")
            f.write("=" * 40 + "\n\n")
            
            for tree_id, result in self.inspection_results.items():
                f.write(f"{tree_id}:\n")
                f.write(f"  Result: {result['result']}\n")
                f.write(f"  Expected: {result['expected']}\n")
                f.write(f"  Detected: {result['detected']}\n")
                f.write(f"  Message: {result['message']}\n\n")
```

**Step 2: Add Visualization**
```python
def generate_report_with_images(self):
    # Save images from each station
    # Overlay detection results on images
    # Create summary image/PDF
    pass
```

**Deliverable:** Complete inspection report

**Success criteria:**
- Report lists all 5 trees
- Shows pass/fail for each
- Indicates expected vs detected colors
- Saved to file for download/display

---

### Phase 4: Exhibition Display (Optional Enhancement)
**Goal:** Make demonstration engaging and clear

**Tasks:**

**Step 1: Build Orchard Display**
1. Physical setup:
   - 5 "trees" (posts, stands, or mini trees)
   - Attached fruit at each tree:
     - Trees 1, 2, 4: Orange (correct)
     - Tree 3: Green (unripe - wrong)
     - Tree 5: Brown (overripe - wrong)
   - Clear path between trees
   - Starting and ending markers

2. Visual elements:
   - Orchard signage
   - Tree labels (Tree 1, Tree 2, etc.)
   - Under-canopy aesthetic (leaves, branches above)

**Step 2: Demo Visualization**
1. Screen showing:
   - Current camera view
   - Detected color overlay
   - Current station
   - Running results

2. Physical indicators:
   - LED or light for PASS/FAIL
   - Sound beeps at each station

**Step 3: Narration Materials**
1. Poster explaining:
   - Why ground-based inspection?
   - What problems does this solve?
   - How does color detection work?

2. Demo script:
   - "Watch as robot inspects 5 tangerine trees"
   - "It checks if fruit is the correct orange color"
   - "Trees 3 and 5 have defective fruit - watch it detect them!"

---

## Implementation Strategy

### Work Division (2 people)

**Person 1: Detection & Analysis**
- Phase 1: Color detection system
- Color range tuning
- Dictionary management
- Reporting system

**Person 2: Navigation & Integration**
- Phase 2: Path following
- Station positioning
- Integration with detection
- Exhibition display

**Shared:**
- Testing together
- Demo preparation
- Documentation

### Priority Order

1. **Phase 1 (Detection)** - Core functionality, must work perfectly
2. **Phase 2 (Navigation)** - Start simple (teleop or timed), enhance if time
3. **Phase 3 (Reporting)** - Quick to implement once 1 & 2 work
4. **Phase 4 (Display)** - Polish for exhibition

---

## Terrain Considerations

### What Terrain to Use

**For Exhibition Demo:**
- **Flat/gentle terrain** - Focus on proving the concept
- **2-4cm steps maximum** - Within robot's capability
- **Avoid:**
  - 10-30cm drops (robot may get stuck)
  - Muddy surfaces (high risk)
  - Steep slopes >15 degrees (wait for new walking algorithm)

**Why this scope:**
- Current gait should handle flat/gentle terrain
- Reduces risk of robot failure during demo
- Still proves the under-canopy inspection concept
- Can discuss rough terrain as "future work"

### Note on Walking Algorithm

I'm working on an improved walking algorithm for rough terrain. Current status:
- **Current gait:** Good for flat terrain, 2-4cm steps
- **New algorithm:** Will handle steeper slopes, larger steps
- **Timeline:** May be available before exhibition
- **Your approach:** Build demo assuming flat terrain, can upgrade later if new algorithm is ready

---

## Code Organization

### Recommended Package Structure

Create your package: `orchard_inspector`

```
orchard_inspector/
├── orchard_inspector/
│   ├── __init__.py
│   ├── fruit_color_detector.py    # Phase 1: Color detection
│   ├── path_follower.py            # Phase 2: Navigation
│   ├── inspection_manager.py       # Phase 3: Orchestration
│   └── report_generator.py         # Phase 3: Reporting
├── config/
│   ├── expected_colors.yaml        # Expected fruit colors
│   ├── color_ranges.yaml           # HSV color definitions
│   └── path_waypoints.yaml         # Station positions
├── launch/
│   ├── inspector.launch.py         # Main launcher
│   └── test_detection.launch.py    # Testing
├── test/
│   ├── test_color_detection.py
│   └── test_path_following.py
├── data/
│   └── test_images/                # Sample fruit images
├── package.xml
└── setup.py
```

---

## Key Learning Resources

### Documentation to Read
1. **OpenCV Color Detection:**
   - https://docs.opencv.org/
   - HSV color space tutorial
   - Color thresholding

2. **ROS 2 Basics:**
   - https://docs.ros.org/en/humble/Tutorials.html
   - Image messages
   - cv_bridge

3. **Mini Pupper Packages:**
   - Navigation: https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_navigation
   - Tracking framework: https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_tracking

### Code to Study First
```bash
# Camera and image processing
~/ros2_ws/src/mini_pupper_ros/mini_pupper_tracking/

# Navigation (if using Nav2)
~/ros2_ws/src/mini_pupper_ros/mini_pupper_navigation/

# Hardware control
~/ros2_ws/src/mini_pupper_ros/mini_pupper_bringup/
```

---

## Testing Strategy

### Unit Tests

**Color detection:**
```bash
# Test with static images
python test_color_detector.py orange_fruit.jpg
python test_color_detector.py green_fruit.jpg

# Test with live camera
ros2 run orchard_inspector fruit_color_detector
# Hold colored objects in front of camera
```

**Path following:**
```bash
# Test movement between two points
# Measure actual distance traveled
# Tune speed and duration
```

### Integration Tests

**Full inspection run:**
1. Place robot at start
2. Launch full system
3. Robot visits all 5 stations
4. Robot performs inspections
5. Report generated
6. Verify results match expectations

### Performance Metrics

- **Detection accuracy:** >90% correct color identification
- **Path completion:** 100% of stations visited
- **Report accuracy:** All results correctly recorded
- **Time per inspection:** <30 seconds per tree
- **Total demo time:** <5 minutes for 5 trees

---

## Success Criteria by Phase

### Phase 1 (Color Detection) - MINIMUM VIABLE DEMO
Orange fruit correctly detected
Green fruit (unripe) correctly detected
Brown fruit (overripe) correctly detected
Detection works in exhibition lighting
Results compared against dictionary

### Phase 2 (Path Navigation)
Robot visits all 5 stations
Stops at each station
Maintains straight path
Completes without manual intervention

### Phase 3 (Reporting)
Results logged for all stations
Report generated with pass/fail
Report saved to file
Summary statistics calculated

### Exhibition Demo (COMPLETE)
Robot inspects 5 trees autonomously
Correctly identifies problem trees
Generates complete report
Display looks professional (orchard theme)
Demo runs reliably (3+ successful runs)
Team can explain technical approach
