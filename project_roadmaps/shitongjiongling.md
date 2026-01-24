# Scoliosis Posture Detection Robot - Technical Roadmap
**Team:** Shitong Zhang, Rachel (Jiongling) Yu  
**Project:** Posture monitoring robot that detects bad sitting habits and provides escalating reminders

---

## Important Notes

**Robot Update Status:** Your robots are NOT yet updated with the latest packages (tracking, navigation). I will update them while you are on your tour tomorrow. When you return, you'll have access to all the packages described in this roadmap.

**GitHub Repository:** All Mini Pupper ROS 2 packages can be found at:
- Main Repository: https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev
- API/LLM Examples: https://github.com/mangdangroboticsclub/apps-md-robots

**How to Study:** Browse these repositories on GitHub to understand the code structure. Read through the files mentioned in each section below. When you have questions about how things work, **ask me**. Understanding these packages is critical before you start modifying them.

---

## Project Overview

Build a posture monitoring robot that:
- Detects bad sitting postures using MediaPipe Pose (33 keypoints)
- Identifies specific harmful positions: leg crossing, slouching/tech neck, C-shaped spine, prolonged sitting
- Provides escalating reminders (3 levels) based on frequency of bad posture
- Nudges user's ankle as physical intervention at highest level

This is an **excellent technical scope** with well-defined detection rules. Your detection logic is solid - now we need to integrate it with Mini Pupper hardware.

---

## Your Detection Rules Summary

You've already defined great detection rules. Here's a quick reference:

| Posture | Key Detection | Duration Threshold |
|---------|--------------|-------------------|
| Leg crossing | LEFT_KNEE.y < RIGHT_HIP.y | 5 seconds |
| Slouching/Tech neck | EAR forward of SHOULDER + neck angle < 160° | 120 seconds |
| C-shaped spine | Shoulder/hip asymmetry + head shift | 30 seconds |
| Prolonged sitting | Low variance in hip/shoulder position | 30 minutes |

**Reminder Levels:**
- Level 1: Soft music, gentle face
- Level 2: Louder music, concerned face
- Level 3: Loud music + attention-grabbing movement, alert face

**Note on ankle nudging:** While the ankle nudge idea is creative, it may not demo well at an exhibition (robot bumping into visitors' feet). Consider these Level 3 alternatives instead:
- **Dramatic attention dance** - Robot does a noticeable movement sequence
- **Verbal call-out** - Robot says user's name or "Hey! Posture check!"
- **Approach + stare** - Robot walks toward user and stares with alert face
- **Stand up and bark** - Robot rises on hind legs briefly

**Level Escalation Rules:**
- Δt ≤ 5 min → Level up
- 5 min < Δt ≤ 20 min → Stay same
- Δt > 20 min → Level down

---

## Answers to Your Questions

### Question 1: How to connect to AI for verbal reminders?
**Answer:** Use the `apps-md-robots` repository for LLM integration patterns. You can:
```python
# Option A: Pre-generate reminders (recommended for demo)
reminders = [
    "Hey, I noticed you're slouching a bit!",
    "Time to sit up straight!",
    "Your posture could use some love!",
]

# Option B: Live LLM generation (slower, needs API)
def get_ai_reminder(posture_type):
    prompt = f"Generate a friendly 10-word reminder about {posture_type}"
    return llm_api.query(prompt)
```
**Recommendation:** Pre-generate 10-20 reminders per posture type. LLM generation adds latency (2-5 seconds) which may feel slow.

### Question 2: Can MediaPipe detect multiple people?
**Answer:** Yes! MediaPipe Pose can detect multiple people, but with caveats:
- **Holistic mode:** Single person only (more accurate)
- **Pose detection:** Can detect multiple people with lower accuracy
- **For classroom scenario:** You'd need to track individuals and navigate between them

---

## Existing Package Resources

### Packages You'll Use Directly

#### 1. **mini_pupper_tracking** (Detection Framework)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_tracking  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/mini_pupper_tracking/`

**What it does:**
- Camera-based detection using neural networks
- Publishes detection information to ROS topics
- Framework for processing camera images

**Your tasks:**
1. **Study the code** - Look at how detection pipeline works
2. **Run vanilla version** - Test the camera feed
3. **Understand topics** - What ROS topics does it publish?
4. **Your touch** - Replace YOLO person detection with MediaPipe Pose

**Key files to examine:**
```
mini_pupper_tracking/
├── mini_pupper_tracking/
│   ├── tracking_node.py        # Main detection logic
│   └── yolo_detector.py        # Replace with MediaPipe
├── launch/
│   └── tracking.launch.py      # Launch configuration
└── config/
    └── tracking_params.yaml    # Detection parameters
```

**Learning goals:**
- How does the camera image pipeline work?
- How do you publish detection results to ROS topics?
- How can you integrate MediaPipe Pose into this framework?

---

#### 2. **mini_pupper_bringup** (Hardware Control)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_bringup  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/mini_pupper_bringup/`

**What it does:**
- Launches all base hardware nodes
- Controls servo motors
- Manages audio playback

**Your tasks:**
1. **Study the code** - Understand the launch system
2. **Run vanilla version** - `ros2 launch mini_pupper_bringup bringup.launch.py`
3. **Understand audio** - How to play sounds for reminders
4. **Your touch** - Create custom launch file for posture monitoring mode
5. **This may be a reach** - Add volume control for escalating reminders

**Key files to examine:**
```
mini_pupper_bringup/
├── launch/
│   └── bringup.launch.py       # Main hardware launcher
└── config/
    └── hardware_params.yaml    # Hardware config
```

**Learning goals:**
- How does ROS 2 launch system work?
- How do you play audio through the robot?
- How do you control audio volume programmatically?

---

#### 3. **stanford_controller** (Motion Control for Nudging)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/stanford_controller  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/stanford_controller/`

**What it does:**
- Quadruped gait controller
- Converts velocity commands to leg movements
- Controls walking and body pose

**Your tasks:**
1. **Study the code** - How does motion control work?
2. **Run vanilla version** - Test walking with teleop
3. **Understand cmd_vel** - How to move robot toward user
4. **Your touch** - Create gentle "nudge" motion toward ankle
5. **This may be a reach** - Create nudge that targets specific ankle location

**Key files to examine:**
```
stanford_controller/
└── stanford_controller/
    ├── controller.py           # Main controller logic
    └── gait_controller.py      # Gait patterns
```

**Learning goals:**
- How do you make the robot walk forward a small distance?
- How do you create a gentle, non-aggressive motion?
- How do you stop precisely at the right distance?

---

#### 4. **mini_pupper_dance** (Facial Expressions & Animations)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_dance  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/mini_pupper_dance/`

**What it does:**
- Pre-programmed movement sequences
- Can be adapted for facial expression display
- Animation playback system

**Your tasks:**
1. **Study the code** - How are sequences defined?
2. **Run vanilla version** - Test existing animations
3. **Understand display** - How to show expressions on screen
4. **Your touch** - Create expression animations: gentle, concerned, alert
5. **This may be a reach** - Sync expressions with audio reminders

**Key files to examine:**
```
mini_pupper_dance/
├── mini_pupper_dance/
│   ├── dance_controller.py     # Animation control
│   └── sequence_player.py      # Playback system
└── sequences/
    └── *.yaml                  # Animation definitions
```

**Learning goals:**
- How do you display images/expressions on the robot's screen?
- How do you create custom expression animations?
- How do you trigger expressions from code?

---

### Packages for Reference

#### 5. **mini_pupper_interfaces** (Message Definitions)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_interfaces  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/mini_pupper_interfaces/`

**What it provides:**
- Custom ROS 2 message types
- Service definitions

**Your tasks:**
1. **Study** - Look at existing message types
2. **Your touch** - Create custom messages for your project:
   - `PostureDetection.msg` - Detected posture type and confidence
   - `ReminderLevel.msg` - Current reminder level (1, 2, 3)
   - `PostureEvent.msg` - Timestamp and posture details

**Learning goals:**
- How are custom ROS messages defined?
- When should you create new vs. use standard messages?

---

### API/LLM Integration

#### **apps-md-robots Repository**
**Location:** https://github.com/mangdangroboticsclub/apps-md-robots

**What it provides:**
- Examples of API integrations
- LLM conversation patterns
- Text-to-speech examples

**Your tasks:**
1. **Clone and study** - `git clone https://github.com/mangdangroboticsclub/apps-md-robots`
2. **Examine examples** - Look for audio/speech patterns
3. **Your touch** - Generate varied verbal reminders
4. **This may be a reach** - Live AI-generated reminders with TTS

**Typical integration pattern:**
```python
# Pre-generated reminders (recommended)
SLOUCH_REMINDERS = [
    "Hey! Let's sit up straight!",
    "Your neck will thank you for better posture!",
    "Time for a posture check!",
]

# AI-generated (slower but varied)
def get_ai_reminder(posture_type, level):
    prompt = f"""
    User has bad posture: {posture_type}
    Reminder level: {level}/3
    Generate a friendly reminder under 15 words.
    Level 1 = gentle, Level 3 = more urgent but still kind.
    """
    return llm_api.query(prompt)
```

---

## MediaPipe Pose Integration

### Setup MediaPipe
```bash
pip install mediapipe
```

### Basic Pose Detection Node
```python
import mediapipe as mp
import cv2
import numpy as np
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

class PostureDetector:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.bridge = CvBridge()
        
        # Landmark indices
        self.LEFT_SHOULDER = 11
        self.RIGHT_SHOULDER = 12
        self.LEFT_HIP = 23
        self.RIGHT_HIP = 24
        self.LEFT_KNEE = 25
        self.RIGHT_KNEE = 26
        self.LEFT_ANKLE = 27
        self.RIGHT_ANKLE = 28
        self.LEFT_EAR = 7
        self.RIGHT_EAR = 8
        self.NOSE = 0
    
    def process_frame(self, image):
        """Process frame and return landmarks"""
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb)
        
        if results.pose_landmarks:
            return results.pose_landmarks.landmark
        return None
    
    def detect_leg_crossing(self, landmarks):
        """Detect if legs are crossed (二郎腿)"""
        left_knee_y = landmarks[self.LEFT_KNEE].y
        right_knee_y = landmarks[self.RIGHT_KNEE].y
        left_hip_y = landmarks[self.LEFT_HIP].y
        right_hip_y = landmarks[self.RIGHT_HIP].y
        
        # Left leg over right
        if left_knee_y < right_hip_y - 0.05:
            return "left_over_right"
        # Right leg over left
        if right_knee_y < left_hip_y - 0.05:
            return "right_over_left"
        
        return None
    
    def detect_slouching(self, landmarks):
        """Detect slouching/tech neck"""
        # Get ear and shoulder positions
        left_ear = landmarks[self.LEFT_EAR]
        right_ear = landmarks[self.RIGHT_EAR]
        left_shoulder = landmarks[self.LEFT_SHOULDER]
        right_shoulder = landmarks[self.RIGHT_SHOULDER]
        
        # Average ear position (head center)
        ear_x = (left_ear.x + right_ear.x) / 2
        shoulder_x = (left_shoulder.x + right_shoulder.x) / 2
        
        # Calculate torso length for normalization
        hip_y = (landmarks[self.LEFT_HIP].y + landmarks[self.RIGHT_HIP].y) / 2
        shoulder_y = (left_shoulder.y + right_shoulder.y) / 2
        torso_length = abs(hip_y - shoulder_y)
        
        # Head forward of shoulders
        horizontal_distance = abs(ear_x - shoulder_x)
        
        if horizontal_distance > 0.25 * torso_length:
            return True
        
        return False
    
    def detect_c_spine(self, landmarks):
        """Detect C-shaped spine (tilting to one side)"""
        left_shoulder_y = landmarks[self.LEFT_SHOULDER].y
        right_shoulder_y = landmarks[self.RIGHT_SHOULDER].y
        left_hip_y = landmarks[self.LEFT_HIP].y
        right_hip_y = landmarks[self.RIGHT_HIP].y
        
        # Calculate shoulder width for normalization
        shoulder_width = abs(landmarks[self.LEFT_SHOULDER].x - 
                           landmarks[self.RIGHT_SHOULDER].x)
        
        shoulder_diff = abs(left_shoulder_y - right_shoulder_y)
        hip_diff = abs(left_hip_y - right_hip_y)
        
        if (shoulder_diff > 0.15 * shoulder_width and 
            hip_diff > 0.12 * shoulder_width):
            # Determine which side
            if left_shoulder_y > right_shoulder_y:
                return "leaning_left"
            else:
                return "leaning_right"
        
        return None
```

### Duration Tracking
```python
class PostureDurationTracker:
    def __init__(self):
        self.posture_start_times = {}
        self.duration_thresholds = {
            "leg_crossing": 5.0,      # 5 seconds
            "slouching": 120.0,        # 2 minutes
            "c_spine": 30.0,           # 30 seconds
            "prolonged_sitting": 1800.0  # 30 minutes
        }
    
    def update(self, posture_type, detected):
        """Track duration of detected posture"""
        current_time = time.time()
        
        if detected:
            if posture_type not in self.posture_start_times:
                self.posture_start_times[posture_type] = current_time
            
            duration = current_time - self.posture_start_times[posture_type]
            threshold = self.duration_thresholds.get(posture_type, 5.0)
            
            if duration >= threshold:
                return True, duration
        else:
            # Reset timer if posture corrected
            if posture_type in self.posture_start_times:
                del self.posture_start_times[posture_type]
        
        return False, 0.0
```

---

## Phase-by-Phase Implementation Roadmap

### Phase 1: MediaPipe Pose Detection Setup
**Goal:** Get MediaPipe pose detection working with Mini Pupper camera

**Packages to use:**
- `mini_pupper_tracking` - Camera pipeline
- `mini_pupper_bringup` - Hardware

**Tasks:**
1. Set up robot with camera facing user's desk/chair
2. Install MediaPipe: `pip install mediapipe`
3. Test camera feed: `ros2 launch mini_pupper_bringup bringup.launch.py`
4. Create pose detection node that processes camera images
5. Visualize detected landmarks (draw skeleton on image)
6. Verify that at least some keypoints are detected reliably

**Deliverable:** Real-time pose skeleton displayed on screen

**Code to study:**
```bash
# Look at tracking node for camera integration
cat ~/ros2_ws/src/mini_pupper_ros/mini_pupper_tracking/mini_pupper_tracking/tracking_node.py

# See camera topics
ros2 topic list | grep camera
ros2 topic echo /camera/image_raw
```

---

### Phase 2: Posture Detection Rules
**Goal:** Implement your detection rules for bad postures

**Packages to use:**
- Your pose detection node (Phase 1)
- Custom posture analyzer

**Tasks:**
1. Implement leg crossing detection:
```python
def check_leg_crossing(self, landmarks):
    # Your rule: LEFT_KNEE.y < RIGHT_HIP.y
    if landmarks[self.LEFT_KNEE].y < landmarks[self.RIGHT_HIP].y:
        return "left_over_right"
    if landmarks[self.RIGHT_KNEE].y < landmarks[self.LEFT_HIP].y:
        return "right_over_left"
    return None
```

2. Implement slouching/tech neck detection
3. Implement C-shaped spine detection
4. Implement prolonged sitting detection (low movement variance)
5. Add duration tracking for each posture type
6. Test each detection rule with actual postures

**Deliverable:** All 4 posture types detected with duration thresholds

**Your touch ideas:**
- Calibration phase to learn user's normal posture
- Sensitivity adjustment per posture type
- Visual feedback showing which posture detected

---

### Phase 3: Reminder Level System
**Goal:** Implement escalating reminder levels

**Tasks:**
1. Create reminder level manager:
```python
class ReminderLevelManager:
    def __init__(self):
        self.current_level = 1
        self.last_detection_time = None
        self.L_MAX = 3
        self.L_MIN = 1
    
    def on_bad_posture_detected(self):
        current_time = time.time()
        
        if self.last_detection_time is None:
            # First detection in session
            self.current_level = 1
        else:
            delta_t = current_time - self.last_detection_time
            delta_minutes = delta_t / 60.0
            
            if delta_minutes <= 5:
                # High frequency - level up
                self.current_level = min(self.current_level + 1, self.L_MAX)
            elif delta_minutes <= 20:
                # Moderate - stay same
                pass
            else:
                # Long interval - level down
                self.current_level = max(self.current_level - 1, self.L_MIN)
        
        self.last_detection_time = current_time
        return self.current_level
```

2. Implement level-based responses:
   - Level 1: Soft music only
   - Level 2: Louder music
   - Level 3: Music + nudge

3. Add cool-down rule (suppress for 1 min after Level 3)
4. Test escalation with repeated bad postures
5. Test de-escalation with good posture periods

**Deliverable:** Working 3-level reminder system with proper escalation

---

### Phase 4: Audio & Visual Feedback (MINIMUM VIABLE DEMO)
**Goal:** Robot plays sounds and shows expressions

**Packages to use:**
- `mini_pupper_bringup` - Audio playback
- `mini_pupper_dance` - Display/expressions

**Tasks:**
1. Create/collect audio files:
   - `soft_music_low.wav` - Level 1
   - `soft_music_medium.wav` - Level 2
   - `soft_music_high.wav` - Level 3
   - Or use `espeak` for verbal reminders

2. Test audio playback:
```bash
# Test audio
sudo apt-get install espeak
espeak "Please sit up straight"

# Or play wav file
aplay soft_music.wav
```

3. Create facial expression images:
   - `gentle.png` - Soft, friendly face
   - `concerned.png` - Slightly worried
   - `alert.png` - More urgent expression

4. Implement expression display on robot screen
5. Integrate: posture detected → level calculated → play sound + show face
6. Test full reminder flow

**Deliverable:** Robot responds with appropriate audio and visual feedback

---

### Phase 5: Level 3 Attention-Grabbing Response
**Goal:** Robot does something dramatic to get user's attention at Level 3

**Note:** While ankle nudging is a creative idea, it may not demo well at an exhibition. These alternatives are more visually impressive and easier to execute:

**Packages to use:**
- `mini_pupper_dance` - Dramatic animations
- `stanford_controller` - Movement control

**Option A: Attention Dance (Recommended)**
```python
class AttentionGetter:
    def __init__(self):
        self.dance_pub = self.create_publisher(String, '/dance_command', 10)
    
    def level_3_response(self):
        # Play loud alert sound
        self.play_sound("alert_high.wav")
        
        # Do attention-grabbing dance
        self.trigger_dance("attention_dance")
        
        # Show alert face
        self.show_expression("alert")
```

**Option B: Approach and Stare**
```python
def approach_user(self):
    # Move toward user
    cmd = Twist()
    cmd.linear.x = 0.1  # Walk forward
    
    for _ in range(20):  # ~2 seconds
        self.cmd_vel_pub.publish(cmd)
        time.sleep(0.1)
    
    # Stop and stare with alert expression
    cmd.linear.x = 0.0
    self.cmd_vel_pub.publish(cmd)
    self.show_expression("alert_stare")
```

**Option C: Stand Up Gesture**
```python
def stand_up_alert(self):
    # Robot rises up on hind legs briefly
    # (if supported by stanford_controller)
    self.set_body_pose(pitch=-30)  # Lean back
    time.sleep(1.0)
    self.set_body_pose(pitch=0)    # Return to normal
```

**Tasks:**
1. Create attention dance sequence:
```yaml
# attention_dance.yaml
attention:
  - action: "spin_left"
    duration: 0.3
  - action: "spin_right"
    duration: 0.3
  - action: "jump"
    duration: 0.4
  - action: "bark_pose"
    duration: 0.5
```

2. Test different attention-getters, pick the most effective
3. Combine with loud audio and alert expression
4. Ensure it's noticeable but not annoying

**Deliverable:** Dramatic Level 3 response that grabs attention

**Your touch ideas:**
- Robot "barks" (plays bark sound)
- Robot spins in circles
- Robot does jumping motion

---

### Phase 6: This May Be a Reach

These features are **stretch goals**. Only attempt if Phases 1-4 are solid.

#### Live AI-Generated Reminders
**Goal:** Each reminder is unique and AI-generated

**Tasks:**
1. Study apps-md-robots for LLM integration
2. Create prompt template:
```python
prompt = f"""
Generate a friendly posture reminder. 
Posture issue: {posture_type}
Urgency level: {level}/3
Keep under 15 words. Be kind, not preachy.
"""
```
3. Add text-to-speech for spoken reminders
4. Cache generated reminders to reduce API calls

---

#### Scenario Two: Multi-Student Classroom
**Goal:** Monitor multiple students, navigate and nudge individually

**Packages:** `mini_pupper_navigation`

**Tasks:**
1. Enable multi-person pose detection
2. Track individual students by position
3. Navigate to each student with bad posture
4. Queue reminders and process one by one

**Note:** This is VERY ambitious. Focus on Scenario One first.

---

#### Custom Voice Recording Import
**Goal:** Users record their own reminder messages

**Tasks:**
1. Create audio upload interface
2. Store user recordings
3. Play custom recordings instead of default

---

## Code Organization

### Recommended Package Structure

Create your own package: `posture_monitor`

```
posture_monitor/
├── posture_monitor/
│   ├── __init__.py
│   ├── pose_detector.py          # Phase 1: MediaPipe integration
│   ├── posture_analyzer.py       # Phase 2: Detection rules
│   ├── duration_tracker.py       # Phase 2: Time tracking
│   ├── reminder_manager.py       # Phase 3: Level escalation
│   ├── feedback_controller.py    # Phase 4: Audio/visual
│   └── ankle_nudger.py           # Phase 5: Physical nudge
├── config/
│   ├── detection_thresholds.yaml # Posture detection params
│   └── reminder_settings.yaml    # Level timing params
├── audio/
│   ├── soft_music_low.wav
│   ├── soft_music_medium.wav
│   ├── soft_music_high.wav
│   └── verbal_reminders/
├── expressions/
│   ├── gentle.png
│   ├── concerned.png
│   └── alert.png
├── launch/
│   ├── posture_monitor.launch.py
│   └── test_detection.launch.py
├── test/
│   ├── test_leg_crossing.py
│   ├── test_slouching.py
│   └── test_reminder_levels.py
├── package.xml
└── setup.py
```

---

## Key Learning Resources

### Documentation to Read
1. **MediaPipe Pose:**
   - https://google.github.io/mediapipe/solutions/pose
   - 33 landmark indices and positions

2. **ROS 2 Humble Basics:**
   - https://docs.ros.org/en/humble/Tutorials.html
   - Focus on: Publishers, Subscribers, Timers

3. **Mini Pupper Docs:**
   - https://minipupperdocs.readthedocs.io/

### Code to Study First
```bash
# Camera and detection pipeline
~/ros2_ws/src/mini_pupper_ros/mini_pupper_tracking/

# Hardware and audio
~/ros2_ws/src/mini_pupper_ros/mini_pupper_bringup/

# Motion control (for nudging)
~/ros2_ws/src/mini_pupper_ros/stanford_controller/

# Display/expressions
~/ros2_ws/src/mini_pupper_ros/mini_pupper_dance/

# API examples
git clone https://github.com/mangdangroboticsclub/apps-md-robots
```

---

## Testing Strategy

### Unit Tests

**Pose detection:**
```bash
# Test MediaPipe detection
python test_pose_detection.py

# Sit normally → no detection
# Cross legs → leg_crossing detected
# Slouch → slouching detected
```

**Duration tracking:**
```bash
# Test duration thresholds
# Hold bad posture for threshold time
# Verify trigger happens at correct time
```

**Reminder levels:**
```bash
# Test escalation
# Trigger bad posture repeatedly (<5 min intervals)
# Verify level increases 1→2→3
```

### Integration Test

**Full flow:**
1. Start monitoring
2. Sit with good posture → no reminder
3. Cross legs for 5+ seconds → Level 1 reminder
4. Cross legs again within 5 min → Level 2 reminder
5. Cross legs again within 5 min → Level 3 + nudge
6. Maintain good posture for 20+ min → Level decreases

---

## Success Criteria by Phase

### Phase 1
MediaPipe pose detection working

### Phase 2
Leg crossing detected correctly
Slouching/tech neck detected correctly
C-shaped spine detected correctly
Duration thresholds working
False positive rate is low

### Phase 3 (MINIMUM VIABLE DEMO)
Audio plays at correct levels
Facial expressions display correctly
Full reminder flow works end-to-end
Demo runs reliably (3+ successful runs)

### Phase 5
Attention-grabbing motion is noticeable
Robot movement is safe and controlled
Level 3 response integrated properly
Visually impressive for exhibition
