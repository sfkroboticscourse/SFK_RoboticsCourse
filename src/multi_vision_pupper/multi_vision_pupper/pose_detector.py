#!/usr/bin/env python3
"""
Pose Detection Node for Mini Pupper

Task 4: Pose detection for directional control.
Uses OpenCV's DNN module to run a pose estimation model.

Control Logic (based on arm positions):
- Both arms up: Move forward
- Both arms down: Stop
- Left arm up: Turn left
- Right arm up: Turn right
- Arms pointing forward: Move forward
- T-pose: Stop and wait

This uses the lightweight OpenPose or MoveNet model running on CPU.

Topics:
    Subscribes:
        /camera/image_raw (sensor_msgs/Image): Camera frames
    
    Publishes:
        /vision/pose_detected (std_msgs/String): Pose info (JSON)
        /vision/visualization (sensor_msgs/Image): Skeleton overlay (optional)
        /cmd_vel (geometry_msgs/Twist): Velocity commands

Parameters:
    visualization (bool): Enable visualization output
    control_enabled (bool): Enable movement control
    model_type (str): 'mediapipe' or 'opencv_pose' (default: mediapipe)
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from geometry_msgs.msg import Twist
from cv_bridge import CvBridge
import cv2
import numpy as np
import json

# Try to import MediaPipe (much better than OpenCV pose on RPi)
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("Warning: MediaPipe not available, pose detection will be limited")


class PoseDetector(Node):
    """ROS2 node for pose detection and gesture-based control."""
    
    # MediaPipe pose landmark indices
    NOSE = 0
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24
    
    def __init__(self):
        super().__init__('pose_detector')
        
        # Parameters
        self.declare_parameter('visualization', False)
        self.declare_parameter('control_enabled', True)
        self.declare_parameter('forward_speed', 0.15)
        self.declare_parameter('turn_speed', 0.6)
        self.declare_parameter('detection_confidence', 0.5)
        self.declare_parameter('tracking_confidence', 0.5)
        
        self.visualization = self.get_parameter('visualization').value
        self.control_enabled = self.get_parameter('control_enabled').value
        self.forward_speed = self.get_parameter('forward_speed').value
        self.turn_speed = self.get_parameter('turn_speed').value
        self.detection_confidence = self.get_parameter('detection_confidence').value
        self.tracking_confidence = self.get_parameter('tracking_confidence').value
        
        # CV Bridge
        self.bridge = CvBridge()
        
        # Initialize pose detector
        self.pose = None
        self.mp_pose = None
        self.mp_drawing = None
        self._init_pose_detector()
        
        # Subscribers
        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10)
        
        # Publishers
        self.pose_pub = self.create_publisher(String, '/vision/pose_detected', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        if self.visualization:
            self.viz_pub = self.create_publisher(Image, '/vision/visualization', 10)
        
        self.get_logger().info(
            f"Pose detector started. MediaPipe={MEDIAPIPE_AVAILABLE}, "
            f"control={self.control_enabled}")
    
    def _init_pose_detector(self):
        """Initialize MediaPipe Pose."""
        if MEDIAPIPE_AVAILABLE:
            self.mp_pose = mp.solutions.pose
            self.mp_drawing = mp.solutions.drawing_utils
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=0,  # 0 = lite, 1 = full, 2 = heavy
                enable_segmentation=False,
                min_detection_confidence=self.detection_confidence,
                min_tracking_confidence=self.tracking_confidence
            )
            self.get_logger().info("MediaPipe Pose initialized")
        else:
            self.get_logger().warn("MediaPipe not available, pose detection disabled")
    
    def get_landmark_coords(self, landmarks, idx, width, height):
        """Get pixel coordinates for a landmark."""
        if landmarks is None or idx >= len(landmarks.landmark):
            return None
        lm = landmarks.landmark[idx]
        if lm.visibility < 0.5:
            return None
        return (int(lm.x * width), int(lm.y * height))
    
    def analyze_pose(self, landmarks, width, height):
        """
        Analyze pose landmarks and determine gesture/command.
        
        Returns:
            gesture (str): Detected gesture name
            command (dict): {'linear_x': float, 'angular_z': float}
        """
        if landmarks is None:
            return "NO_POSE", {'linear_x': 0.0, 'angular_z': 0.0}
        
        # Get key landmarks
        nose = self.get_landmark_coords(landmarks, self.NOSE, width, height)
        left_shoulder = self.get_landmark_coords(landmarks, self.LEFT_SHOULDER, width, height)
        right_shoulder = self.get_landmark_coords(landmarks, self.RIGHT_SHOULDER, width, height)
        left_wrist = self.get_landmark_coords(landmarks, self.LEFT_WRIST, width, height)
        right_wrist = self.get_landmark_coords(landmarks, self.RIGHT_WRIST, width, height)
        left_elbow = self.get_landmark_coords(landmarks, self.LEFT_ELBOW, width, height)
        right_elbow = self.get_landmark_coords(landmarks, self.RIGHT_ELBOW, width, height)
        
        # Check if we have enough landmarks
        if not all([left_shoulder, right_shoulder, left_wrist, right_wrist]):
            return "INCOMPLETE", {'linear_x': 0.0, 'angular_z': 0.0}
        
        # Calculate shoulder center
        shoulder_y = (left_shoulder[1] + right_shoulder[1]) // 2
        
        # Determine arm positions
        left_arm_up = left_wrist[1] < left_shoulder[1] - 50  # Wrist above shoulder
        right_arm_up = right_wrist[1] < right_shoulder[1] - 50
        left_arm_down = left_wrist[1] > left_shoulder[1] + 50  # Wrist below shoulder
        right_arm_down = right_wrist[1] > right_shoulder[1] + 50
        
        # T-pose detection (arms horizontal)
        left_arm_horizontal = abs(left_wrist[1] - left_shoulder[1]) < 50
        right_arm_horizontal = abs(right_wrist[1] - right_shoulder[1]) < 50
        t_pose = left_arm_horizontal and right_arm_horizontal
        
        # Determine gesture and command
        gesture = "UNKNOWN"
        command = {'linear_x': 0.0, 'angular_z': 0.0}
        
        if t_pose:
            gesture = "T_POSE_STOP"
            # Stop
        elif left_arm_up and right_arm_up:
            gesture = "BOTH_ARMS_UP_FORWARD"
            command['linear_x'] = self.forward_speed
        elif left_arm_down and right_arm_down:
            gesture = "ARMS_DOWN_STOP"
            # Stop
        elif left_arm_up and not right_arm_up:
            gesture = "LEFT_ARM_UP_TURN_LEFT"
            command['angular_z'] = self.turn_speed
        elif right_arm_up and not left_arm_up:
            gesture = "RIGHT_ARM_UP_TURN_RIGHT"
            command['angular_z'] = -self.turn_speed
        elif left_arm_up and right_arm_down:
            gesture = "LEFT_UP_RIGHT_DOWN_TURN_LEFT"
            command['angular_z'] = self.turn_speed
        elif right_arm_up and left_arm_down:
            gesture = "RIGHT_UP_LEFT_DOWN_TURN_RIGHT"
            command['angular_z'] = -self.turn_speed
        else:
            gesture = "NEUTRAL"
        
        return gesture, command
    
    def image_callback(self, msg):
        """Process incoming camera frame."""
        if self.pose is None:
            return
        
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
        except Exception as e:
            self.get_logger().error(f"Failed to convert image: {e}")
            return
        
        height, width = frame.shape[:2]
        
        # Process with MediaPipe
        results = self.pose.process(frame)
        
        # Analyze pose
        landmarks = results.pose_landmarks
        gesture, command = self.analyze_pose(landmarks, width, height)
        
        # Build result message
        result = {
            'detected': landmarks is not None,
            'gesture': gesture,
            'command': command
        }
        
        if landmarks is not None:
            # Include some key landmark positions
            result['landmarks'] = {}
            for name, idx in [('nose', self.NOSE), 
                              ('left_wrist', self.LEFT_WRIST),
                              ('right_wrist', self.RIGHT_WRIST)]:
                coords = self.get_landmark_coords(landmarks, idx, width, height)
                if coords:
                    result['landmarks'][name] = coords
        
        # Publish results
        result_msg = String()
        result_msg.data = json.dumps(result)
        self.pose_pub.publish(result_msg)
        
        # Publish velocity command
        twist = Twist()
        if self.control_enabled:
            twist.linear.x = command['linear_x']
            twist.angular.z = command['angular_z']
        self.cmd_vel_pub.publish(twist)
        
        if landmarks is not None:
            self.get_logger().info(
                f"Pose detected: {gesture}, vx={command['linear_x']:.2f}, "
                f"wz={command['angular_z']:.2f}")
        
        # Visualization
        if self.visualization:
            viz_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            if landmarks is not None:
                # Draw pose skeleton
                self.mp_drawing.draw_landmarks(
                    viz_frame,
                    landmarks,
                    self.mp_pose.POSE_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
                    self.mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
                )
            
            # Status text
            cv2.putText(viz_frame, f"Gesture: {gesture}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            if self.control_enabled:
                cmd_text = f"Cmd: vx={command['linear_x']:.2f}, wz={command['angular_z']:.2f}"
                cv2.putText(viz_frame, cmd_text, (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Instructions
            instructions = [
                "Both arms UP = Forward",
                "Left arm UP = Turn Left",
                "Right arm UP = Turn Right",
                "T-Pose/Arms DOWN = Stop"
            ]
            for i, text in enumerate(instructions):
                cv2.putText(viz_frame, text, (10, height - 80 + i * 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
            
            # Publish
            try:
                viz_msg = self.bridge.cv2_to_imgmsg(viz_frame, encoding='bgr8')
                viz_msg.header = msg.header
                self.viz_pub.publish(viz_msg)
            except Exception as e:
                self.get_logger().error(f"Failed to publish visualization: {e}")
    
    def destroy_node(self):
        """Clean up resources."""
        if self.pose is not None:
            self.pose.close()
        twist = Twist()
        self.cmd_vel_pub.publish(twist)
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = PoseDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
