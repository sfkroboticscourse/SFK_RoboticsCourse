#!/usr/bin/env python3
"""
Posture Monitor for Scoliosis Prevention (脊柱侧弯预防姿势监测)

Detects bad sitting postures that can worsen spinal curvature:
1. 二郎腿 (Crossed legs)
2. Slouching / Tech neck (头前伸/驼背)
3. 单侧托腮 / C-shaped spine (Leaning to one side, chin resting on hand)
4. 久坐不起 (Sitting too long without moving)

The robot can alert the user when bad posture is detected!

Topics:
    Subscribes:
        /camera/image_raw (sensor_msgs/Image): Camera frames
    
    Publishes:
        /vision/posture_status (std_msgs/String): Current posture analysis (JSON)
        /vision/posture_alert (std_msgs/String): Alert when bad posture detected
        /vision/visualization (sensor_msgs/Image): Annotated frame
        /cmd_vel (geometry_msgs/Twist): Robot can move to get attention
        /ai/speak (std_msgs/String): Voice alerts (if TTS node running)

Parameters:
    visualization (bool): Enable visualization output
    alert_enabled (bool): Enable alerts for bad posture
    slouch_threshold (float): Angle threshold for slouching detection (degrees)
    tilt_threshold (float): Angle threshold for side leaning (degrees)
    sitting_alert_minutes (int): Minutes before "sit too long" alert
    alert_cooldown_seconds (int): Seconds between repeated alerts
    
Dependencies:
    pip3 install mediapipe --break-system-packages

Usage:
    ros2 run multi_vision_pupper posture_monitor
    
    # With visualization
    ros2 launch multi_vision_pupper oakd_vision.launch.py mode:=posture visualization:=true
    
    # Adjust sensitivity
    ros2 run multi_vision_pupper posture_monitor --ros-args -p slouch_threshold:=15.0 -p tilt_threshold:=10.0

Author: Mini Pupper Teaching Lab - Scoliosis Prevention Project
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
import time
from collections import deque
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple, List

# MediaPipe
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("Warning: MediaPipe not available. Install with: pip3 install mediapipe")


# =============================================================================
# POSTURE DEFINITIONS
# =============================================================================

class PostureIssue(Enum):
    """Types of bad posture that can worsen scoliosis."""
    NONE = "good_posture"
    CROSSED_LEGS = "crossed_legs"           # 二郎腿
    SLOUCHING = "slouching"                  # 驼背/头前伸 (tech neck)
    LEANING_LEFT = "leaning_left"           # 左侧托腮/C形脊柱
    LEANING_RIGHT = "leaning_right"         # 右侧托腮/C形脊柱
    SITTING_TOO_LONG = "sitting_too_long"   # 久坐不起


@dataclass
class PostureAnalysis:
    """Results of posture analysis."""
    issues: List[PostureIssue]
    head_forward_angle: float  # Degrees head is forward (slouching)
    shoulder_tilt_angle: float  # Degrees shoulders are tilted
    spine_curve_angle: float   # Estimated spine curvature
    sitting_duration_minutes: float
    confidence: float
    
    def has_issues(self) -> bool:
        return len(self.issues) > 0 and PostureIssue.NONE not in self.issues
    
    def to_dict(self) -> dict:
        return {
            'issues': [issue.value for issue in self.issues],
            'head_forward_angle': round(self.head_forward_angle, 1),
            'shoulder_tilt_angle': round(self.shoulder_tilt_angle, 1),
            'spine_curve_angle': round(self.spine_curve_angle, 1),
            'sitting_duration_minutes': round(self.sitting_duration_minutes, 1),
            'confidence': round(self.confidence, 2),
            'has_issues': self.has_issues()
        }


# Alert messages in Chinese and English
ALERT_MESSAGES = {
    PostureIssue.CROSSED_LEGS: {
        'zh': '请不要翘二郎腿！这会加重脊柱侧弯。',
        'en': 'Please uncross your legs! This can worsen spinal curvature.'
    },
    PostureIssue.SLOUCHING: {
        'zh': '请坐直！你正在驼背，头部前伸。',
        'en': 'Please sit up straight! You are slouching with tech neck.'
    },
    PostureIssue.LEANING_LEFT: {
        'zh': '请坐正！你正在向左侧倾斜，脊柱呈C形。',
        'en': 'Please sit centered! You are leaning left with C-shaped spine.'
    },
    PostureIssue.LEANING_RIGHT: {
        'zh': '请坐正！你正在向右侧倾斜，脊柱呈C形。',
        'en': 'Please sit centered! You are leaning right with C-shaped spine.'
    },
    PostureIssue.SITTING_TOO_LONG: {
        'zh': '你已经坐了很久了！请站起来活动一下。',
        'en': 'You have been sitting too long! Please stand up and move around.'
    }
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def calculate_angle(p1, p2, p3) -> Optional[float]:
    """Calculate angle at p2 given three points. Returns degrees."""
    if any(p is None for p in [p1, p2, p3]):
        return None
    
    v1 = np.array([p1[0] - p2[0], p1[1] - p2[1]])
    v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])
    
    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
    angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
    return np.degrees(angle)


def calculate_horizontal_angle(p1, p2) -> Optional[float]:
    """Calculate angle from horizontal (0 = level, positive = tilted right)."""
    if p1 is None or p2 is None:
        return None
    
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return np.degrees(np.arctan2(dy, dx))


def get_distance(p1, p2) -> Optional[float]:
    """Calculate Euclidean distance between two points."""
    if p1 is None or p2 is None:
        return None
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


# =============================================================================
# POSTURE MONITOR NODE
# =============================================================================

class PostureMonitor(Node):
    """ROS2 node for monitoring sitting posture and detecting scoliosis-worsening positions."""
    
    # MediaPipe landmark indices
    NOSE = 0
    LEFT_EYE = 2
    RIGHT_EYE = 5
    LEFT_EAR = 7
    RIGHT_EAR = 8
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ANKLE = 27
    RIGHT_ANKLE = 28
    
    def __init__(self):
        super().__init__('posture_monitor')
        
        # Parameters
        self.declare_parameter('visualization', True)
        self.declare_parameter('alert_enabled', True)
        self.declare_parameter('language', 'en')  # 'en' or 'zh'
        
        # Detection thresholds
        self.declare_parameter('slouch_threshold', 20.0)  # Degrees head forward
        self.declare_parameter('tilt_threshold', 8.0)     # Degrees shoulder tilt
        self.declare_parameter('lean_threshold', 15.0)    # Degrees spine lean
        
        # Sitting duration alert
        self.declare_parameter('sitting_alert_minutes', 30)  # Alert after N minutes
        self.declare_parameter('alert_cooldown_seconds', 30)  # Time between alerts
        
        # Movement alert (robot wiggles to get attention)
        self.declare_parameter('movement_alert', True)
        
        # MediaPipe confidence
        self.declare_parameter('detection_confidence', 0.5)
        self.declare_parameter('tracking_confidence', 0.5)
        
        # Get parameters
        self.visualization = self.get_parameter('visualization').value
        self.alert_enabled = self.get_parameter('alert_enabled').value
        self.language = self.get_parameter('language').value
        self.slouch_threshold = self.get_parameter('slouch_threshold').value
        self.tilt_threshold = self.get_parameter('tilt_threshold').value
        self.lean_threshold = self.get_parameter('lean_threshold').value
        self.sitting_alert_minutes = self.get_parameter('sitting_alert_minutes').value
        self.alert_cooldown = self.get_parameter('alert_cooldown_seconds').value
        self.movement_alert = self.get_parameter('movement_alert').value
        
        # State tracking
        self.sitting_start_time = None
        self.last_alert_time = {}  # Track last alert time per issue type
        self.posture_history = deque(maxlen=30)  # ~1 second at 30fps
        self.person_detected = False
        
        # CV Bridge
        self.bridge = CvBridge()
        
        # Initialize MediaPipe
        self.pose = None
        self.mp_pose = None
        self.mp_drawing = None
        self._init_mediapipe()
        
        # Subscribers
        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10)
        
        # Publishers
        self.status_pub = self.create_publisher(String, '/vision/posture_status', 10)
        self.alert_pub = self.create_publisher(String, '/vision/posture_alert', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.speak_pub = self.create_publisher(String, '/ai/speak', 10)
        
        if self.visualization:
            self.viz_pub = self.create_publisher(Image, '/vision/visualization', 10)
        
        self.get_logger().info("=" * 60)
        self.get_logger().info("Posture Monitor for Scoliosis Prevention Started!")
        self.get_logger().info("脊柱侧弯预防姿势监测已启动！")
        self.get_logger().info(f"  Slouch threshold: {self.slouch_threshold}°")
        self.get_logger().info(f"  Tilt threshold: {self.tilt_threshold}°")
        self.get_logger().info(f"  Sitting alert: {self.sitting_alert_minutes} minutes")
        self.get_logger().info("=" * 60)
    
    def _init_mediapipe(self):
        """Initialize MediaPipe Pose."""
        if not MEDIAPIPE_AVAILABLE:
            self.get_logger().error("MediaPipe not available!")
            return
        
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=self.get_parameter('detection_confidence').value,
            min_tracking_confidence=self.get_parameter('tracking_confidence').value
        )
        self.get_logger().info("MediaPipe Pose initialized")
    
    def get_landmark(self, landmarks, idx, width, height) -> Optional[Tuple[int, int]]:
        """Get pixel coordinates for a landmark."""
        if landmarks is None:
            return None
        lm = landmarks.landmark[idx]
        if lm.visibility < 0.5:
            return None
        return (int(lm.x * width), int(lm.y * height))
    
    def analyze_posture(self, landmarks, width, height) -> PostureAnalysis:
        """Analyze posture and detect issues that worsen scoliosis."""
        issues = []
        head_forward = 0.0
        shoulder_tilt = 0.0
        spine_curve = 0.0
        confidence = 0.0
        
        if landmarks is None:
            return PostureAnalysis(
                issues=[],
                head_forward_angle=0,
                shoulder_tilt_angle=0,
                spine_curve_angle=0,
                sitting_duration_minutes=self._get_sitting_duration(),
                confidence=0
            )
        
        # Get key landmarks
        nose = self.get_landmark(landmarks, self.NOSE, width, height)
        left_ear = self.get_landmark(landmarks, self.LEFT_EAR, width, height)
        right_ear = self.get_landmark(landmarks, self.RIGHT_EAR, width, height)
        left_shoulder = self.get_landmark(landmarks, self.LEFT_SHOULDER, width, height)
        right_shoulder = self.get_landmark(landmarks, self.RIGHT_SHOULDER, width, height)
        left_hip = self.get_landmark(landmarks, self.LEFT_HIP, width, height)
        right_hip = self.get_landmark(landmarks, self.RIGHT_HIP, width, height)
        left_wrist = self.get_landmark(landmarks, self.LEFT_WRIST, width, height)
        right_wrist = self.get_landmark(landmarks, self.RIGHT_WRIST, width, height)
        left_knee = self.get_landmark(landmarks, self.LEFT_KNEE, width, height)
        right_knee = self.get_landmark(landmarks, self.RIGHT_KNEE, width, height)
        left_ankle = self.get_landmark(landmarks, self.LEFT_ANKLE, width, height)
        right_ankle = self.get_landmark(landmarks, self.RIGHT_ANKLE, width, height)
        
        # Calculate confidence based on landmark visibility
        visible_landmarks = sum(1 for lm in [nose, left_shoulder, right_shoulder, 
                                              left_hip, right_hip] if lm is not None)
        confidence = visible_landmarks / 5.0
        
        if confidence < 0.6:
            return PostureAnalysis(
                issues=[],
                head_forward_angle=0,
                shoulder_tilt_angle=0,
                spine_curve_angle=0,
                sitting_duration_minutes=self._get_sitting_duration(),
                confidence=confidence
            )
        
        # =====================================================================
        # 1. SLOUCHING / TECH NECK DETECTION (驼背/头前伸)
        # =====================================================================
        # Check if head is forward relative to shoulders
        if all([nose, left_shoulder, right_shoulder, left_ear, right_ear]):
            # Shoulder center
            shoulder_center_x = (left_shoulder[0] + right_shoulder[0]) // 2
            
            # Ear center (approximates head position)
            ear_center_x = (left_ear[0] + right_ear[0]) // 2
            
            # In a side view, if head is forward, nose will be forward of shoulder line
            # Since we're viewing from front, we check ear-shoulder alignment
            # and nose-to-shoulder-center vertical alignment
            
            # Calculate head forward angle using ear and shoulder positions
            if left_ear and left_shoulder:
                # Vector from shoulder to ear
                head_forward = self._calculate_head_forward_angle(
                    nose, left_ear, right_ear, left_shoulder, right_shoulder
                )
                
                if head_forward > self.slouch_threshold:
                    issues.append(PostureIssue.SLOUCHING)
        
        # =====================================================================
        # 2. SHOULDER TILT / SIDE LEANING (单侧托腮/C形脊柱)
        # =====================================================================
        if left_shoulder and right_shoulder:
            # Calculate shoulder tilt angle
            shoulder_tilt = calculate_horizontal_angle(left_shoulder, right_shoulder)
            
            if shoulder_tilt is not None:
                # Normalize to deviation from horizontal
                shoulder_tilt = abs(shoulder_tilt)
                
                if shoulder_tilt > self.tilt_threshold:
                    # Determine which side is lower
                    if left_shoulder[1] > right_shoulder[1]:
                        issues.append(PostureIssue.LEANING_LEFT)
                    else:
                        issues.append(PostureIssue.LEANING_RIGHT)
        
        # Also check spine curvature (nose-hip alignment)
        if nose and left_hip and right_hip and left_shoulder and right_shoulder:
            hip_center_x = (left_hip[0] + right_hip[0]) // 2
            shoulder_center_x = (left_shoulder[0] + right_shoulder[0]) // 2
            
            # Spine curve = deviation of nose from hip-shoulder line
            spine_deviation = nose[0] - hip_center_x
            # Normalize by frame width
            spine_curve = (spine_deviation / width) * 100  # As percentage
            
            if abs(spine_curve) > self.lean_threshold:
                if spine_curve > 0 and PostureIssue.LEANING_RIGHT not in issues:
                    issues.append(PostureIssue.LEANING_RIGHT)
                elif spine_curve < 0 and PostureIssue.LEANING_LEFT not in issues:
                    issues.append(PostureIssue.LEANING_LEFT)
        
        # =====================================================================
        # 3. CROSSED LEGS DETECTION (二郎腿)
        # =====================================================================
        if all([left_knee, right_knee, left_ankle, right_ankle]):
            # When legs are crossed, one knee will be significantly higher/displaced
            knee_height_diff = abs(left_knee[1] - right_knee[1])
            knee_horizontal_diff = abs(left_knee[0] - right_knee[0])
            
            # Also check ankle positions
            ankle_height_diff = abs(left_ankle[1] - right_ankle[1])
            
            # Crossed legs signature: knees close together horizontally but 
            # one ankle far from expected position
            if knee_height_diff > 30 or (knee_horizontal_diff < 50 and ankle_height_diff > 50):
                issues.append(PostureIssue.CROSSED_LEGS)
        
        # =====================================================================
        # 4. SITTING TOO LONG (久坐不起)
        # =====================================================================
        sitting_duration = self._get_sitting_duration()
        if sitting_duration > self.sitting_alert_minutes:
            issues.append(PostureIssue.SITTING_TOO_LONG)
        
        # If no issues detected, mark as good posture
        if len(issues) == 0:
            issues.append(PostureIssue.NONE)
        
        return PostureAnalysis(
            issues=issues,
            head_forward_angle=head_forward,
            shoulder_tilt_angle=shoulder_tilt if shoulder_tilt else 0,
            spine_curve_angle=spine_curve,
            sitting_duration_minutes=sitting_duration,
            confidence=confidence
        )
    
    def _calculate_head_forward_angle(self, nose, left_ear, right_ear, 
                                       left_shoulder, right_shoulder) -> float:
        """
        Calculate how far forward the head is relative to shoulders.
        Uses the ear position relative to shoulder as proxy for head forward position.
        """
        # This is an approximation since we're viewing from front
        # In a true side view, we'd measure nose-to-shoulder horizontal distance
        
        # Use ear-shoulder relationship
        ear_center_y = (left_ear[1] + right_ear[1]) // 2
        shoulder_center_y = (left_shoulder[1] + right_shoulder[1]) // 2
        
        # Nose should be roughly above shoulders when sitting straight
        nose_to_shoulder_y = shoulder_center_y - nose[1]
        
        # Calculate a forward lean metric
        # When slouching, the nose drops and moves forward
        # We use the ratio of vertical to expected position
        expected_nose_height = shoulder_center_y - 150  # Expected nose ~150px above shoulders
        
        if nose[1] > expected_nose_height:
            # Nose is lower than expected = slouching
            forward_angle = (nose[1] - expected_nose_height) / 5  # Rough conversion to degrees
            return min(forward_angle, 45)  # Cap at 45 degrees
        
        return 0
    
    def _get_sitting_duration(self) -> float:
        """Get how long the person has been sitting (in minutes)."""
        if self.sitting_start_time is None:
            return 0.0
        return (time.time() - self.sitting_start_time) / 60.0
    
    def _should_alert(self, issue: PostureIssue) -> bool:
        """Check if we should send an alert for this issue (respecting cooldown)."""
        if not self.alert_enabled:
            return False
        
        now = time.time()
        last_alert = self.last_alert_time.get(issue, 0)
        
        if now - last_alert >= self.alert_cooldown:
            self.last_alert_time[issue] = now
            return True
        return False
    
    def _send_alerts(self, analysis: PostureAnalysis):
        """Send alerts for detected posture issues."""
        for issue in analysis.issues:
            if issue == PostureIssue.NONE:
                continue
            
            if self._should_alert(issue):
                # Get alert message
                msg = ALERT_MESSAGES.get(issue, {})
                alert_text = msg.get(self.language, msg.get('en', 'Bad posture detected!'))
                
                # Publish alert
                alert_msg = String()
                alert_msg.data = json.dumps({
                    'issue': issue.value,
                    'message': alert_text,
                    'language': self.language
                })
                self.alert_pub.publish(alert_msg)
                
                # Speak alert (if TTS node is running)
                speak_msg = String()
                speak_msg.data = alert_text
                self.speak_pub.publish(speak_msg)
                
                # Movement alert - robot wiggles to get attention
                if self.movement_alert:
                    self._wiggle_alert()
                
                self.get_logger().warn(f"POSTURE ALERT: {issue.value} - {alert_text}")
    
    def _wiggle_alert(self):
        """Make robot wiggle to get user's attention."""
        twist = Twist()
        
        # Quick wiggle
        for _ in range(2):
            twist.angular.z = 0.5
            self.cmd_vel_pub.publish(twist)
            time.sleep(0.15)
            twist.angular.z = -0.5
            self.cmd_vel_pub.publish(twist)
            time.sleep(0.15)
        
        # Stop
        self.cmd_vel_pub.publish(Twist())
    
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
        
        # Track sitting time
        if landmarks is not None:
            if not self.person_detected:
                self.person_detected = True
                self.sitting_start_time = time.time()
                self.get_logger().info("Person detected, starting sitting timer")
        else:
            if self.person_detected:
                self.person_detected = False
                self.sitting_start_time = None
                self.get_logger().info("Person left, resetting sitting timer")
        
        # Analyze posture
        analysis = self.analyze_posture(landmarks, width, height)
        
        # Store in history for smoothing
        self.posture_history.append(analysis)
        
        # Publish status
        status_msg = String()
        status_msg.data = json.dumps(analysis.to_dict())
        self.status_pub.publish(status_msg)
        
        # Send alerts if issues detected
        if analysis.has_issues():
            self._send_alerts(analysis)
        
        # Visualization
        if self.visualization:
            self._visualize(frame, landmarks, analysis, msg.header)
    
    def _visualize(self, frame, landmarks, analysis: PostureAnalysis, header):
        """Create visualization with posture analysis overlay."""
        viz_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        height, width = viz_frame.shape[:2]
        
        # Draw pose skeleton
        if landmarks is not None:
            self.mp_drawing.draw_landmarks(
                viz_frame,
                landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
                self.mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
            )
        
        # Status panel background
        cv2.rectangle(viz_frame, (5, 5), (350, 180), (0, 0, 0), -1)
        cv2.rectangle(viz_frame, (5, 5), (350, 180), (255, 255, 255), 2)
        
        y_offset = 30
        
        # Title
        cv2.putText(viz_frame, "Posture Monitor", (15, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        y_offset += 25
        cv2.putText(viz_frame, "姿势监测", (15, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        y_offset += 30
        
        # Posture status
        if analysis.has_issues():
            status_color = (0, 0, 255)  # Red for bad posture
            status_text = "BAD POSTURE!"
        else:
            status_color = (0, 255, 0)  # Green for good posture
            status_text = "Good posture"
        
        cv2.putText(viz_frame, status_text, (15, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
        y_offset += 25
        
        # Show detected issues
        for issue in analysis.issues:
            if issue != PostureIssue.NONE:
                issue_text = issue.value.replace('_', ' ').title()
                cv2.putText(viz_frame, f"- {issue_text}", (20, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 100, 255), 1)
                y_offset += 20
        
        # Metrics
        y_offset = 200
        cv2.putText(viz_frame, f"Head forward: {analysis.head_forward_angle:.1f} deg", 
                   (15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        y_offset += 20
        cv2.putText(viz_frame, f"Shoulder tilt: {analysis.shoulder_tilt_angle:.1f} deg", 
                   (15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        y_offset += 20
        cv2.putText(viz_frame, f"Sitting time: {analysis.sitting_duration_minutes:.1f} min", 
                   (15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Instructions at bottom
        instructions = [
            "Good posture tips:",
            "- Keep head aligned over shoulders",
            "- Keep shoulders level",
            "- Don't cross your legs",
            "- Stand up every 30 minutes"
        ]
        y_bottom = height - 100
        for text in instructions:
            cv2.putText(viz_frame, text, (15, y_bottom),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (180, 180, 180), 1)
            y_bottom += 18
        
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
    
    node = PostureMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
