# ADHD Focus Companion Robot - Technical Roadmap
**Team:**  Zilin, Andong, Sidi
**Project:** Productivity companion robot that helps users with ADHD stay focused on tasks

---

## Important Notes

**Robot Update Status:** Your robots are NOT yet updated with the latest packages (tracking, navigation). I will update them while you are on your tour tomorrow. When you return, you'll have access to all the packages described in this roadmap.

**GitHub Repository:** All Mini Pupper ROS 2 packages can be found at:
- Main Repository: https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev
- API/LLM Examples: https://github.com/mangdangroboticsclub/apps-md-robots

**How to Study:** Browse these repositories on GitHub to understand the code structure. Read through the files mentioned in each section below. When you have questions about how things work, **ask me**. Understanding these packages is critical before you start modifying them.

---

## Project Overview

Build a productivity companion robot that helps users with ADHD overcome "start-up difficulties" by:
- Detecting when the user is at their desk
- Running focus timer sessions (Pomodoro-style)
- Providing calming presence through breathing animations
- Giving encouragement at milestones
- Celebrating completed focus sessions

This is a **scoped-down, achievable version** of an ADHD assistant that focuses on mastery of core robotics concepts: person detection, expressive movement, and state management.

---

## Existing Package Resources

### Packages You'll Use Directly

#### 1. **mini_pupper_tracking** (Person/Presence Detection)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_tracking  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/mini_pupper_tracking/`

**What it does:**
- Real-time person detection using YOLO11n
- Camera-based human tracking
- Publishes detection information to ROS topics

**Your tasks:**
1. **Study the code** - Look at how YOLO detection works
2. **Run vanilla version** - Test person detection at a desk setup
3. **Understand topics** - What ROS topics does it publish?
4. **Your touch** - Simplify to presence detection (person in frame = at desk)
5. **This may be a reach** - Add head pose estimation for "focused vs distracted"

**Key files to examine:**
```
mini_pupper_tracking/
├── mini_pupper_tracking/
│   ├── tracking_node.py        # Main detection logic
│   └── yolo_detector.py        # YOLO model wrapper
├── launch/
│   └── tracking.launch.py      # Launch configuration
└── config/
    └── tracking_params.yaml    # Detection parameters
```

**Learning goals:**
- How does YOLO person detection work?
- How do ROS topics carry detection data?
- How can you trigger actions when a person is detected/absent?

---

#### 2. **mini_pupper_dance** (Expressive Animations)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_dance  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/mini_pupper_dance/`

**What it does:**
- Pre-programmed movement sequences
- Animation playback system
- Expressive robot movements

**Your tasks:**
1. **Study the code** - How are dance sequences defined?
2. **Run vanilla version** - Test existing dances
3. **Understand sequences** - How to create custom movements?
4. **Your touch** - Create focus-related animations:
   - `breathing_loop` - Slow rise/fall for calm presence
   - `celebration` - Happy dance when session completes
   - `encouragement` - Small gesture for milestones
5. **This may be a reach** - Sync breathing animation speed with timer progress

**Key files to examine:**
```
mini_pupper_dance/
├── mini_pupper_dance/
│   ├── dance_controller.py     # Animation control
│   └── sequence_player.py      # Playback system
├── sequences/
│   └── *.yaml                  # Dance definitions
└── launch/
    └── dance.launch.py
```

**Learning goals:**
- How are movement sequences defined in YAML?
- How do you trigger animations from code?
- How do you create smooth, looping movements?

---

#### 3. **mini_pupper_bringup** (Hardware Control)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_bringup  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/mini_pupper_bringup/`

**What it does:**
- Launches all base hardware nodes
- Controls servo motors
- Manages robot state and audio

**Your tasks:**
1. **Study the code** - Understand the launch system
2. **Run vanilla version** - `ros2 launch mini_pupper_bringup bringup.launch.py`
3. **Understand audio** - How to play sounds for encouragement
4. **Your touch** - Create custom launch file for desk companion mode
5. **This may be a reach** - Add LED control for timer visualization

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
- What hardware features are available?

---

#### 4. **stanford_controller** (Motion Control)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/stanford_controller  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/stanford_controller/`

**What it does:**
- Quadruped gait controller
- Converts velocity commands to leg movements
- Handles body pose adjustments

**Your tasks:**
1. **Study the code** - How does pose control work?
2. **Run vanilla version** - Test body movements
3. **Understand body pose** - Can you make the robot "breathe" (rise/lower body)?
4. **Your touch** - Create subtle breathing motion using body height changes
5. **This may be a reach** - Add expressive head tilts for engagement

**Key files to examine:**
```
stanford_controller/
└── stanford_controller/
    ├── controller.py           # Main controller logic
    └── state_command.py        # Body pose commands
```

**Learning goals:**
- How do you control body height/pose?
- What's the difference between walking and stationary movements?
- How do you create subtle, calming motions?

---

### Packages for Reference (Study, Don't Modify Yet)

#### 5. **mini_pupper_interfaces** (Message Definitions)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_interfaces  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/mini_pupper_interfaces/`

**What it provides:**
- Custom ROS 2 message types
- Service definitions

**Your tasks:**
1. **Study** - Look at existing message types
2. **Your touch** - Create custom messages for your project:
   - `FocusState.msg` - Current timer state (IDLE, FOCUSING, PAUSED, COMPLETE)
   - `UserPresence.msg` - Is user at desk?
   - `SessionStats.msg` - Focus session statistics

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
- Text generation examples

**Your tasks:**
1. **Clone and study** - `git clone https://github.com/mangdangroboticsclub/apps-md-robots`
2. **Examine examples** - Look for text generation patterns
3. **Your touch** - Generate varied encouragement messages
4. **This may be a reach** - Full task planning conversation with LLM

**Typical integration pattern:**
```python
# Generate encouragement at milestone
def get_encouragement(minutes_completed, total_minutes):
    prompt = f"""
    User has focused for {minutes_completed} of {total_minutes} minutes.
    Give a short, encouraging message (under 15 words).
    Be warm and supportive, not patronizing.
    """
    response = llm_api.query(prompt)
    return response
```

**Key integration points:**
- Milestone messages can be pre-written OR LLM-generated
- LLM adds variety but isn't required for core functionality
- API calls should not block the timer

---

## Attention/Focus Detection Networks

For detecting whether the user is focused vs distracted, you can optionally add more sophisticated detection beyond simple presence.

### Recommended: MediaPipe Face Mesh (Lightweight)
**Why:** Runs on Raspberry Pi, gives head pose for "looking at work" detection

```python
import mediapipe as mp

class FocusDetector:
    def __init__(self):
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            max_num_faces=1,
            min_detection_confidence=0.5
        )
    
    def detect_focus_state(self, image):
        """Returns: 'focused', 'distracted', or 'absent'"""
        results = self.face_mesh.process(image)
        
        if not results.multi_face_landmarks:
            return "absent"
        
        # Get head pose from landmarks
        head_pitch, head_yaw = self.get_head_pose(results)
        
        # Looking at desk/screen = focused
        if abs(head_yaw) < 30 and -45 < head_pitch < 15:
            return "focused"
        else:
            return "distracted"
```

### Alternative Networks (This may be a reach)

| Network | What it detects | Runs on Pi? |
|---------|----------------|-------------|
| MediaPipe Face Mesh | Head pose, gaze direction | Yes (10-15 FPS) |
| FER (pip install fer) | Emotions (frustrated, happy) | Slow (5-8 FPS) |
| DAiSEE models | Engagement/boredom | No (needs PC) |

**Recommendation:** Start with simple presence detection (person in frame). Add MediaPipe head pose only if you have time and core features work well.

---

## Phase-by-Phase Implementation Roadmap

### Phase 1: Presence Detection & Basic Timer
**Goal:** Detect user at desk, run countdown timer

**Packages to use:**
- `mini_pupper_tracking` - Person detection
- `mini_pupper_bringup` - Hardware

**Tasks:**
1. Set up robot at desk position with camera facing chair
2. Run tracking: `ros2 launch mini_pupper_tracking tracking.launch.py`
3. Test person detection - verify it sees when you sit/leave
4. Create simple presence node:
```python
class PresenceDetector:
    def __init__(self):
        self.detection_sub = self.create_subscription(
            DetectionArray, '/detections', self.detection_callback, 10)
        self.user_present = False
        self.last_seen_time = None
    
    def detection_callback(self, msg):
        if len(msg.detections) > 0:
            self.user_present = True
            self.last_seen_time = self.get_clock().now()
        else:
            # Mark absent after 5 seconds of no detection
            if self.last_seen_time:
                elapsed = (self.get_clock().now() - self.last_seen_time).nanoseconds / 1e9
                if elapsed > 5.0:
                    self.user_present = False
```

5. Create focus timer node:
```python
class FocusTimer:
    def __init__(self):
        self.state = "IDLE"  # IDLE, FOCUSING, PAUSED, COMPLETE
        self.duration_seconds = 25 * 60  # 25 minutes
        self.remaining = self.duration_seconds
        
        self.timer = self.create_timer(1.0, self.tick)
    
    def start_session(self):
        self.state = "FOCUSING"
        self.remaining = self.duration_seconds
        print(f"Starting {self.duration_seconds // 60} minute focus session!")
    
    def tick(self):
        if self.state == "FOCUSING" and self.user_present:
            self.remaining -= 1
            mins, secs = divmod(self.remaining, 60)
            print(f"Focus: {mins:02d}:{secs:02d}")
            
            if self.remaining <= 0:
                self.state = "COMPLETE"
                self.on_complete()
        
        elif self.state == "FOCUSING" and not self.user_present:
            self.state = "PAUSED"
            print("You left - timer paused")
    
    def on_complete(self):
        print("Session complete! Great work!")
```

6. Test timer with presence - verify pause when you leave

**Deliverable:** Timer counts down when user present, pauses when absent

**Code to study:**
```bash
# Look at tracking node
cat ~/ros2_ws/src/mini_pupper_ros/mini_pupper_tracking/mini_pupper_tracking/tracking_node.py

# See what topics it publishes
ros2 topic list | grep -i track
ros2 topic echo /detections
```

---

### Phase 2: Breathing Animation During Focus
**Goal:** Robot performs calming breathing movement during focus sessions

**Packages to use:**
- `mini_pupper_dance` - Animation system
- `stanford_controller` - Body pose control

**Tasks:**
1. Study dance package:
```bash
# Look at how dances are defined
ls ~/ros2_ws/src/mini_pupper_ros/mini_pupper_dance/sequences/
cat ~/ros2_ws/src/mini_pupper_ros/mini_pupper_dance/sequences/dance1.yaml
```

2. Create breathing animation sequence:
```yaml
# breathing_loop.yaml
breathing:
  - body_height: 0.12    # Rise up
    duration: 3.0
  - body_height: 0.08    # Lower down
    duration: 3.0
  # Loops automatically
```

3. Alternative: Use stanford_controller directly for body height:
```python
class BreathingAnimation:
    def __init__(self):
        self.body_height_pub = self.create_publisher(
            Float32, '/body_height', 10)
        
        self.breathing = False
        self.breath_timer = self.create_timer(0.1, self.breathe_tick)
        self.breath_phase = 0.0
    
    def start_breathing(self):
        self.breathing = True
    
    def stop_breathing(self):
        self.breathing = False
    
    def breathe_tick(self):
        if not self.breathing:
            return
        
        # Sine wave for smooth breathing
        import math
        self.breath_phase += 0.05  # Speed of breathing
        height = 0.10 + 0.02 * math.sin(self.breath_phase)
        
        msg = Float32()
        msg.data = height
        self.body_height_pub.publish(msg)
```

4. Integrate with timer - start breathing when session starts, stop when done
5. Test that breathing is calming, not distracting (adjust speed/amplitude)

**Deliverable:** Robot "breathes" slowly during focus sessions

**Your touch ideas:**
- Slower breathing as session progresses
- Slightly faster breathing near completion (building anticipation)
- Different breathing pattern for breaks

---

### Phase 3: Encouragement & Celebration
**Goal:** Robot encourages at milestones, celebrates completion

**Packages to use:**
- `mini_pupper_dance` - Celebration animation
- `mini_pupper_bringup` - Audio playback

**Tasks:**
1. Define milestone times:
```python
MILESTONES = [
    {"remaining": 20*60, "message": "5 minutes in! Great start!"},
    {"remaining": 15*60, "message": "10 minutes! Keep going!"},
    {"remaining": 10*60, "message": "Halfway there!"},
    {"remaining": 5*60, "message": "Final stretch! Almost done!"},
]
```

2. Create encouragement system:
```python
class EncouragementSystem:
    def __init__(self):
        self.triggered_milestones = set()
    
    def check_milestones(self, remaining_seconds):
        for milestone in MILESTONES:
            if (remaining_seconds <= milestone["remaining"] and 
                milestone["remaining"] not in self.triggered_milestones):
                
                self.give_encouragement(milestone["message"])
                self.triggered_milestones.add(milestone["remaining"])
    
    def give_encouragement(self, message):
        print(f"🐶 {message}")
        self.play_sound("encouragement_beep.wav")
        self.play_animation("small_nod")
```

3. Create celebration animation for completion:
```yaml
# celebration.yaml
celebration:
  - action: "jump"
    duration: 0.5
  - action: "spin_left"
    duration: 0.5
  - action: "spin_right" 
    duration: 0.5
  - action: "happy_bounce"
    duration: 1.0
```

4. Add audio feedback:
```bash
# Test audio on robot
sudo apt-get install espeak
espeak "Great job! You stayed focused!"

# Or use pre-recorded sounds
aplay /path/to/celebration.wav
```

5. Integrate: milestone → encouragement, completion → celebration

**Deliverable:** Robot gives encouragement and celebrates success

**Your touch ideas:**
- Vary encouragement messages (don't repeat same one)
- Different celebration intensity based on session length
- Track streaks across sessions

---

### Phase 4: Session Control Interface (MINIMUM VIABLE DEMO)
**Goal:** User can start/stop sessions, see status

**Tasks:**
1. Create simple control interface:
```python
# Option A: Keyboard commands
class SessionController:
    def __init__(self):
        self.keyboard_sub = self.create_subscription(
            String, '/keyboard_input', self.handle_input, 10)
    
    def handle_input(self, msg):
        if msg.data == 's':  # Start
            self.timer.start_session()
        elif msg.data == 'p':  # Pause
            self.timer.pause()
        elif msg.data == 'r':  # Resume
            self.timer.resume()
        elif msg.data == 'q':  # Quit
            self.timer.cancel()
```

2. Option B: Simple web interface (Flask):
```python
from flask import Flask, render_template
app = Flask(__name__)

@app.route('/start/<int:minutes>')
def start_session(minutes):
    # Publish to ROS topic
    return f"Started {minutes} minute session"

@app.route('/status')
def get_status():
    return {"state": timer.state, "remaining": timer.remaining}
```

3. Display current status:
   - Timer countdown (terminal, web page, or robot display)
   - Session state (FOCUSING, PAUSED, etc.)
   - Encouragement messages

4. Test full flow:
   - Start session
   - Robot starts breathing
   - User "leaves" (timer pauses)
   - User returns (timer resumes)
   - Milestone encouragement
   - Completion celebration

**Deliverable:** Complete focus session flow with user control

---

### Phase 5: This May Be a Reach

These features are **stretch goals**. Only attempt if Phases 1-4 are solid.

#### Head Pose Focus Detection
**Goal:** Detect if user is looking at work vs distracted

**Tasks:**
1. Add MediaPipe Face Mesh:
```bash
pip install mediapipe
```

2. Implement focus detection:
```python
# If user looks away for >30 seconds, gentle reminder
if focus_state == "distracted":
    distraction_time += 1
    if distraction_time > 30:
        self.gentle_reminder()
        distraction_time = 0
```

3. Gentle reminder (not annoying):
   - Small sound
   - Subtle movement
   - Message: "Hey, let's get back to it!"

---

#### LLM-Generated Encouragement
**Packages:** `apps-md-robots` examples

**Tasks:**
1. Study LLM integration from apps-md-robots
2. Generate varied encouragement:
```python
def get_llm_encouragement(minutes_done, total_minutes):
    prompt = f"User focused for {minutes_done}/{total_minutes} min. Short encouragement:"
    return llm_api.query(prompt)
```

3. Fallback to pre-written messages if API fails

---

#### Task Planning Assistant
**Goal:** Help user break down tasks before starting

**Tasks:**
1. Simple task input:
```python
task = input("What are you working on? ")
# "Writing my essay"
```

2. Basic breakdown (rule-based or LLM):
```python
def break_down_task(task):
    if "write" in task.lower() or "essay" in task.lower():
        return ["Outline main points", "Write intro", "Write body", "Conclude"]
    else:
        return ["Start first part", "Continue working", "Finish up"]
```

3. Display steps before session starts

---

#### Gamification/Rewards
**Goal:** Points and rewards for completed sessions

**Tasks:**
1. Track completed sessions and total focus time
2. Award "coins" for completion
3. Unlock new celebrations or sounds
4. Daily/weekly streaks

---

## Code Organization

### Recommended Package Structure

Create your own package: `focus_companion`

```
focus_companion/
├── focus_companion/
│   ├── __init__.py
│   ├── presence_detector.py      # Phase 1
│   ├── focus_timer.py            # Phase 1
│   ├── breathing_animation.py    # Phase 2
│   ├── encouragement_system.py   # Phase 3
│   └── session_controller.py     # Phase 4
├── animations/
│   ├── breathing_loop.yaml
│   ├── celebration.yaml
│   └── encouragement_nod.yaml
├── sounds/
│   ├── session_start.wav
│   ├── encouragement.wav
│   └── celebration.wav
├── launch/
│   ├── focus_companion.launch.py
│   └── test_breathing.launch.py
├── config/
│   ├── timer_params.yaml
│   └── milestones.yaml
├── web/                          # Optional Phase 4
│   └── templates/
│       └── dashboard.html
├── package.xml
└── setup.py
```

---

## Key Learning Resources

### Documentation to Read
1. **ROS 2 Humble Basics:**
   - https://docs.ros.org/en/humble/Tutorials.html
   - Focus on: Publishers, Subscribers, Timers

2. **Mini Pupper Docs:**
   - https://minipupperdocs.readthedocs.io/
   - Understanding the robot

3. **MediaPipe Face Mesh (optional):**
   - https://google.github.io/mediapipe/solutions/face_mesh
   - For head pose detection

### Code to Study First
```bash
# Person detection
~/ros2_ws/src/mini_pupper_ros/mini_pupper_tracking/

# Animation system
~/ros2_ws/src/mini_pupper_ros/mini_pupper_dance/

# Hardware bringup
~/ros2_ws/src/mini_pupper_ros/mini_pupper_bringup/

# Body pose control
~/ros2_ws/src/mini_pupper_ros/stanford_controller/

# API examples
git clone https://github.com/mangdangroboticsclub/apps-md-robots
```

---

## Testing Strategy

### Unit Tests

**Presence detection:**
```bash
# Run tracking
ros2 launch mini_pupper_tracking tracking.launch.py

# Sit at desk → should detect
# Leave desk → should mark absent after 5 seconds
```

**Timer:**
```bash
# Run timer node
ros2 run focus_companion focus_timer

# Test: start, pause, resume, complete
```

**Breathing:**
```bash
# Test breathing animation
ros2 run focus_companion breathing_animation

# Verify smooth, calming motion
# Not jerky or distracting
```

---

## Success Criteria by Phase

### Phase 1
Presence detection works (user at desk)
Timer displays on the screen of the pupper
Timer counts down correctly
Timer pauses when user leaves
Timer resumes when user returns

### Phase 2
Breathing animation plays during focus
Animation is smooth and calming
Animation stops when session ends

### Phase 3
Encouragement at milestone times
Audio feedback works with either plain voice recordings or with AI/LLM feedback
Celebration on completion
Celebration feels rewarding

### Phase 4 (MINIMUM VIABLE DEMO)
User can start/stop sessions
Status clearly displayed
Full session flow works end-to-end
Demo runs reliably (3+ successful runs)

### Phase 5 (This may be a reach)
ONE advanced feature working
Doesn't break Phase 1-4 functionality
Adds genuine value to experience
