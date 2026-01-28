#!/usr/bin/env python3
"""
Simple Text-to-Speech Node for Mini Pupper

Subscribes to /ai/speak and plays audio through speakers.
Uses pyttsx3 (offline) or gTTS (online) for speech synthesis.

Dependencies:
    pip3 install pyttsx3 --break-system-packages
    # OR for better quality (requires internet):
    pip3 install gTTS pygame --break-system-packages

Usage:
    ros2 run pupper_ai_voice tts_node
"""

import os
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

# Try pyttsx3 first (offline)
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

# Try gTTS as backup (online, better quality)
try:
    from gtts import gTTS
    import pygame
    import io
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False


class TTSNode(Node):
    """Simple text-to-speech ROS2 node."""
    
    def __init__(self):
        super().__init__('tts_node')
        
        # Parameters
        self.declare_parameter('engine', 'auto')  # 'pyttsx3', 'gtts', or 'auto'
        self.declare_parameter('rate', 150)  # Speech rate for pyttsx3
        self.declare_parameter('volume', 1.0)
        
        engine_pref = self.get_parameter('engine').value
        self.rate = self.get_parameter('rate').value
        self.volume = self.get_parameter('volume').value
        
        # Initialize TTS engine
        self.engine = None
        self.use_gtts = False
        
        if engine_pref == 'gtts' and GTTS_AVAILABLE:
            self.use_gtts = True
            pygame.mixer.init()
            self.get_logger().info("Using gTTS (online, high quality)")
        elif engine_pref == 'pyttsx3' and PYTTSX3_AVAILABLE:
            self._init_pyttsx3()
        elif engine_pref == 'auto':
            if PYTTSX3_AVAILABLE:
                self._init_pyttsx3()
            elif GTTS_AVAILABLE:
                self.use_gtts = True
                pygame.mixer.init()
                self.get_logger().info("Using gTTS (online)")
            else:
                self.get_logger().error("No TTS engine available!")
        
        # Subscriber
        self.subscription = self.create_subscription(
            String,
            '/ai/speak',
            self.speak_callback,
            10
        )
        
        self.get_logger().info("TTS Node ready - listening on /ai/speak")
    
    def _init_pyttsx3(self):
        """Initialize pyttsx3 engine."""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)
            self.get_logger().info("Using pyttsx3 (offline)")
        except Exception as e:
            self.get_logger().error(f"Failed to init pyttsx3: {e}")
    
    def speak_callback(self, msg: String):
        """Handle incoming speech requests."""
        text = msg.data.strip()
        if not text:
            return
        
        self.get_logger().info(f"Speaking: {text}")
        
        if self.use_gtts and GTTS_AVAILABLE:
            self._speak_gtts(text)
        elif self.engine:
            self._speak_pyttsx3(text)
        else:
            self.get_logger().warn(f"No TTS engine - would say: {text}")
    
    def _speak_pyttsx3(self, text: str):
        """Speak using pyttsx3."""
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            self.get_logger().error(f"pyttsx3 error: {e}")
    
    def _speak_gtts(self, text: str):
        """Speak using gTTS."""
        try:
            tts = gTTS(text=text, lang='en')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            
            pygame.mixer.music.load(fp, 'mp3')
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as e:
            self.get_logger().error(f"gTTS error: {e}")


def main(args=None):
    rclpy.init(args=args)
    
    if not PYTTSX3_AVAILABLE and not GTTS_AVAILABLE:
        print("ERROR: No TTS engine available!")
        print("Install one of:")
        print("  pip3 install pyttsx3 --break-system-packages")
        print("  pip3 install gTTS pygame --break-system-packages")
        return
    
    node = TTSNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
