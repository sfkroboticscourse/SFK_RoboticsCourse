#!/usr/bin/env python3
"""
Keyboard Command Node for Mini Pupper AI Demo

For testing without a microphone - type commands instead of speaking.
Uses the same intent classification as the voice node.

Usage:
    ros2 run pupper_ai_voice keyboard_control
    
    Then type commands like:
    > move forward
    > dance
    > help
    > quit
"""

import os
import sys
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String

# Google GenAI
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


# Same configuration as voice node
INTENT_CONFIG = [
    ("move_forward",  "Okay, moving forward!",     0.15,  0.0,  2.0),
    ("move_backward", "Okay, backing up!",        -0.15,  0.0,  2.0),
    ("turn_left",     "Turning left!",             0.0,   0.5,  1.5),
    ("turn_right",    "Turning right!",            0.0,  -0.5,  1.5),
    ("come_here",     "Coming to you!",            0.15,  0.0,  3.0),
    ("go_away",       "Okay, going away!",        -0.15,  0.0,  3.0),
    ("spin",          "Wheee, spinning!",          0.0,   1.0,  3.0),
    ("dance",         "Let's dance!",              0.0,   0.8,  4.0),
    ("stop",          "Stopping!",                 0.0,   0.0,  0.1),
    ("look_left",     "Looking left!",             0.0,   0.3,  0.5),
    ("look_right",    "Looking right!",            0.0,  -0.3,  0.5),
    ("greeting",      "Hello! I'm Mini Pupper!",   0.0,   0.0,  0.0),
    ("goodbye",       "Goodbye, see you later!",   0.0,   0.0,  0.0),
]

INTENT_ACTIONS = {intent: (response, lx, az, dur) 
                  for intent, response, lx, az, dur in INTENT_CONFIG}

CLASSIFIER_PROMPT = """You are an intent classifier for a quadruped robot dog named Mini Pupper.
Classify the user's input into exactly ONE of these intents:

MOVEMENT:
- move_forward: "move forward", "go forward", "walk", "come", "come here"
- move_backward: "move backward", "go back", "reverse", "back up"
- turn_left: "turn left", "go left", "left"
- turn_right: "turn right", "go right", "right"
- come_here: "come here", "come to me"
- go_away: "go away", "leave"

ACTIONS:
- spin: "spin", "spin around"
- dance: "dance", "party"
- stop: "stop", "halt", "freeze"

SOCIAL:
- greeting: "hello", "hi", "hey"
- goodbye: "goodbye", "bye"

SYSTEM:
- help: "help", "commands"
- conversation: anything else

User said: "{user_input}"

Respond with ONLY the intent name."""


class KeyboardControlNode(Node):
    """Keyboard-based control for testing."""
    
    def __init__(self):
        super().__init__('keyboard_control')
        
        # Get API key
        api_key = os.environ.get('GOOGLE_API_KEY', '')
        
        # Publisher
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Initialize Gemini
        self.genai_client = None
        if GENAI_AVAILABLE and api_key:
            try:
                self.genai_client = genai.Client(api_key=api_key)
                self.get_logger().info("Gemini AI initialized!")
            except Exception as e:
                self.get_logger().warn(f"Gemini init failed: {e}")
        
        self.get_logger().info("=" * 50)
        self.get_logger().info("Keyboard Control Ready!")
        self.get_logger().info("Type commands and press Enter")
        self.get_logger().info("Type 'help' for commands, 'quit' to exit")
        self.get_logger().info("=" * 50)
    
    def classify_intent(self, text: str) -> str:
        """Classify intent using Gemini or keywords."""
        if self.genai_client:
            try:
                prompt = CLASSIFIER_PROMPT.format(user_input=text)
                response = self.genai_client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                intent = response.text.strip().lower()
                if intent in INTENT_ACTIONS or intent in ["help", "conversation"]:
                    return intent
            except Exception as e:
                self.get_logger().warn(f"Gemini error: {e}")
        
        # Keyword fallback
        text = text.lower()
        if "forward" in text or "come" in text:
            return "move_forward"
        elif "backward" in text or "back" in text:
            return "move_backward"
        elif "left" in text:
            return "turn_left"
        elif "right" in text:
            return "turn_right"
        elif "spin" in text:
            return "spin"
        elif "dance" in text:
            return "dance"
        elif "stop" in text:
            return "stop"
        elif "hello" in text or "hi" in text:
            return "greeting"
        elif "help" in text:
            return "help"
        else:
            return "conversation"
    
    def execute_command(self, text: str):
        """Process and execute a command."""
        intent = self.classify_intent(text)
        print(f"  Intent: {intent}")
        
        if intent == "help":
            print("\n  Available commands:")
            print("  - move forward / backward")
            print("  - turn left / right")
            print("  - spin / dance / stop")
            print("  - hello / goodbye")
            print("  - quit (to exit)\n")
            return
        
        if intent == "conversation":
            if self.genai_client:
                try:
                    response = self.genai_client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=f"You are Mini Pupper, a friendly robot dog. Short response to: {text}"
                    )
                    print(f"  🐕 {response.text.strip()}")
                except:
                    print("  🐕 Woof! I'm just a simple robot.")
            else:
                print("  🐕 Woof! Try 'help' for commands.")
            return
        
        if intent in INTENT_ACTIONS:
            response, linear_x, angular_z, duration = INTENT_ACTIONS[intent]
            print(f"  🔊 {response}")
            
            if duration > 0:
                self.execute_movement(linear_x, angular_z, duration)
    
    def execute_movement(self, linear_x: float, angular_z: float, duration: float):
        """Execute movement."""
        import time
        
        twist = Twist()
        twist.linear.x = linear_x
        twist.angular.z = angular_z
        
        print(f"  Moving for {duration}s...")
        start = time.time()
        while time.time() - start < duration:
            self.cmd_vel_pub.publish(twist)
            time.sleep(0.05)
        
        self.cmd_vel_pub.publish(Twist())
        print("  Done!")
    
    def run_interactive(self):
        """Run interactive command loop."""
        try:
            while True:
                try:
                    text = input("\n> ").strip()
                    if not text:
                        continue
                    if text.lower() in ['quit', 'exit', 'q']:
                        print("Goodbye!")
                        break
                    self.execute_command(text)
                except EOFError:
                    break
        finally:
            self.cmd_vel_pub.publish(Twist())


def main(args=None):
    rclpy.init(args=args)
    node = KeyboardControlNode()
    
    try:
        node.run_interactive()
    except KeyboardInterrupt:
        print("\nInterrupted")
    finally:
        node.cmd_vel_pub.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
