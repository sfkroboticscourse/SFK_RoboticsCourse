#!/usr/bin/env python3
"""
AI Voice Control Node for Mini Pupper

A clean, minimal ROS2 node that:
1. Listens to voice input (using sounddevice - works on Mini Pupper!)
2. Uses Gemini to classify intent
3. Executes pre-programmed responses and movements
4. Publishes to /cmd_vel for ROS2 control

Dependencies:
    pip3 install google-genai sounddevice soundfile SpeechRecognition --break-system-packages

Usage:
    # Set your API key
    export GOOGLE_API_KEY="your-api-key-here"
    
    # Run the node
    ros2 run pupper_ai_voice ai_voice_control

Author: For Mini Pupper Teaching Lab
License: Apache 2.0
"""

import os
import sys
import time
import threading
import tempfile
import numpy as np
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String

# Audio recording with sounddevice (works on Mini Pupper!)
try:
    import sounddevice as sd
    import soundfile as sf
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    print("Warning: sounddevice not available. Install with: pip3 install sounddevice soundfile")

# Speech recognition (for Google STT)
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False
    print("Note: SpeechRecognition not available - install with: pip3 install SpeechRecognition")

# Google GenAI
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("Warning: google-genai not available. Install with: pip3 install google-genai")


# =============================================================================
# CONFIGURATION - Easy to modify for students!
# =============================================================================

# Audio settings (matching Mini Pupper's working config)
SAMPLE_RATE = 48000
CHANNELS = 1
RECORD_SECONDS = 4  # How long to listen for each command

# Intent configuration: (intent_name, response_text, linear_x, angular_z, duration)
INTENT_CONFIG = [
    # Movement commands
    ("move_forward",  "Okay, moving forward!",     0.15,  0.0,  2.0),
    ("move_backward", "Okay, backing up!",        -0.15,  0.0,  2.0),
    ("turn_left",     "Turning left!",             0.0,   0.5,  1.5),
    ("turn_right",    "Turning right!",            0.0,  -0.5,  1.5),
    
    # Combined movements
    ("come_here",     "Coming to you!",            0.15,  0.0,  3.0),
    ("go_away",       "Okay, going away!",        -0.15,  0.0,  3.0),
    
    # Spin/dance
    ("spin",          "Wheee, spinning!",          0.0,   1.0,  3.0),
    ("dance",         "Let's dance!",              0.0,   0.8,  4.0),
    
    # Stop
    ("stop",          "Stopping!",                 0.0,   0.0,  0.1),
    
    # Greeting (no movement)
    ("greeting",      "Hello! I'm Mini Pupper!",   0.0,   0.0,  0.0),
    ("goodbye",       "Goodbye, see you later!",   0.0,   0.0,  0.0),
]

SYSTEM_INTENTS = ["sleep", "wake", "help", "conversation"]

INTENT_ACTIONS = {intent: (response, lx, az, dur) 
                  for intent, response, lx, az, dur in INTENT_CONFIG}


# =============================================================================
# INTENT CLASSIFIER PROMPT
# =============================================================================

CLASSIFIER_PROMPT = """You are an intent classifier for a quadruped robot dog named Mini Pupper.
Classify the user's voice input into exactly ONE of these intents:

MOVEMENT:
- move_forward: "move forward", "go forward", "walk", "come", "come here", "go"
- move_backward: "move backward", "go back", "reverse", "back up"
- turn_left: "turn left", "go left", "left"
- turn_right: "turn right", "go right", "right"
- come_here: "come here", "come to me", "here boy"
- go_away: "go away", "leave", "shoo"

ACTIONS:
- spin: "spin", "spin around", "rotate"
- dance: "dance", "party", "boogie", "celebrate"
- stop: "stop", "halt", "freeze", "stay"

SOCIAL:
- greeting: "hello", "hi", "hey", "good morning", "good boy"
- goodbye: "goodbye", "bye", "see you", "later"

SYSTEM:
- sleep: "shut up", "be quiet", "sleep", "stop listening"
- wake: "wake up", "start listening", "hello robot"
- help: "help", "what can you do", "commands"
- conversation: anything else that doesn't fit above

User said: "{user_input}"

Respond with ONLY the intent name, nothing else."""


# =============================================================================
# ROS2 NODE
# =============================================================================

class AIVoiceControlNode(Node):
    """ROS2 node for AI-powered voice control of Mini Pupper."""
    
    def __init__(self):
        super().__init__('ai_voice_control')
        
        # Parameters
        self.declare_parameter('api_key', '')
        self.declare_parameter('sample_rate', SAMPLE_RATE)
        self.declare_parameter('record_seconds', RECORD_SECONDS)
        
        api_key = self.get_parameter('api_key').value
        if not api_key:
            api_key = os.environ.get('GOOGLE_API_KEY', '')
        
        self.sample_rate = self.get_parameter('sample_rate').value
        self.record_seconds = self.get_parameter('record_seconds').value
        
        # State
        self.is_listening = True
        
        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.speech_pub = self.create_publisher(String, '/ai/speech_text', 10)
        self.intent_pub = self.create_publisher(String, '/ai/intent', 10)
        self.speak_pub = self.create_publisher(String, '/ai/speak', 10)
        
        # Initialize Gemini
        self.genai_client = None
        if GENAI_AVAILABLE and api_key:
            try:
                self.genai_client = genai.Client(api_key=api_key)
                self.get_logger().info("Gemini AI initialized successfully!")
            except Exception as e:
                self.get_logger().error(f"Failed to initialize Gemini: {e}")
        else:
            self.get_logger().warn("Gemini not available - using keyword fallback")
        
        # Initialize speech recognizer
        self.recognizer = None
        if SR_AVAILABLE:
            self.recognizer = sr.Recognizer()
            self.get_logger().info("Speech recognition ready (Google STT)")
        
        # Set speaker volume
        os.system("amixer -c 0 sset 'Headphone' 100% 2>/dev/null || true")
        
        # Start listening thread
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        
        self.get_logger().info("=" * 50)
        self.get_logger().info("AI Voice Control Ready!")
        self.get_logger().info("Say 'help' to hear available commands")
        self.get_logger().info("=" * 50)
    
    def _record_audio(self) -> np.ndarray:
        """Record audio using sounddevice (works on Mini Pupper!)."""
        self.get_logger().info(f"🎤 Recording for {self.record_seconds}s... speak now!")
        try:
            audio = sd.rec(
                int(self.record_seconds * self.sample_rate),
                samplerate=self.sample_rate,
                channels=CHANNELS,
                dtype='int16'
            )
            sd.wait()
            return audio.flatten()
        except Exception as e:
            self.get_logger().error(f"Recording error: {e}")
            return np.array([], dtype='int16')
    
    def _recognize_speech(self, audio: np.ndarray) -> str:
        """Recognize speech using Google Speech Recognition."""
        if not self.recognizer or len(audio) == 0:
            return ""
        
        try:
            # Save to temp WAV file (SpeechRecognition needs a file)
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                temp_path = f.name
                sf.write(temp_path, audio, self.sample_rate)
            
            # Use SpeechRecognition to transcribe
            with sr.AudioFile(temp_path) as source:
                audio_data = self.recognizer.record(source)
            
            os.unlink(temp_path)
            
            text = self.recognizer.recognize_google(audio_data)
            return text.lower().strip()
            
        except sr.UnknownValueError:
            self.get_logger().debug("Could not understand audio")
            return ""
        except sr.RequestError as e:
            self.get_logger().error(f"Google STT error: {e}")
            return ""
        except Exception as e:
            self.get_logger().error(f"Recognition error: {e}")
            return ""
    
    def _listen_loop(self):
        """Background thread for continuous listening."""
        if not AUDIO_AVAILABLE:
            self.get_logger().error("Audio not available!")
            return
        
        if not SR_AVAILABLE:
            self.get_logger().error("Speech recognition not available!")
            return
        
        # Wait a moment for node to fully initialize
        time.sleep(2)
        
        while rclpy.ok():
            if not self.is_listening:
                time.sleep(0.5)
                continue
            
            try:
                # Record audio
                audio = self._record_audio()
                if len(audio) == 0:
                    continue
                
                # Recognize speech
                text = self._recognize_speech(audio)
                
                if not text:
                    self.get_logger().info("(no speech detected)")
                    continue
                
                self.get_logger().info(f"Heard: '{text}'")
                
                # Publish what we heard
                msg = String()
                msg.data = text
                self.speech_pub.publish(msg)
                
                # Process the command
                self._process_voice_input(text)
                
            except Exception as e:
                self.get_logger().error(f"Listen error: {e}")
                time.sleep(1)
    
    def _process_voice_input(self, text: str):
        """Process voice input and execute appropriate action."""
        intent = self._classify_intent(text)
        self.get_logger().info(f"Intent: {intent}")
        
        # Publish intent
        msg = String()
        msg.data = intent
        self.intent_pub.publish(msg)
        
        # Handle system intents
        if intent == "sleep":
            self.is_listening = False
            self._speak("Going to sleep. Say 'wake up' to wake me.")
            return
        elif intent == "wake":
            self.is_listening = True
            self._speak("I'm awake and listening!")
            return
        elif intent == "help":
            self._speak("I can move forward, backward, turn left, turn right, spin, dance, and stop.")
            return
        elif intent == "conversation":
            response = self._get_conversation_response(text)
            self._speak(response)
            return
        
        # Handle movement intents
        if intent in INTENT_ACTIONS:
            response, linear_x, angular_z, duration = INTENT_ACTIONS[intent]
            self._speak(response)
            self._execute_movement(linear_x, angular_z, duration)
        else:
            self._speak("I'm not sure what you want. Try saying 'help'.")
    
    def _classify_intent(self, text: str) -> str:
        """Use Gemini to classify the intent, with keyword fallback."""
        if self.genai_client:
            try:
                prompt = CLASSIFIER_PROMPT.format(user_input=text)
                response = self.genai_client.models.generate_content(
                    model="gemini-2.0-flash-lite",
                    contents=prompt
                )
                intent = response.text.strip().lower()
                if intent in INTENT_ACTIONS or intent in SYSTEM_INTENTS:
                    return intent
            except Exception as e:
                self.get_logger().warn(f"Gemini classification failed: {e}")
        
        return self._keyword_classify(text)
    
    def _keyword_classify(self, text: str) -> str:
        """Simple keyword-based intent classification as fallback."""
        text = text.lower()
        
        if any(w in text for w in ["forward", "come here", "walk"]):
            return "move_forward"
        elif any(w in text for w in ["backward", "back", "reverse"]):
            return "move_backward"
        elif "left" in text:
            return "turn_left"
        elif "right" in text:
            return "turn_right"
        elif any(w in text for w in ["spin", "rotate"]):
            return "spin"
        elif any(w in text for w in ["dance", "party"]):
            return "dance"
        elif any(w in text for w in ["stop", "halt", "freeze"]):
            return "stop"
        elif any(w in text for w in ["hello", "hi", "hey"]):
            return "greeting"
        elif any(w in text for w in ["bye", "goodbye"]):
            return "goodbye"
        elif any(w in text for w in ["shut up", "quiet", "sleep"]):
            return "sleep"
        elif any(w in text for w in ["wake", "listen"]):
            return "wake"
        elif any(w in text for w in ["help", "command"]):
            return "help"
        else:
            return "conversation"
    
    def _get_conversation_response(self, text: str) -> str:
        """Get a conversational response from Gemini."""
        if not self.genai_client:
            return "I'm just a simple robot. Try 'help' for commands."
        
        try:
            prompt = f"""You are Mini Pupper, a friendly quadruped robot dog. 
Give a short, cheerful response (1-2 sentences max) to: "{text}"
Be playful and dog-like!"""
            
            response = self.genai_client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            self.get_logger().error(f"Conversation error: {e}")
            return "Woof! I didn't catch that."
    
    def _speak(self, text: str):
        """Output speech - publishes to /ai/speak for TTS node."""
        self.get_logger().info(f"🔊 {text}")
        msg = String()
        msg.data = text
        self.speak_pub.publish(msg)
    
    def _execute_movement(self, linear_x: float, angular_z: float, duration: float):
        """Execute a movement command."""
        if duration <= 0:
            return
        
        self.get_logger().info(f"Moving: linear={linear_x}, angular={angular_z}, duration={duration}s")
        
        twist = Twist()
        twist.linear.x = linear_x
        twist.angular.z = angular_z
        
        start_time = time.time()
        rate = 20  # Hz
        while time.time() - start_time < duration:
            self.cmd_vel_pub.publish(twist)
            time.sleep(1.0 / rate)
        
        self.cmd_vel_pub.publish(Twist())
        self.get_logger().info("Movement complete")


def main(args=None):
    rclpy.init(args=args)
    
    if not AUDIO_AVAILABLE:
        print("ERROR: sounddevice not installed!")
        print("Run: pip3 install sounddevice soundfile --break-system-packages")
        return
    
    if not SR_AVAILABLE:
        print("ERROR: SpeechRecognition not installed!")
        print("Run: pip3 install SpeechRecognition --break-system-packages")
        return
    
    node = AIVoiceControlNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cmd_vel_pub.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
