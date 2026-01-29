#!/usr/bin/env python3
"""
Pose Behavior Tracker for Mini Pupper (OAK-D Camera)

An advanced MediaPipe Pose-based behavior tracking node that can:
1. Detect and classify poses (standing, sitting, walking, etc.)
2. Track exercises (squats, jumping jacks, arm raises)
3. Recognize gestures for robot control
4. Analyze body movement patterns over time

Students can easily add new behaviors by defining them in the BEHAVIORS config.

Topics:
    Subscribes:
        /camera/image_raw (sensor_msgs/Image): Camera frames
    
    Publishes:
        /vision/pose_landmarks (std_msgs/String): All 33 landmarks as JSON
        /vision/behavior (std_msgs/String): Detected behavior/activity
        /vision/exercise_count (std_msgs/Int32): Exercise repetition counter
        /vision/visualization (sensor_msgs/Image): Annotated frame
        /cmd_vel (geometry_msgs/Twist): Robot control commands

Parameters:
    visualization (bool): Enable visualization output
    control_enabled (bool): Enable robot movement control
    behavior_mode (str): 'gesture_control', 'exercise_counter', 'activity_tracker'
    exercise_type (str): 'squats', 'jumping_jacks', 'arm_raises'
    
Dependencies:
    pip3 install mediapipe --break-system-packages

Author: Mini Pupper Teaching Lab
License: Apache 2.0
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String, Int32
from geometry_msgs.msg import Twist
from cv_bridge import CvBridge
import cv2
import numpy as np
import json
import math
from collections import deque
from enum import Enum

# MediaPipe
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("Warning: MediaPipe not available. Install with: pip3 install mediapipe")


# =============================================================================
# LANDMARK INDICES (MediaPipe Pose 33 landmarks)
# =============================================================================
class PoseLandmark(Enum):
    NOSE = 0
    LEFT_EYE_INNER = 1
    LEFT_EYE = 2
    LEFT_EYE_OUTER = 3
    RIGHT_EYE_INNER = 4
    RIGHT_EYE = 5
    RIGHT_EYE_OUTER = 6
    LEFT_EAR = 7
    RIGHT_EAR = 8
    MOUTH_LEFT = 9
    MOUTH_RIGHT = 10
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_PINKY = 17
    RIGHT_PINKY = 18
    LEFT_INDEX = 19
    RIGHT_INDEX = 20
    LEFT_THUMB = 21
    RIGHT_THUMB = 22
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28
    LEFT_HEEL = 29
    RIGHT_HEEL = 30
    LEFT_FOOT_INDEX = 31
    RIGHT_FOOT_INDEX = 32


# =============================================================================
# BEHAVIOR CONFIGURATION - Students can easily add new behaviors here!
# =============================================================================

# Gesture -> Robot Control mapping
GESTURE_CONTROLS = {
    'BOTH_ARMS_UP': {'linear_x': 0.15, 'angular_z': 0.0, 'description': 'Move forward'},
    'BOTH_ARMS_DOWN': {'linear_x': 0.0, 'angular_z': 0.0, 'description': 'Stop'},
    'LEFT_ARM_UP': {'linear_x': 0.0, 'angular_z': 0.5, 'description': 'Turn left'},
    'RIGHT_ARM_UP': {'linear_x': 0.0, 'angular_z': -0.5, 'description': 'Turn right'},
    'T_POSE': {'linear_x': 0.0, 'angular_z': 0.0, 'description': 'Stop'},
    'ARMS_FORWARD': {'linear_x': 0.15, 'angular_z': 0.0, 'description': 'Move forward'},
    'WAVE_LEFT': {'linear_x': 0.0, 'angular_z': 0.3, 'description': 'Slow turn left'},
    'WAVE_RIGHT': {'linear_x': 0.0, 'angular_z': -0.3, 'description': 'Slow turn right'},
    'CROUCH': {'linear_x': -0.1, 'angular_z': 0.0, 'description': 'Move backward'},
}

# Activity definitions
ACTIVITIES = ['STANDING', 'SITTING', 'WALKING', 'JUMPING', 'UNKNOWN']


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def calculate_angle(p1, p2, p3):
    """
    Calculate angle at p2 given three points.
    Returns angle in degrees.
    """
    if any(p is None for p in [p1, p2, p3]):
        return None
    
    v1 = np.array([p1[0] - p2[0], p1[1] - p2[1]])
    v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])
    
    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
    angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
    return np.degrees(angle)


def get_distance(p1, p2):
    """Calculate Euclidean distance between two points."""
    if p1 is None or p2 is None:
        return None
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


# =============================================================================
# POSE BEHAVIOR TRACKER NODE
# =============================================================================

class PoseBehaviorTracker(Node):
    """ROS2 node for advanced pose behavior tracking."""
    
    def __init__(self):
        super().__init__('pose_behavior_tracker')
        
        # Parameters
        self.declare_parameter('visualization', True)
        self.declare_parameter('control_enabled', True)
        self.declare_parameter('forward_speed', 0.15)
        self.declare_parameter('turn_speed', 0.5)
        self.declare_parameter('detection_confidence', 0.5)
        self.declare_parameter('tracking_confidence', 0.5)
        
        # Behavior mode: 'gesture_control', 'exercise_counter', 'activity_tracker'
        self.declare_parameter('behavior_mode', 'gesture_control')
        
        # Exercise tracking
        self.declare_parameter('exercise_type', 'squats')  # squats, jumping_jacks, arm_raises
        
        # Commitment mode (for smoother robot control)
        self.declare_parameter('commitment_mode', True)
        self.declare_parameter('action_duration', 0.5)
        self.declare_parameter('pause_duration', 0.3)
        
        # Get parameters
        self.visualization = self.get_parameter('visualization').value
        self.control_enabled = self.get_parameter('control_enabled').value
        self.forward_speed = self.get_parameter('forward_speed').value
        self.turn_speed = self.get_parameter('turn_speed').value
        self.behavior_mode = self.get_parameter('behavior_mode').value
        self.exercise_type = self.get_parameter('exercise_type').value
        self.commitment_mode = self.get_parameter('commitment_mode').value
        self.action_duration = self.get_parameter('action_duration').value
        self.pause_duration = self.get_parameter('pause_duration').value
        
        # State
        self.state = 'ASSESS'
        self.state_start_time = self.get_clock().now()
        self.current_action = Twist()
        self.current_gesture = 'NONE'
        
        # Exercise counting state
        self.exercise_count = 0
        self.exercise_state = 'UP'  # UP or DOWN for counting reps
        
        # Activity tracking (rolling window)
        self.pose_history = deque(maxlen=30)  # ~1 second of poses at 30fps
        self.current_activity = 'UNKNOWN'
        
        # CV Bridge
        self.bridge = CvBridge()
        
        # Initialize MediaPipe Pose
        self.pose = None
        self.mp_pose = None
        self.mp_drawing = None
        self._init_mediapipe()
        
        # Subscribers
        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10)
        
        # Publishers
        self.landmarks_pub = self.create_publisher(String, '/vision/pose_landmarks', 10)
        self.behavior_pub = self.create_publisher(String, '/vision/behavior', 10)
        self.exercise_pub = self.create_publisher(Int32, '/vision/exercise_count', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        if self.visualization:
            self.viz_pub = self.create_publisher(Image, '/vision/visualization', 10)
        
        self.get_logger().info("=" * 60)
        self.get_logger().info("Pose Behavior Tracker Started!")
        self.get_logger().info(f"  Mode: {self.behavior_mode}")
        if self.behavior_mode == 'exercise_counter':
            self.get_logger().info(f"  Exercise: {self.exercise_type}")
        self.get_logger().info(f"  Control enabled: {self.control_enabled}")
        self.get_logger().info("=" * 60)
    
    def _init_mediapipe(self):
        """Initialize MediaPipe Pose."""
        if not MEDIAPIPE_AVAILABLE:
            self.get_logger().error("MediaPipe not available!")
            return
        
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,  # 0=lite, 1=full, 2=heavy
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=self.get_parameter('detection_confidence').value,
            min_tracking_confidence=self.get_parameter('tracking_confidence').value
        )
        self.get_logger().info("MediaPipe Pose initialized (33 landmarks)")
    
    def get_landmark(self, landmarks, idx, width, height):
        """Get pixel coordinates for a landmark."""
        if landmarks is None:
            return None
        lm = landmarks.landmark[idx]
        if lm.visibility < 0.5:
            return None
        return (int(lm.x * width), int(lm.y * height))
    
    def get_all_landmarks(self, landmarks, width, height):
        """Get all 33 landmarks as a dictionary."""
        if landmarks is None:
            return None
        
        result = {}
        for landmark in PoseLandmark:
            lm = landmarks.landmark[landmark.value]
            result[landmark.name] = {
                'x': int(lm.x * width),
                'y': int(lm.y * height),
                'z': lm.z,
                'visibility': lm.visibility
            }
        return result
    
    # =========================================================================
    # GESTURE DETECTION
    # =========================================================================
    
    def detect_gesture(self, landmarks, width, height):
        """Detect gesture for robot control."""
        if landmarks is None:
            return 'NONE', {'linear_x': 0.0, 'angular_z': 0.0}
        
        # Get key landmarks
        left_shoulder = self.get_landmark(landmarks, PoseLandmark.LEFT_SHOULDER.value, width, height)
        right_shoulder = self.get_landmark(landmarks, PoseLandmark.RIGHT_SHOULDER.value, width, height)
        left_wrist = self.get_landmark(landmarks, PoseLandmark.LEFT_WRIST.value, width, height)
        right_wrist = self.get_landmark(landmarks, PoseLandmark.RIGHT_WRIST.value, width, height)
        left_elbow = self.get_landmark(landmarks, PoseLandmark.LEFT_ELBOW.value, width, height)
        right_elbow = self.get_landmark(landmarks, PoseLandmark.RIGHT_ELBOW.value, width, height)
        left_hip = self.get_landmark(landmarks, PoseLandmark.LEFT_HIP.value, width, height)
        right_hip = self.get_landmark(landmarks, PoseLandmark.RIGHT_HIP.value, width, height)
        
        if not all([left_shoulder, right_shoulder, left_wrist, right_wrist]):
            return 'INCOMPLETE', {'linear_x': 0.0, 'angular_z': 0.0}
        
        # Arm position analysis
        shoulder_y = (left_shoulder[1] + right_shoulder[1]) // 2
        
        left_arm_up = left_wrist[1] < left_shoulder[1] - 50
        right_arm_up = right_wrist[1] < right_shoulder[1] - 50
        left_arm_down = left_wrist[1] > left_shoulder[1] + 50
        right_arm_down = right_wrist[1] > right_shoulder[1] + 50
        
        # T-pose (arms horizontal)
        left_arm_horizontal = abs(left_wrist[1] - left_shoulder[1]) < 50
        right_arm_horizontal = abs(right_wrist[1] - right_shoulder[1]) < 50
        t_pose = left_arm_horizontal and right_arm_horizontal
        
        # Crouch detection (shoulders below normal)
        if left_hip and right_hip:
            hip_y = (left_hip[1] + right_hip[1]) // 2
            torso_height = hip_y - shoulder_y
            is_crouching = torso_height < 100  # Compressed torso
        else:
            is_crouching = False
        
        # Determine gesture
        gesture = 'NEUTRAL'
        command = {'linear_x': 0.0, 'angular_z': 0.0}
        
        if is_crouching:
            gesture = 'CROUCH'
        elif t_pose:
            gesture = 'T_POSE'
        elif left_arm_up and right_arm_up:
            gesture = 'BOTH_ARMS_UP'
        elif left_arm_down and right_arm_down:
            gesture = 'BOTH_ARMS_DOWN'
        elif left_arm_up and not right_arm_up:
            gesture = 'LEFT_ARM_UP'
        elif right_arm_up and not left_arm_up:
            gesture = 'RIGHT_ARM_UP'
        
        # Get command for gesture
        if gesture in GESTURE_CONTROLS:
            cmd = GESTURE_CONTROLS[gesture]
            command = {'linear_x': cmd['linear_x'], 'angular_z': cmd['angular_z']}
        
        return gesture, command
    
    # =========================================================================
    # EXERCISE COUNTING
    # =========================================================================
    
    def count_exercise(self, landmarks, width, height):
        """Count exercise repetitions."""
        if landmarks is None:
            return self.exercise_count, self.exercise_state
        
        if self.exercise_type == 'squats':
            return self._count_squats(landmarks, width, height)
        elif self.exercise_type == 'jumping_jacks':
            return self._count_jumping_jacks(landmarks, width, height)
        elif self.exercise_type == 'arm_raises':
            return self._count_arm_raises(landmarks, width, height)
        
        return self.exercise_count, self.exercise_state
    
    def _count_squats(self, landmarks, width, height):
        """Count squat repetitions based on knee angle."""
        left_hip = self.get_landmark(landmarks, PoseLandmark.LEFT_HIP.value, width, height)
        left_knee = self.get_landmark(landmarks, PoseLandmark.LEFT_KNEE.value, width, height)
        left_ankle = self.get_landmark(landmarks, PoseLandmark.LEFT_ANKLE.value, width, height)
        
        knee_angle = calculate_angle(left_hip, left_knee, left_ankle)
        
        if knee_angle is None:
            return self.exercise_count, self.exercise_state
        
        # State machine for counting
        if self.exercise_state == 'UP' and knee_angle < 100:  # Going down
            self.exercise_state = 'DOWN'
        elif self.exercise_state == 'DOWN' and knee_angle > 160:  # Coming up
            self.exercise_state = 'UP'
            self.exercise_count += 1
            self.get_logger().info(f"Squat count: {self.exercise_count}")
        
        return self.exercise_count, self.exercise_state
    
    def _count_jumping_jacks(self, landmarks, width, height):
        """Count jumping jack repetitions."""
        left_wrist = self.get_landmark(landmarks, PoseLandmark.LEFT_WRIST.value, width, height)
        right_wrist = self.get_landmark(landmarks, PoseLandmark.RIGHT_WRIST.value, width, height)
        left_shoulder = self.get_landmark(landmarks, PoseLandmark.LEFT_SHOULDER.value, width, height)
        right_shoulder = self.get_landmark(landmarks, PoseLandmark.RIGHT_SHOULDER.value, width, height)
        
        if not all([left_wrist, right_wrist, left_shoulder, right_shoulder]):
            return self.exercise_count, self.exercise_state
        
        # Check if arms are up (above shoulders)
        arms_up = left_wrist[1] < left_shoulder[1] and right_wrist[1] < right_shoulder[1]
        
        # Check if arms are down (below shoulders)
        arms_down = left_wrist[1] > left_shoulder[1] + 50 and right_wrist[1] > right_shoulder[1] + 50
        
        if self.exercise_state == 'DOWN' and arms_up:
            self.exercise_state = 'UP'
        elif self.exercise_state == 'UP' and arms_down:
            self.exercise_state = 'DOWN'
            self.exercise_count += 1
            self.get_logger().info(f"Jumping jack count: {self.exercise_count}")
        
        return self.exercise_count, self.exercise_state
    
    def _count_arm_raises(self, landmarks, width, height):
        """Count arm raise repetitions."""
        left_wrist = self.get_landmark(landmarks, PoseLandmark.LEFT_WRIST.value, width, height)
        left_shoulder = self.get_landmark(landmarks, PoseLandmark.LEFT_SHOULDER.value, width, height)
        nose = self.get_landmark(landmarks, PoseLandmark.NOSE.value, width, height)
        
        if not all([left_wrist, left_shoulder, nose]):
            return self.exercise_count, self.exercise_state
        
        # Arm raised = wrist above nose level
        arm_raised = left_wrist[1] < nose[1]
        arm_lowered = left_wrist[1] > left_shoulder[1] + 30
        
        if self.exercise_state == 'DOWN' and arm_raised:
            self.exercise_state = 'UP'
        elif self.exercise_state == 'UP' and arm_lowered:
            self.exercise_state = 'DOWN'
            self.exercise_count += 1
            self.get_logger().info(f"Arm raise count: {self.exercise_count}")
        
        return self.exercise_count, self.exercise_state
    
    # =========================================================================
    # ACTIVITY TRACKING
    # =========================================================================
    
    def track_activity(self, landmarks, width, height):
        """Track activity (standing, sitting, walking, etc.)."""
        if landmarks is None:
            return 'UNKNOWN'
        
        # Get key landmarks for activity detection
        nose = self.get_landmark(landmarks, PoseLandmark.NOSE.value, width, height)
        left_hip = self.get_landmark(landmarks, PoseLandmark.LEFT_HIP.value, width, height)
        right_hip = self.get_landmark(landmarks, PoseLandmark.RIGHT_HIP.value, width, height)
        left_knee = self.get_landmark(landmarks, PoseLandmark.LEFT_KNEE.value, width, height)
        right_knee = self.get_landmark(landmarks, PoseLandmark.RIGHT_KNEE.value, width, height)
        left_ankle = self.get_landmark(landmarks, PoseLandmark.LEFT_ANKLE.value, width, height)
        right_ankle = self.get_landmark(landmarks, PoseLandmark.RIGHT_ANKLE.value, width, height)
        
        if not all([left_hip, right_hip, left_knee, right_knee]):
            return 'UNKNOWN'
        
        # Calculate key angles
        left_knee_angle = calculate_angle(left_hip, left_knee, left_ankle) if left_ankle else None
        right_knee_angle = calculate_angle(right_hip, right_knee, right_ankle) if right_ankle else None
        
        # Hip height relative to frame
        hip_y = (left_hip[1] + right_hip[1]) / 2
        normalized_hip_y = hip_y / height
        
        # Store for history
        pose_data = {
            'hip_y': normalized_hip_y,
            'left_knee_angle': left_knee_angle,
            'right_knee_angle': right_knee_angle,
        }
        self.pose_history.append(pose_data)
        
        # Determine activity
        activity = 'UNKNOWN'
        
        # Check knee angles for sitting vs standing
        avg_knee_angle = None
        if left_knee_angle and right_knee_angle:
            avg_knee_angle = (left_knee_angle + right_knee_angle) / 2
        
        if avg_knee_angle:
            if avg_knee_angle < 100:
                activity = 'SITTING'
            elif avg_knee_angle > 160:
                activity = 'STANDING'
        
        # Check for jumping (analyze vertical motion)
        if len(self.pose_history) >= 10:
            recent_hip_y = [p['hip_y'] for p in list(self.pose_history)[-10:]]
            hip_variance = np.var(recent_hip_y)
            if hip_variance > 0.002:  # Significant vertical motion
                activity = 'JUMPING'
        
        # Check for walking (alternating leg positions)
        if len(self.pose_history) >= 20 and activity == 'STANDING':
            # Check for periodic knee angle changes
            left_angles = [p['left_knee_angle'] for p in list(self.pose_history)[-20:] if p['left_knee_angle']]
            if len(left_angles) >= 10:
                angle_variance = np.var(left_angles)
                if angle_variance > 50:  # Legs moving
                    activity = 'WALKING'
        
        self.current_activity = activity
        return activity
    
    # =========================================================================
    # MAIN CALLBACK
    # =========================================================================
    
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
        landmarks = results.pose_landmarks
        
        # Publish all landmarks
        all_landmarks = self.get_all_landmarks(landmarks, width, height)
        if all_landmarks:
            landmarks_msg = String()
            landmarks_msg.data = json.dumps(all_landmarks)
            self.landmarks_pub.publish(landmarks_msg)
        
        # Process based on mode
        behavior_result = {}
        
        if self.behavior_mode == 'gesture_control':
            gesture, command = self.detect_gesture(landmarks, width, height)
            behavior_result = {
                'mode': 'gesture_control',
                'gesture': gesture,
                'command': command
            }
            self._handle_robot_control(gesture, command)
            
        elif self.behavior_mode == 'exercise_counter':
            count, state = self.count_exercise(landmarks, width, height)
            behavior_result = {
                'mode': 'exercise_counter',
                'exercise': self.exercise_type,
                'count': count,
                'state': state
            }
            # Publish count
            count_msg = Int32()
            count_msg.data = count
            self.exercise_pub.publish(count_msg)
            
        elif self.behavior_mode == 'activity_tracker':
            activity = self.track_activity(landmarks, width, height)
            behavior_result = {
                'mode': 'activity_tracker',
                'activity': activity
            }
        
        # Publish behavior
        behavior_msg = String()
        behavior_msg.data = json.dumps(behavior_result)
        self.behavior_pub.publish(behavior_msg)
        
        # Visualization
        if self.visualization:
            self._visualize(frame, landmarks, behavior_result, msg.header)
    
    def _handle_robot_control(self, gesture, command):
        """Handle robot control with commitment mode."""
        desired_twist = Twist()
        if self.control_enabled:
            desired_twist.linear.x = float(command.get('linear_x', 0.0))
            desired_twist.angular.z = float(command.get('angular_z', 0.0))
        
        if not self.commitment_mode:
            # Direct control
            self.cmd_vel_pub.publish(desired_twist)
            return
        
        # Commitment mode state machine
        now = self.get_clock().now()
        elapsed = (now - self.state_start_time).nanoseconds / 1e9
        
        if self.state == 'ASSESS':
            is_action = gesture not in ['NONE', 'INCOMPLETE', 'NEUTRAL', 'T_POSE', 'BOTH_ARMS_DOWN']
            
            if is_action:
                self.current_action = desired_twist
                self.current_gesture = gesture
                self.state = 'EXECUTE'
                self.state_start_time = now
                self.get_logger().info(f"COMMIT: {gesture}")
            else:
                self.cmd_vel_pub.publish(Twist())
        
        elif self.state == 'EXECUTE':
            if elapsed < self.action_duration:
                self.cmd_vel_pub.publish(self.current_action)
            else:
                self.state = 'PAUSE'
                self.state_start_time = now
                self.cmd_vel_pub.publish(Twist())
        
        elif self.state == 'PAUSE':
            self.cmd_vel_pub.publish(Twist())
            if elapsed >= self.pause_duration:
                self.state = 'ASSESS'
                self.state_start_time = now
    
    def _visualize(self, frame, landmarks, behavior_result, header):
        """Create visualization frame."""
        viz_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Draw pose skeleton
        if landmarks is not None:
            self.mp_drawing.draw_landmarks(
                viz_frame,
                landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
                self.mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
            )
        
        # Draw mode and result
        mode = behavior_result.get('mode', '')
        y_offset = 30
        
        cv2.putText(viz_frame, f"Mode: {mode}", (10, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        y_offset += 30
        
        if mode == 'gesture_control':
            gesture = behavior_result.get('gesture', 'NONE')
            cv2.putText(viz_frame, f"Gesture: {gesture}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            if gesture in GESTURE_CONTROLS:
                desc = GESTURE_CONTROLS[gesture]['description']
                y_offset += 30
                cv2.putText(viz_frame, f"Action: {desc}", (10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
        elif mode == 'exercise_counter':
            exercise = behavior_result.get('exercise', '')
            count = behavior_result.get('count', 0)
            state = behavior_result.get('state', '')
            cv2.putText(viz_frame, f"{exercise.upper()}: {count}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 3)
            y_offset += 40
            cv2.putText(viz_frame, f"State: {state}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
                       
        elif mode == 'activity_tracker':
            activity = behavior_result.get('activity', 'UNKNOWN')
            cv2.putText(viz_frame, f"Activity: {activity}", (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        
        # Publish
        try:
            viz_msg = self.bridge.cv2_to_imgmsg(viz_frame, encoding='bgr8')
            viz_msg.header = header
            self.viz_pub.publish(viz_msg)
        except Exception as e:
            self.get_logger().error(f"Failed to publish visualization: {e}")
    
    def destroy_node(self):
        """Clean up."""
        if self.pose:
            self.pose.close()
        self.cmd_vel_pub.publish(Twist())
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    
    if not MEDIAPIPE_AVAILABLE:
        print("ERROR: MediaPipe not installed!")
        print("Run: pip3 install mediapipe --break-system-packages")
        return
    
    node = PoseBehaviorTracker()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
