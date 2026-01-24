# Art Exhibition Company Dog - Technical Roadmap
**Team:** Lian, Ivy  
**Project:** Museum companion robot that follows visitors and provides interactive art gallery experience

---

## Important Notes

**Robot Update Status:** Your robots are NOT yet updated with the latest packages (tracking, navigation). I will update them while you are on your tour tomorrow. When you return, you'll have access to all the packages described in this roadmap.

**GitHub Repository:** All Mini Pupper ROS 2 packages can be found at:
- Main Repository: https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev
- API/LLM Examples: https://github.com/mangdangroboticsclub/apps-md-robots

**How to Study:** Browse these repositories on GitHub to understand the code structure. Read through the files mentioned in each section below. When you have questions about how things work, **ask me**. Understanding these packages is critical before you start modifying them.

---

## Project Overview

Build an art exhibition companion robot that:
- Follows a visitor through the gallery (tracking a marker on their leg)
- Performs different behaviors based on visitor state (following, sitting, guiding, coming back)
- Communicates through text/chat interface (QR code bonding)
- Shows facial expressions based on visitor emotion
- Generates experience summary report at the end

**Exhibition Vision:** A robotic "gallery dog" that enhances the art viewing experience through companionship and interaction. Your pseudocode already outlines clear behavior states - now we need to implement them!

---

## Your Current Design - Implementation Breakdown

Based on your notes, you have four main behavior states:

### A. Visitor Tracking & Behavior States

**State 1: Follow (most situations)**
- Robot tracks visitor using marker detection
- Stays within designated range
- Follows at appropriate distance

**State 2: Sit (visitor stops to appreciate art)**
- Robot detects visitor has stopped (velocity = 0)
- Robot performs sitting animation/pose
- Waits patiently

**State 3: Guide (visitor is clueless)**
- Robot takes the lead
- Guides visitor to next artwork
- Shows direction with body orientation

**State 4: Come Back (visitor doesn't follow)**
- Robot detects visitor is too far or outside range
- Robot moves to side of path
- Or: Robot follows from behind

### B. Communication System
- QR code to bond with robot
- Text/voice chat interface on phone
- Robot shows facial expressions based on text emotion analysis

### C. Experience Summary
- Records time at each painting
- Logs chat conversations
- Generates downloadable report

---

## Key Technical Challenges & Solutions

### Challenge 1: Single-Person Tracking
**Your Solution:** Marker-based tracking (shape on back of visitor's leg)  
**Why this works:** Simple, reliable, no confusion with multiple people  
**Implementation:** Use RGB camera + color/shape detection

### Challenge 2: Multi-Behavior State Machine  
**Your Solution:** Pseudocode with if/else conditions based on position/velocity  
**Implementation:** ROS 2 state machine with behavior nodes

### Challenge 3: Exhibition Space Navigation
**Your Solution:** Designated ranges around each artwork  
**Implementation:** Simple position tracking, possibly Nav2 for path planning

---

## Existing Package Resources

### Packages You'll Use Directly

#### 1. **mini_pupper_dance** (Animation & Movement Primitives)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_dance  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/mini_pupper_dance/`

**What it provides:**
- Pre-programmed movement sequences
- Choreographed actions (sit, stand, turn, etc.)
- Animation playback system

**Your tasks:**
1. **Study the code** - How are dance sequences defined?
2. **Run vanilla version** - Test existing dance moves
3. **Understand sequence format** - How to create custom movements?
4. **Your touch** - Create "sit", "guide", "follow" animations
5. **This may be a reach** - Add emotional expressions through movement

**Key files to examine:**
```
mini_pupper_dance/
├── mini_pupper_dance/
│   ├── dance_controller.py      # Main dance logic
│   └── sequence_player.py       # Plays movement sequences
├── sequences/
│   └── *.yaml                   # Dance sequence definitions
└── launch/
    └── dance.launch.py          # Dance launcher
```

**Learning goals:**
- How are movement sequences stored?
- How to trigger specific animations?
- How to create new behaviors (sitting, guiding)?

**Why start here:** Your behavior states need animations. Understanding the dance package will show you how to make the robot sit, guide, and perform other actions.

---

#### 2. **mini_pupper_tracking** (Visual Marker Detection)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_tracking  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/mini_pupper_tracking/`

**What it provides:**
- YOLO11n object detection
- Camera image processing
- Real-time detection framework
- Bounding box tracking

**Your tasks:**
1. **Study the code** - How does object detection work?
2. **Run vanilla version** - Test person detection
3. **Understand bounding boxes** - How to keep marker centered?
4. **Your touch** - Detect colored marker instead of person
5. **This may be a reach** - Detect multiple markers, track specific one

**Key files to examine:**
```
mini_pupper_tracking/
├── mini_pupper_tracking/
│   ├── tracking_node.py         # Main tracking logic
│   ├── yolo_detector.py         # Detection engine
│   └── camera_processor.py      # Image preprocessing
└── launch/
    └── tracking.launch.py
```

**Learning goals:**
- How to detect colored shapes/markers?
- How to calculate distance to marker?
- How to determine if marker is in "designated range"?

**Why this matters:** Your marker-on-leg solution needs vision detection. This package has the framework - you just need to change what it detects.

---

#### 3. **stanford_controller** (Motion Control)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/stanford_controller  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/stanford_controller/`

**What it provides:**
- Velocity command processing
- Following behavior
- Stopping and movement control

**Your tasks:**
1. **Study the code** - How to command robot movement?
2. **Run vanilla version** - Test with teleop
3. **Understand cmd_vel** - How to follow vs stop vs guide?
4. **Your touch** - Create following controller that keeps marker in bounding box
5. **This may be a reach** - Smooth transitions between behavior states

**Learning goals:**
- How to move forward/backward/turn?
- How to calculate velocity from marker position?
- How to implement "follow from behind"?

---

#### 4. **mini_pupper_navigation** (Path Planning - Optional)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_navigation  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/mini_pupper_navigation/`

**What it provides:**
- Nav2 stack for autonomous navigation
- Path planning
- Obstacle avoidance

**When to use:**
- "Guide" state: Robot leads visitor to next artwork
- "Come back" state: Robot navigates to side of path
- **This may be a reach** for initial demo

**Your tasks:**
1. **Study later** - Understand Nav2 basics
2. **Your touch** - Use for "guide" behavior if simple following isn't enough

**Note:** Start without Nav2. Only add if you need complex navigation.

---

#### 5. **mini_pupper_bringup** (Hardware Control)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_bringup  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/mini_pupper_bringup/`

**What it provides:**
- Hardware initialization
- Sensor access
- Camera feed

**Your tasks:**
1. **Study the code** - How to launch robot hardware?
2. **Run vanilla version** - `ros2 launch mini_pupper_bringup bringup.launch.py`
3. **Understand topics** - Where does camera data come from?

---

#### 6. **mini_pupper_interfaces** (Custom Messages)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_interfaces  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/mini_pupper_interfaces/`

**Your tasks:**
1. **Study** - Look at message definitions
2. **Your touch** - Create custom messages:
   - `BehaviorState.msg` - Current robot behavior (follow/sit/guide/comeback)
   - `VisitorStatus.msg` - Visitor position, velocity, in_range
   - `EmotionState.msg` - Detected emotion from chat
   - `ExperienceLog.msg` - Gallery visit data

---

## Phase-by-Phase Implementation Roadmap

### Phase 0: Understanding Movement & Animation
**Goal:** Learn how robot movements work by studying dance package

**Why start here:** Your project needs custom behaviors (sitting, guiding, following). The dance package shows you how to create these movements.

**Packages to study:**
- `mini_pupper_dance`
- `stanford_controller`

**Tasks:**

**Step 1: Study Dance Package**
1. Browse the dance package on GitHub:
```bash
# Look at dance sequences
mini_pupper_dance/sequences/*.yaml

# Understand the controller
mini_pupper_dance/mini_pupper_dance/dance_controller.py
```

2. Understand how sequences are structured:
```yaml
# Example sequence structure
sequence_name: "sit"
movements:
  - action: "lower_body"
    duration: 1.0
  - action: "hold"
    duration: 2.0
```

3. Run existing dance demos:
```bash
ros2 launch mini_pupper_dance dance.launch.py
```

**Step 2: Create Custom Behavior Animations**
1. Define "sit" behavior:
```yaml
sit_behavior:
  - lower_body
  - rest_pose
```

2. Define "guide" behavior:
```yaml
guide_behavior:
  - look_forward
  - walk_confidently
  - occasional_look_back
```

3. Test animations in isolation

**Deliverable:** Custom movement sequences for each behavior state

**Success criteria:**
- Robot can perform "sit" animation
- Robot can perform "guide" animation
- Animations look natural

---

### Phase 1: Marker Detection & Following
**Goal:** Detect colored marker on visitor's leg and follow it

**Packages to use:**
- `mini_pupper_tracking` - Marker detection
- `stanford_controller` - Following movement
- `mini_pupper_bringup` - Camera access

**Tasks:**

**Step 1: Setup Marker Detection**
1. Choose marker design:
   - **Recommended:** Red circular sticker (easy to detect)
   - Alternative: Specific shape (triangle, square)
   - Size: 5-10cm diameter for visibility

2. Study tracking package:
```bash
# Look at how YOLO detection works
mini_pupper_tracking/mini_pupper_tracking/yolo_detector.py

# Understand camera processing
mini_pupper_tracking/mini_pupper_tracking/camera_processor.py
```

3. Create marker detector node:
```python
class MarkerDetector:
    def __init__(self):
        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10)
        
        self.marker_pub = self.create_publisher(
            MarkerPosition, '/marker_position', 10)
    
    def image_callback(self, msg):
        # Convert to OpenCV format
        cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        
        # Detect red circular marker
        marker_pos = self.detect_red_circle(cv_image)
        
        if marker_pos:
            self.publish_marker_position(marker_pos)
    
    def detect_red_circle(self, image):
        # Convert to HSV color space
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Red color range
        lower_red = np.array([0, 100, 100])
        upper_red = np.array([10, 255, 255])
        mask = cv2.inRange(hsv, lower_red, upper_red)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, 
                                      cv2.CHAIN_APPROX_SIMPLE)
        
        # Find largest circular contour
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 100:  # Minimum size threshold
                # Calculate center
                M = cv2.moments(contour)
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])
                return (cx, cy)
        
        return None
```

**Step 2: Implement Following Logic**
1. Create following controller:
```python
class FollowController:
    def __init__(self):
        self.marker_sub = self.create_subscription(
            MarkerPosition, '/marker_position', self.marker_callback, 10)
        
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Define bounding box (keep marker in center region)
        self.bbox_left = 240   # pixels
        self.bbox_right = 400
        self.bbox_top = 200
        self.bbox_bottom = 400
        
        # Desired distance (in pixels, approximation)
        self.target_size = 150  # marker size when at right distance
    
    def marker_callback(self, msg):
        marker_x = msg.x
        marker_y = msg.y
        marker_size = msg.size
        
        # Check if marker in bounding box
        in_bbox = (self.bbox_left < marker_x < self.bbox_right and 
                   self.bbox_top < marker_y < self.bbox_bottom)
        
        if in_bbox:
            # STATE: Follow - marker in good position
            self.follow_behavior(marker_x, marker_size)
        else:
            # STATE: Adjust - turn to center marker
            self.adjust_behavior(marker_x)
    
    def follow_behavior(self, marker_x, marker_size):
        cmd = Twist()
        
        # Move forward if marker is small (far away)
        if marker_size < self.target_size * 0.8:
            cmd.linear.x = 0.2  # Move forward
        
        # Stop if marker is large (too close)
        elif marker_size > self.target_size * 1.2:
            cmd.linear.x = 0.0  # Stop
        
        # Maintain distance
        else:
            cmd.linear.x = 0.1  # Slow forward
        
        # Small corrections to keep centered
        image_center = 320  # Assuming 640px width
        error = marker_x - image_center
        cmd.angular.z = -error * 0.001  # Turn to center
        
        self.cmd_vel_pub.publish(cmd)
    
    def adjust_behavior(self, marker_x):
        cmd = Twist()
        
        # Turn to face marker
        image_center = 320
        if marker_x < image_center:
            cmd.angular.z = 0.3  # Turn left
        else:
            cmd.angular.z = -0.3  # Turn right
        
        self.cmd_vel_pub.publish(cmd)
```

**Step 3: Test Following**
1. Place marker on test subject's leg
2. Test following at different speeds
3. Test following with turns
4. Tune parameters:
   - Following distance (target_size)
   - Angular correction gain
   - Linear speed

**Deliverable:** Robot follows marker reliably

**Success criteria:**
- Robot follows marker through gallery space
- Maintains 1-2 meter following distance
- Doesn't lose tracking during turns
- Smooth motion (no jerky movements)

---

### Phase 2: Behavior State Machine
**Goal:** Implement four behavior states based on visitor position/velocity

**Packages to use:**
- Custom state machine logic
- `mini_pupper_dance` - Animation playback
- Following controller from Phase 1

**Tasks:**

**Step 1: Implement State Tracking**
1. Create visitor state detector:
```python
class VisitorStateDetector:
    def __init__(self):
        self.marker_sub = self.create_subscription(
            MarkerPosition, '/marker_position', self.marker_callback, 10)
        
        self.state_pub = self.create_publisher(
            BehaviorState, '/behavior_state', 10)
        
        # State tracking
        self.last_marker_pos = None
        self.last_marker_time = None
        self.visitor_velocity = 0.0
        
        # Gallery space definition
        self.artwork_zones = [
            {"name": "painting1", "x_range": [0, 2], "y_range": [0, 1]},
            {"name": "painting2", "x_range": [3, 5], "y_range": [0, 1]},
            # etc.
        ]
    
    def marker_callback(self, msg):
        current_time = self.get_clock().now()
        
        # Calculate visitor velocity
        if self.last_marker_pos and self.last_marker_time:
            dt = (current_time - self.last_marker_time).nanoseconds / 1e9
            dx = msg.x - self.last_marker_pos.x
            self.visitor_velocity = dx / dt
        
        self.last_marker_pos = msg
        self.last_marker_time = current_time
        
        # Determine state
        state = self.determine_state(msg, self.visitor_velocity)
        self.state_pub.publish(state)
    
    def determine_state(self, marker_pos, velocity):
        # Based on your pseudocode
        
        # Check if visitor in designated range
        in_range = self.is_in_designated_range(marker_pos)
        
        if in_range:
            if abs(velocity) < 0.1:  # Visitor stopped
                return "SIT"  # State 2
            else:
                return "FOLLOW"  # State 1
        else:
            # Visitor outside range
            distance = self.calculate_distance_to_visitor(marker_pos)
            
            if distance < 2.0:  # Close but outside range
                return "COMEBACK"  # State 4
            else:  # Far away
                return "GUIDE"  # State 3
        
        return "FOLLOW"  # Default
    
    def is_in_designated_range(self, marker_pos):
        # Check if marker within expected following zone
        # For gallery: check if near current artwork
        for zone in self.artwork_zones:
            if self.in_zone(marker_pos, zone):
                return True
        return False
```

**Step 2: Implement Behavior State Machine**
1. Create state machine:
```python
class BehaviorStateMachine:
    def __init__(self):
        self.state_sub = self.create_subscription(
            BehaviorState, '/behavior_state', self.state_callback, 10)
        
        self.dance_client = self.create_client(PlaySequence, 
                                               '/play_dance_sequence')
        
        self.current_state = "FOLLOW"
        self.follow_controller = FollowController()
    
    def state_callback(self, msg):
        new_state = msg.state
        
        # State transition
        if new_state != self.current_state:
            self.transition_to_state(new_state)
        
        # Execute current state behavior
        self.execute_state(new_state)
    
    def transition_to_state(self, new_state):
        self.get_logger().info(f"Transitioning to {new_state}")
        
        # Play transition animation
        if new_state == "SIT":
            self.play_animation("sit")
        elif new_state == "GUIDE":
            self.play_animation("stand_confident")
        
        self.current_state = new_state
    
    def execute_state(self, state):
        if state == "FOLLOW":
            # Let follow controller handle movement
            self.follow_controller.update()
        
        elif state == "SIT":
            # Stay in sitting position
            self.stop_movement()
            self.play_animation("sit_wait")
        
        elif state == "GUIDE":
            # Move towards next artwork
            self.guide_to_next_artwork()
        
        elif state == "COMEBACK":
            # Move to side or follow from behind
            self.comeback_behavior()
    
    def play_animation(self, animation_name):
        request = PlaySequence.Request()
        request.sequence_name = animation_name
        self.dance_client.call_async(request)
```

**Step 3: Test State Transitions**
1. Test each state in isolation
2. Test transitions between states
3. Verify animations play correctly
4. Tune transition thresholds

**Deliverable:** Working state machine with all four behaviors

**Success criteria:**
- Robot correctly identifies visitor state
- Smooth transitions between states
- Appropriate animations for each state
- No state oscillation (rapid switching)

---

### Phase 3: Communication System
**Goal:** Implement QR code bonding, chat interface, emotion detection

**Packages to use:**
- `apps-md-robots` - API examples for chat integration
- Custom emotion detection logic

**Tasks:**

**Step 1: QR Code Bonding System**
1. Generate unique QR codes:
```python
import qrcode

def generate_robot_qr(robot_id):
    # URL to chat interface
    chat_url = f"https://your-chat-server.com/bond/{robot_id}"
    
    qr = qrcode.make(chat_url)
    qr.save(f"robot_{robot_id}_qr.png")
```

2. Create bonding interface:
   - Display QR code on robot or sign
   - Visitor scans to access chat
   - Chat interface opens with robot connection

**Step 2: Chat Interface (Simple Web App)**
1. Create basic chat UI:
```html
<!-- Simple chat interface -->
<div id="chat-container">
    <div id="messages"></div>
    <input type="text" id="message-input" placeholder="Chat with robot...">
    <button onclick="sendMessage()">Send</button>
</div>
```

2. Connect to ROS 2:
```python
class ChatInterface:
    def __init__(self):
        self.chat_sub = self.create_subscription(
            String, '/user_message', self.message_callback, 10)
        
        self.emotion_pub = self.create_publisher(
            EmotionState, '/detected_emotion', 10)
    
    def message_callback(self, msg):
        user_text = msg.data
        
        # Detect emotion from text
        emotion = self.detect_emotion(user_text)
        
        # Publish emotion
        emotion_msg = EmotionState()
        emotion_msg.emotion = emotion
        emotion_msg.confidence = 0.8
        self.emotion_pub.publish(emotion_msg)
    
    def detect_emotion(self, text):
        # Simple keyword-based emotion detection
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["love", "beautiful", "amazing"]):
            return "happy"
        elif any(word in text_lower for word in ["interesting", "hmm", "curious"]):
            return "curious"
        elif any(word in text_lower for word in ["boring", "meh", "whatever"]):
            return "bored"
        else:
            return "neutral"
```

**Step 3: Facial Expression System**
1. Map emotions to robot behaviors:
```python
EMOTION_EXPRESSIONS = {
    "happy": {
        "ears": "up",
        "tail": "wag",
        "movement": "excited_wiggle"
    },
    "curious": {
        "head": "tilt",
        "ears": "forward",
        "movement": "lean_forward"
    },
    "bored": {
        "head": "down",
        "ears": "droop",
        "movement": "slow_shuffle"
    },
    "neutral": {
        "head": "normal",
        "ears": "relaxed"
    }
}
```

2. Implement expression player:
```python
class ExpressionController:
    def __init__(self):
        self.emotion_sub = self.create_subscription(
            EmotionState, '/detected_emotion', 
            self.emotion_callback, 10)
        
        self.dance_client = self.create_client(PlaySequence, 
                                               '/play_dance_sequence')
    
    def emotion_callback(self, msg):
        emotion = msg.emotion
        
        # Get expression for emotion
        expression = EMOTION_EXPRESSIONS.get(emotion, 
                                             EMOTION_EXPRESSIONS["neutral"])
        
        # Play corresponding animation
        if "movement" in expression:
            self.play_animation(expression["movement"])
```

**Deliverable:** Working chat system with emotion-based expressions

**Success criteria:**
- Visitor can scan QR code and open chat
- Messages reach robot
- Robot shows appropriate expression for emotion
- Expressions are clear and engaging

**This may be a reach:**
- Advanced NLP emotion detection using LLM
- Voice input instead of text
- More sophisticated facial animations

---

### Phase 4: Experience Summary System
**Goal:** Log visitor journey and generate downloadable report

**Tasks:**

**Step 1: Data Logging**
1. Create experience logger:
```python
class ExperienceLogger:
    def __init__(self):
        self.state_sub = self.create_subscription(
            BehaviorState, '/behavior_state', 
            self.state_callback, 10)
        
        self.chat_sub = self.create_subscription(
            String, '/user_message', 
            self.chat_callback, 10)
        
        # Log data structures
        self.visit_start_time = self.get_clock().now()
        self.artwork_times = {}
        self.chat_log = []
        self.current_artwork = None
    
    def state_callback(self, msg):
        # Track time at each artwork
        if msg.location and msg.location != self.current_artwork:
            if self.current_artwork:
                # Log time at previous artwork
                time_spent = (self.get_clock().now() - 
                             self.artwork_times[self.current_artwork]["start"])
                self.artwork_times[self.current_artwork]["duration"] = time_spent
            
            # Start timing new artwork
            self.current_artwork = msg.location
            self.artwork_times[msg.location] = {
                "start": self.get_clock().now(),
                "duration": 0
            }
    
    def chat_callback(self, msg):
        # Log chat message
        self.chat_log.append({
            "time": self.get_clock().now(),
            "message": msg.data
        })
    
    def generate_report(self):
        report = {
            "visit_duration": self.get_clock().now() - self.visit_start_time,
            "artworks_viewed": len(self.artwork_times),
            "time_per_artwork": self.artwork_times,
            "chat_messages": len(self.chat_log),
            "chat_log": self.chat_log
        }
        return report
```

**Step 2: Report Generation**
1. Create report formatter:
```python
def format_report_html(report_data):
    html = f"""
    <html>
    <head><title>Gallery Experience Report</title></head>
    <body>
        <h1>Your Gallery Visit Summary</h1>
        <p>Total visit time: {report_data['visit_duration']}</p>
        <h2>Artworks Viewed:</h2>
        <ul>
    """
    
    for artwork, data in report_data['time_per_artwork'].items():
        html += f"<li>{artwork}: {data['duration']} seconds</li>"
    
    html += """
        </ul>
        <h2>Your Conversations:</h2>
    """
    
    for chat in report_data['chat_log']:
        html += f"<p>{chat['message']}</p>"
    
    html += """
    </body>
    </html>
    """
    
    return html
```

**Step 3: Report Delivery**
1. Options for delivery:
   - Email (visitor provides email at start)
   - Download link in chat interface
   - QR code with download URL

**Deliverable:** Experience summary report system

**Success criteria:**
- System tracks time at each artwork
- Chat conversations logged
- Report generated at end of visit
- Visitor can download/access report

---

## Exhibition Display Recommendations

### Physical Setup

**Gallery Layout:**
1. **Multiple artwork stations** (3-5 paintings/exhibits)
2. **Clear pathways** between stations (1.5-2m wide)
3. **Designated viewing areas** at each artwork
4. **QR code display** at entrance for bonding
5. **Safety barriers** to keep robot in exhibition space

**Visitor Experience Flow:**
1. Visitor scans QR code at entrance
2. Attaches marker to back of leg
3. Robot greets and begins following
4. Visitor walks through gallery
5. Robot follows, sits when visitor stops
6. Visitor can chat throughout
7. At end, visitor receives experience report

**Visual Elements:**
- Robot wearing gallery "uniform" (cute vest or badge)
- Clear signage explaining interaction
- Marker attachment instructions
- Safety guidelines

---

## Implementation Strategy

### Parallel Work Streams

**Phase 0: Foundation (START HERE)**
- Study `mini_pupper_dance` package
- Understand movement sequences
- Test existing animations
- Create custom behavior animations

**Phase 1: Core Following**
- Implement marker detection
- Create following controller
- Test in simple environment
- Tune following parameters

**Phase 2: Behavior States**
- Build state machine
- Integrate animations
- Test state transitions
- Add exhibition space awareness

**Phase 3: Communication**
- Setup QR code system
- Build chat interface
- Implement emotion detection
- Create facial expressions

**Phase 4: Experience Logging**
- Add data logging
- Generate reports
- Test end-to-end flow
- Polish user experience

**Display Team (Parallel):**
- Design gallery layout
- Create artwork displays
- Test robot movement space
- Add aesthetic elements
- Prepare demo presentation

---

## Code Organization

### Recommended Package Structure

Create your package: `exhibition_companion_dog`

```
exhibition_companion_dog/
├── exhibition_companion_dog/
│   ├── __init__.py
│   ├── marker_detector.py          # Phase 1: Vision
│   ├── follow_controller.py        # Phase 1: Following
│   ├── visitor_state_detector.py   # Phase 2: State tracking
│   ├── behavior_state_machine.py   # Phase 2: Behaviors
│   ├── chat_interface.py           # Phase 3: Communication
│   ├── emotion_detector.py         # Phase 3: Emotions
│   ├── expression_controller.py    # Phase 3: Expressions
│   └── experience_logger.py        # Phase 4: Logging
├── animations/
│   ├── sit.yaml                    # Custom animations
│   ├── guide.yaml
│   └── excited.yaml
├── launch/
│   ├── companion_dog.launch.py     # Main launcher
│   └── test_behaviors.launch.py    # Testing
├── config/
│   ├── marker_params.yaml          # Detection parameters
│   ├── behavior_params.yaml        # State thresholds
│   └── gallery_map.yaml            # Artwork locations
├── web/
│   ├── chat_interface.html         # Web chat UI
│   ├── qr_generator.py             # QR code creation
│   └── report_generator.py         # Report creation
├── test/
│   ├── test_marker_detection.py
│   ├── test_following.py
│   └── test_state_machine.py
├── package.xml
└── setup.py
```

---

## Key Learning Resources

### Documentation to Read
1. **ROS 2 State Machines:**
   - https://docs.ros.org/en/humble/Tutorials.html
   - BehaviorTree.CPP for complex logic

2. **Mini Pupper Packages:**
   - Dance: https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_dance
   - Tracking: https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_tracking

3. **Computer Vision:**
   - OpenCV color detection: https://docs.opencv.org/
   - HSV color space for marker detection

### Code to Study First
```bash
# Movement and animation
~/ros2_ws/src/mini_pupper_ros/mini_pupper_dance/

# Visual detection
~/ros2_ws/src/mini_pupper_ros/mini_pupper_tracking/

# Motion control
~/ros2_ws/src/mini_pupper_ros/stanford_controller/
```

---

## Testing Strategy

### Unit Tests

**Marker detection:**
```bash
# Test with static image
python test_marker_detector.py test_image.jpg

# Test with camera feed
ros2 run exhibition_companion_dog marker_detector
# Hold marker in front of camera
```

**Following controller:**
```bash
# Test in open space
# Person with marker walks in patterns:
# - Straight line
# - Turns
# - Stop and go
# - Speed variations
```

**State machine:**
```bash
# Test each state transition
# Verify correct behavior in each state
# Check state doesn't oscillate
```

### Integration Tests

**Full system:**
1. Visitor approaches with marker
2. Robot begins following
3. Visitor stops → robot sits
4. Visitor continues → robot follows
5. Visitor goes off path → robot guides back
6. Chat messages → robot shows expressions
7. End of visit → report generated

### Performance Metrics

- **Following accuracy:** Robot maintains 1-2m distance
- **State response time:** <1 second to detect state change
- **Marker detection rate:** >90% detection (when visible)
- **Expression timing:** Emotion displayed within 2 seconds of message

---

## Success Criteria by Phase

### Phase 0 (Movement Foundation) - START HERE
Understand dance package structure
Can trigger existing animations
Created custom "sit" animation
Created custom "guide" animation

### Phase 1 (Following) - MINIMUM VIABLE DEMO
Marker detection working
Robot follows marker smoothly
Maintains appropriate distance (1-2m)
Doesn't lose tracking during movement

### Phase 2 (Behavior States)
State machine implemented
All four states working (follow/sit/guide/comeback)
Smooth transitions between states
Appropriate animations for each state

### Phase 3 (Experience Logging)
Visit data logged throughout
Report generated at end
Visitor can access report
Report includes timing and chat data

### Phase 4 (Communication--might not work!)
QR code bonding works
Chat interface functional
Emotion detection responds to messages
Robot shows expressions based on emotions
