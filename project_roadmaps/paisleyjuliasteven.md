# Bodega Cat MP2 - Technical Roadmap
**Team:** Steven, Paisley, Julia  
**Project:** Shelf-based store assistant robot using Mini Pupper 2

---

## Important Notes

**Robot Update Status:** Your robots are NOT yet updated with the latest packages (tracking, navigation). I will update them while you are on your tour tomorrow. When you return, you'll have access to all the packages described in this roadmap.

**GitHub Repository:** All Mini Pupper ROS 2 packages can be found at:
- Main Repository: https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev
- API/LLM Examples: https://github.com/mangdangroboticsclub/apps-md-robots

**How to Study:** Browse these repositories on GitHub to understand the code structure. Read through the files mentioned in each section below. When you have questions about how things work, **ask me**. Understanding these packages is critical before you start modifying them.

---

## Project Overview

Build a "bodega cat" robot that lives on a shelf track, greets customers, helps them find products, and creates a welcoming store experience. This is a **scoped-down, achievable version** of autonomous retail assistance that focuses on mastery of core robotics concepts.

---

## Existing Package Resources

### Packages You'll Use Directly

#### 1. **mini_pupper_tracking** (Person Detection Foundation)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_tracking  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/mini_pupper_tracking/`

**What it does:**
- Real-time person detection using YOLO11n
- Camera-based human tracking
- Publishes detection information to ROS topics

**Your tasks:**
1. **Study the code** - Look at how YOLO detection works
2. **Run vanilla version** - Test person detection in your workspace
3. **Understand topics** - What ROS topics does it publish?
4. **Your touch** - Modify detection to trigger greeting behavior
5. **AMBITIOUS SAUCE** - Add distance estimation, customer counting

**Key files to examine:**
```
mini_pupper_tracking/
├── mini_pupper_tracking/
│   ├── tracking_node.py        # Main detection logic
│   └── yolo_detector.py         # YOLO model wrapper
├── launch/
│   └── tracking.launch.py       # Launch configuration
└── config/
    └── tracking_params.yaml     # Detection parameters
```

**Learning goals:**
- How does YOLO person detection work?
- How do ROS topics carry detection data?
- How can you trigger actions when a person is detected?

---

#### 2. **mini_pupper_bringup** (Hardware Control)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_bringup  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/mini_pupper_bringup/`

**What it does:**
- Launches all base hardware nodes
- Controls servo motors for walking
- Manages robot state

**Your tasks:**
1. ****Study the code** - Understand the launch system
2. ****Run vanilla version** - `ros2 launch mini_pupper_bringup bringup.launch.py`
3. ****Test teleop** - Control the robot manually
4. ****Your touch** - Create custom launch file for shelf mode
5. *AMBITIOUS* **AMBITIOUS SAUCE** - Add shelf position awareness, safety limits

**Key files to examine:**
```
mini_pupper_bringup/
├── launch/
│   └── bringup.launch.py        # Main hardware launcher
└── config/
    └── hardware_params.yaml     # Servo/hardware config
```

**Learning goals:**
- How does ROS 2 launch system work?
- How are motors controlled via topics?
- What safety features exist?

---

#### 3. **stanford_controller** (Motion Control)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/stanford_controller  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/stanford_controller/`

**What it does:**
- Quadruped gait controller
- Converts velocity commands to leg movements
- Handles walking, trotting gaits

**Your tasks:**
1. ****Study the code** - How does the controller work?
2. ****Run vanilla version** - Test with keyboard teleop
3. ****Understand cmd_vel** - How are velocity commands structured?
4. ****Your touch** - Create position-based movement commands
5. *AMBITIOUS* **AMBITIOUS SAUCE** - Add smooth acceleration, position tracking

**Key files to examine:**
```
stanford_controller/
└── stanford_controller/
    ├── controller.py            # Main controller logic
    └── gait_controller.py       # Gait patterns
```

**Learning goals:**
- What is cmd_vel and how does it work?
- How do you convert "go to position X" into velocity commands?
- What's the relationship between velocity and position?

---

### Packages for Reference (Study, Don't Modify Yet)

#### 4. **mini_pupper_interfaces** (Message Definitions)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_interfaces  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/mini_pupper_interfaces/`

**What it provides:**
- Custom ROS 2 message types
- Service definitions
- Action definitions

**Your tasks:**
1. ****Study** - Look at existing message types
2. ****Your touch** - Create custom messages for your project:
   - `ProductQuery.msg` - Customer product requests
   - `ShelfPosition.msg` - Robot position on shelf
   - `GreetingState.msg` - Interaction state

**Learning goals:**
- How are custom ROS messages defined?
- When should you create new vs. use standard messages?

---

#### 5. **mini_pupper_navigation** (Future Reference)
**GitHub Location:** https://github.com/mangdangroboticsclub/mini_pupper_ros/tree/ros2-dev/mini_pupper_navigation  
**On Robot:** `~/ros2_ws/src/mini_pupper_ros/mini_pupper_navigation/`

**What it does:**
- Full Nav2 stack integration
- SLAM-based mapping
- Autonomous navigation

**Important note:1.DON'T USE THIS FOR PHASE 1-4**

**Why not?**
- Nav2 is overkill for a linear track
- You need to map semantic labels (product names) to positions first
- Nav2 only understands (x, y) coordinates, not "Doritos"

**When to use it:**
- Phase 5: Multi-aisle expansion
- When you have obstacles to avoid
- When you need path planning around furniture

**Your tasks:**
1. ****Study later** - Understand how Nav2 works for future phases
2. *AMBITIOUS* **AMBITIOUS** - Phase 5: Multi-aisle navigation

---

### ** Google API / LLM Integration

#### **apps-md-robots Repository**
**Location:** https://github.com/mangdangroboticsclub/apps-md-robots

**What it provides:**
- Examples of API integrations
- Cloud service connections
- Example voice/LLM interactions

**Your tasks:**
1. ****Clone and study** - `git clone https://github.com/mangdangroboticsclub/apps-md-robots`
2. ****Examine examples** - Look for LLM/API integration patterns
3. ****Test examples** - Try running example scripts
4. ****Your touch** - Adapt for product query parsing
5. *AMBITIOUS* **AMBITIOUS SAUCE** - Natural language product search, voice interaction

**Typical integration pattern:**
```python
# Customer says: "Where are the Doritos?"
customer_query = get_voice_input()  # or text input
parsed_product = llm_api.parse_product(customer_query)  # "doritos"
position = product_database.lookup(parsed_product)  # 0.4m
move_to_position(position)
say_response("I'll show you the Doritos!")
```

**Key integration points:**
- Voice input → LLM parsing → Product extraction
- LLM can handle variations: "chips", "Doritos", "nacho cheese chips"
- API calls should be asynchronous (don't block robot motion)

---

## Phase-by-Phase Implementation Roadmap

### Phase 1: Phase 1: Hardware Setup & Basic Motion
**Goal:** Get MP2 moving on a track

**Packages to use:**
- `mini_pupper_bringup` - Hardware control
- `stanford_controller` - Motion control

**Tasks:**
1. Build or acquire shelf track (1-2 meters)
2. Mount MP2 on track with ability to move forward/backward
3. Test basic bringup: `ros2 launch mini_pupper_bringup bringup.launch.py`
4. Test keyboard teleop: `ros2 run teleop_twist_keyboard teleop_twist_keyboard`
5. Verify robot can move along track safely
6. Measure track length and establish coordinate system

**Deliverable:** MP2 reliably moves on track via manual control

**Code to study:**
```bash
# Look at how bringup works
cat ~/ros2_ws/src/mini_pupper_ros/mini_pupper_bringup/launch/bringup.launch.py

# Understand cmd_vel topic
ros2 topic info /cmd_vel
ros2 topic echo /cmd_vel
```

---

### Phase 2: Phase 2: Product Database & Position Control
**Goal:** Create product-to-position mapping and move to positions

**Packages to use:**
- `stanford_controller` - Motion control
- `mini_pupper_interfaces` - Custom messages

**Tasks:**
1. Create simple product database (JSON or Python dict):
```python
PRODUCTS = {
    "doritos": 0.4,      # meters from home position
    "drinks": 1.2,
    "cheez-its": 0.8,
    "candy": 0.2,
    "chips": 0.5
}
```

2. Manually measure and verify positions on track
3. Create a position controller node:
```python
# Pseudocode structure
class PositionController:
    def __init__(self):
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel')
        self.current_position = 0.0
    
    def move_to_position(self, target):
        error = target - self.current_position
        while abs(error) > 0.05:  # 5cm tolerance
            velocity = calculate_velocity(error)
            self.publish_velocity(velocity)
            error = target - self.current_position
        self.stop()
```

4. Test moving to each product position
5. Implement "home" position (start of track)

**Deliverable:** Robot moves to specific positions on command

**Code pattern:**
```bash
# Create new package
cd ~/ros2_ws/src/mini_pupper_ros
ros2 pkg create --build-type ament_python bodega_cat_controller \
  --dependencies rclpy std_msgs geometry_msgs

# Build and test
cd ~/ros2_ws
colcon build --packages-select bodega_cat_controller
source install/setup.bash
ros2 run bodega_cat_controller position_controller
```

---

### Phase 2: Phase 3: Person Detection & Greeting
**Goal:** Detect customers and greet them

**Packages to use:**
- `mini_pupper_tracking` - Person detection
- Your custom greeting node

**Tasks:**
1. Study person detection in `mini_pupper_tracking`:
```bash
# Run tracking to see how it works
ros2 launch mini_pupper_tracking tracking.launch.py

# See what topics it publishes
ros2 topic list | grep tracking
ros2 topic echo /person_detected  # or similar
```

2. Create greeting behavior node:
```python
class GreetingNode:
    def __init__(self):
        self.detection_sub = self.create_subscription(
            PersonDetection, '/person_detected', self.on_person_detected)
        self.last_greeting_time = 0.0
        
    def on_person_detected(self, msg):
        # Don't spam greetings
        if time.time() - self.last_greeting_time > 30.0:
            self.say_greeting()
            self.last_greeting_time = time.time()
    
    def say_greeting(self):
        # Use audio playback or text-to-speech
        print("Hello! Ask me anything if you need help in the store.")
```

3. Integrate audio output (text-to-speech or pre-recorded):
```bash
# Test audio playback
sudo apt-get install espeak
espeak "Hello! Ask me anything if you need help in the store."
```

4. Test detection → greeting pipeline
5. Add greeting cooldown (don't greet same person repeatedly)

**Deliverable:** Robot detects people and greets them

****Your touch ideas:**
- Different greetings based on time of day
- Track number of customers
- Friendly animations (ears wiggle, etc.)

---

### Phase 4: Phase 4: Query Processing & Product Finding
**Goal:** Accept product queries and navigate to products

**Packages to use:**
- Your position controller (Phase 2)
- Your greeting node (Phase 3)
- `apps-md-robots` examples for parsing

**Tasks:**
1. Create query input system (start simple):
```python
# Option A: Manual input for testing
product = input("What product? ")

# Option B: Pre-defined test queries
test_queries = ["doritos", "drinks", "candy"]

# Option C (later): Voice or app input
```

2. Create query handler:
```python
class QueryHandler:
    def __init__(self):
        self.products = load_product_database()
        self.position_controller = PositionController()
        
    def handle_query(self, query):
        # Simple text matching
        product = self.parse_product(query)
        if product in self.products:
            position = self.products[product]
            self.position_controller.move_to_position(position)
            return f"I'll show you the {product}!"
        else:
            return "Sorry, I don't know where that is."
    
    def parse_product(self, query):
        # Simple keyword matching
        query_lower = query.lower()
        for product in self.products:
            if product in query_lower:
                return product
        return None
```

3. Integrate query → movement pipeline
4. Add response feedback ("Moving to Doritos...")
5. Test full interaction loop:
   - Detect person
   - Greet
   - Receive query
   - Navigate to product
   - Confirm arrival

**Deliverable:** Complete query-to-navigation pipeline

****Your touch ideas:**
- Fuzzy matching ("chips" → "doritos")
- Multiple product locations (tell customer both)
- "Out of stock" status

---

### Phase 5: Phase 5: AMBITIOUS SAUCE

These features are **stretch goals**. Only attempt if Phases 1-4 are solid.

#### *AMBITIOUS* Voice Input Integration
**Packages:** `apps-md-robots` examples

**Tasks:**
1. Study voice input examples from apps-md-robots
2. Integrate Google Speech-to-Text API or similar
3. Replace manual input with voice commands
4. Handle noisy environment (store background noise)

**Technical challenges:**
- Hotword detection ("Hey Bodega Cat")
- Noise cancellation
- API latency management

---

#### *AMBITIOUS**AMBITIOUS* LLM-Based Query Parsing
**Packages:** `apps-md-robots` examples

**Tasks:**
1. Study LLM integration from apps-md-robots:
```bash
git clone https://github.com/mangdangroboticsclub/apps-md-robots
cd apps-md-robots
# Look for API examples, conversation handlers
```

2. Integrate Google Gemini/ChatGPT for natural language:
```python
def parse_query_with_llm(customer_query):
    prompt = f"""
    Customer in a bodega asks: "{customer_query}"
    Available products: doritos, drinks, cheez-its, candy, chips
    
    Extract the product name they're asking for.
    Return only the product name, or "unknown".
    """
    
    response = llm_api.query(prompt)
    return response.strip().lower()
```

3. Handle complex queries:
   - "Where can I find something salty?"
   - "I need a snack"
   - "Do you have any Frito-Lay products?"

4. Add conversational memory:
   - "What about the spicy ones?"
   - "Show me the other chips"

**Technical challenges:**
- API costs (use free tier wisely)
- Response latency (5-10 seconds per query)
- Fallback when API unavailable

---

#### *AMBITIOUS**AMBITIOUS**AMBITIOUS* Multi-Aisle Navigation (NAV2)
**Packages:** `mini_pupper_navigation`

**Only attempt this if:**
- Phases 1-4 are rock solid
- You have multiple aisles built
- You understand Nav2 fundamentals

**Tasks:**
1. Study `mini_pupper_navigation` package thoroughly
2. Map the multi-aisle environment with SLAM
3. Create semantic layer over Nav2:
```python
# Map product names → Nav2 goals
PRODUCT_LOCATIONS = {
    "doritos": {"x": 1.2, "y": 0.3, "aisle": 1},
    "drinks": {"x": 2.5, "y": 0.8, "aisle": 2},
}

def navigate_to_product(product):
    location = PRODUCT_LOCATIONS[product]
    nav2_goal = create_goal_from_location(location)
    navigate_to_goal(nav2_goal)
```

4. Handle obstacles (customers, carts)
5. Dynamic re-routing

**This is VERY ambitious** - most retail robots use pre-defined paths, not full SLAM.

---

## Testing & Development Strategy

### Week-by-Week Suggested Timeline

**Week 1-2: Phase 1** - Hardware & Basic Motion
- Build track
- Get MP2 running
- Test movements

**Week 3-4: Phase 2** - Position Control
- Create database
- Implement position controller
- Test accuracy

**Week 5-6: Phase 3** - Person Detection
- Study tracking package
- Implement greeting
- Test interaction

**Week 7-8: Phase 4** - Query Pipeline
- Build query handler
- Integrate components
- Polish demo

**Week 9+ (if time): Phase 5** - SAUCE
- Pick ONE ambitious feature
- Prototype carefully
- Have fallback to Phase 4

---

## Code Organization

### Recommended Package Structure

Create your own package: `bodega_cat_mp2`

```
bodega_cat_mp2/
├── bodega_cat_mp2/
│   ├── __init__.py
│   ├── position_controller.py    # Phase 2
│   ├── greeting_node.py           # Phase 3
│   ├── query_handler.py           # Phase 4
│   ├── product_database.py        # Phase 2
│   └── voice_interface.py         # Phase 5 (ambitious)
├── launch/
│   ├── bodega_cat.launch.py       # Main launcher
│   └── test_position.launch.py    # Testing launcher
├── config/
│   ├── products.yaml               # Product database
│   └── greetings.yaml              # Greeting messages
├── data/
│   └── audio/                      # Greeting sound files
├── test/
│   ├── test_position_control.py
│   └── test_query_parsing.py
├── package.xml
└── setup.py
```

---

## Key Learning Resources

### Documentation to Read
1. **ROS 2 Humble Basics:**
   - https://docs.ros.org/en/humble/Tutorials.html
   - Focus on: Publishers, Subscribers, Launch files

2. **Mini Pupper Docs:**
   - https://minipupperdocs.readthedocs.io/
   - Understanding the robot

3. **Cmd_vel and Twist messages:**
   - http://docs.ros.org/en/humble/p/geometry_msgs/
   - How to control motion

### Code to Study First
```bash
# Person detection
~/ros2_ws/src/mini_pupper_ros/mini_pupper_tracking/

# Basic motion control  
~/ros2_ws/src/mini_pupper_ros/stanford_controller/

# Hardware bringup
~/ros2_ws/src/mini_pupper_ros/mini_pupper_bringup/

# API examples
git clone https://github.com/mangdangroboticsclub/apps-md-robots
```

---

## Success Criteria by Phase

### Phase 1
- [ ] MP2 moves on track via teleop
- [ ] Team understands cmd_vel
- [ ] Safe motion within track bounds

### Phase 2
- [ ] Product database with 5+ items
- [ ] Robot moves to position within 5cm accuracy
- [ ] Documented position measurements

### Phase 3
- [ ] Person detection triggers greeting
- [ ] Audio output works
- [ ] Cooldown prevents spam

### Phase 4 (MINIMUM VIABLE DEMO)
- [ ] Query → product lookup → navigation works
- [ ] At least 3 products findable
- [ ] Full interaction loop demonstrated

### Phase 5 *AMBITIOUS* (OPTIONAL AMBITIOUS)
- [ ] ONE advanced feature working
- [ ] Doesn't break Phase 4 functionality
- [ ] Clearly labeled as experimental
