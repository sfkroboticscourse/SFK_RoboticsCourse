#!/usr/bin/env python3
"""
Posture Monitor for Scoliosis Prevention (脊柱侧弯预防姿势监测)

Detects bad sitting postures that can worsen spinal curvature:
1. 二郎腿 (Crossed legs)
2. Slouching / Tech neck (头前伸/驼背)
3. 单侧托腮 / C-shaped spine (Leaning to one side, chin resting on hand)
4. 久坐不起 (Sitting too long without moving)

The robot can alert the user when bad posture is detected!

=== IMPORTANT: MODEL SETUP ===

This node requires the MediaPipe Pose Landmarker model. 
Download it ONCE on the Mini Pupper:

    mkdir -p ~/models
    wget -O ~/models/pose_landmarker_lite.task \
        https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task

Or for better accuracy (but slower):
    wget -O ~/models/pose_landmarker_full.task \
        https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task

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
    model_path (str): Path to pose_landmarker.task file
    visualization (bool): Enable visualization output
    alert_enabled (bool): Enable alerts for bad posture
    slouch_threshold (float): Angle threshold for slouching detection (degrees)
    tilt_threshold (float): Angle threshold for side leaning (degrees)
    sitting_alert_minutes (int): Minutes before "sit too long" alert
    alert_cooldown_seconds (int): Seconds between repeated alerts
    
Dependencies:
    pip3 install mediapipe --break-system-packages

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
import os
import urllib.request
from collections import deque
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple, List

# MediaPipe - check for both legacy and Tasks API
MEDIAPIPE_AVAILABLE = False
MEDIAPIPE_TASKS_AVAILABLE = False
MEDIAPIPE_LEGACY_AVAILABLE = False

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
    
    # Check for Tasks API (newer, requires model file)
    try:
        from mediapipe.tasks import python as mp_tasks
        from mediapipe.tasks.python import vision as mp_vision
        MEDIAPIPE_TASKS_AVAILABLE = True
    except ImportError:
        pass
    
    # Check for legacy API (older, auto-downloads)
    try:
        _ = mp.solutions.pose
        MEDIAPIPE_LEGACY_AVAILABLE = True
    except AttributeError:
        pass
        
except ImportError:
    print("=" * 60)
    print("ERROR: MediaPipe not installed!")
    print("Run: pip3 install mediapipe --break-system-packages")
    print("=" * 60)


# =============================================================================
# MODEL PATHS AND DOWNLOAD URLS
# =============================================================================

MODEL_URLS = {
    'lite': 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task',
    'full': 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task',
    'heavy': 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task',
}

DEFAULT_MODEL_DIR = os.path.expanduser('~/models')
DEFAULT_MODEL_NAME = 'pose_landmarker_lite.task'


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
    head_forward_angle: float
    shoulder_tilt_angle: float
    spine_curve_angle: float
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


# MediaPipe Pose landmark indices (same for both APIs)
class LandmarkIdx:
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
    """Calculate angle from horizontal (0 = level, positive = tilted)."""
    if p1 is None or p2 is None:
        return None
    
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return np.degrees(np.arctan2(dy, dx))


def download_model(url: str, dest_path: str) -> bool:
    """Download model file if it doesn't exist."""
    if os.path.exists(dest_path):
        return True
    
    print(f"Downloading model to {dest_path}...")
    try:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        urllib.request.urlretrieve(url, dest_path)
        print(f"Model downloaded successfully!")
        return True
    except Exception as e:
        print(f"Failed to download model: {e}")
        return False


# =============================================================================
# POSTURE MONITOR NODE
# =============================================================================

class PostureMonitor(Node):
    """ROS2 node for monitoring sitting posture and detecting scoliosis-worsening positions."""
    
    def __init__(self):
        super().__init__('posture_monitor')
        
        # Parameters
        self.declare_parameter('visualization', True)
        self.declare_parameter('alert_enabled', True)
        self.declare_parameter('language', 'en')
        
        # Model path - IMPORTANT!
        default_model_path = os.path.join(DEFAULT_MODEL_DIR, DEFAULT_MODEL_NAME)
        self.declare_parameter('model_path', default_model_path)
        self.declare_parameter('model_type', 'lite')  # lite, full, or heavy
        self.declare_parameter('auto_download', True)  # Try to download if missing
        
        # Detection thresholds
        self.declare_parameter('slouch_threshold', 20.0)
        self.declare_parameter('tilt_threshold', 8.0)
        self.declare_parameter('lean_threshold', 15.0)
        
        # Sitting duration alert
        self.declare_parameter('sitting_alert_minutes', 30)
        self.declare_parameter('alert_cooldown_seconds', 30)
        
        # Movement alert
        self.declare_parameter('movement_alert', True)
        
        # MediaPipe confidence
        self.declare_parameter('detection_confidence', 0.5)
        self.declare_parameter('tracking_confidence', 0.5)
        
        # Get parameters
        self.visualization = self.get_parameter('visualization').value
        self.alert_enabled = self.get_parameter('alert_enabled').value
        self.language = self.get_parameter('language').value
        self.model_path = self.get_parameter('model_path').value
        self.model_type = self.get_parameter('model_type').value
        self.auto_download = self.get_parameter('auto_download').value
        self.slouch_threshold = self.get_parameter('slouch_threshold').value
        self.tilt_threshold = self.get_parameter('tilt_threshold').value
        self.lean_threshold = self.get_parameter('lean_threshold').value
        self.sitting_alert_minutes = self.get_parameter('sitting_alert_minutes').value
        self.alert_cooldown = self.get_parameter('alert_cooldown_seconds').value
        self.movement_alert = self.get_parameter('movement_alert').value
        self.detection_confidence = self.get_parameter('detection_confidence').value
        
        # State tracking
        self.sitting_start_time = None
        self.last_alert_time = {}
        self.posture_history = deque(maxlen=30)
        self.person_detected = False
        
        # Pose detector (will be set by init)
        self.pose_detector = None
        self.using_tasks_api = False
        self.using_legacy_api = False
        
        # For legacy API
        self.mp_pose = None
        self.mp_drawing = None
        
        # CV Bridge
        self.bridge = CvBridge()
        
        # Initialize MediaPipe
        self._init_mediapipe()
        
        if self.pose_detector is None and self.mp_pose is None:
            self.get_logger().error("=" * 60)
            self.get_logger().error("POSE DETECTION NOT AVAILABLE!")
            self.get_logger().error("See instructions below to fix.")
            self.get_logger().error("=" * 60)
            self._print_setup_instructions()
            return
        
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
        if self.using_tasks_api:
            self.get_logger().info(f"  Using: MediaPipe Tasks API")
            self.get_logger().info(f"  Model: {self.model_path}")
        else:
            self.get_logger().info(f"  Using: MediaPipe Legacy API")
        self.get_logger().info(f"  Slouch threshold: {self.slouch_threshold}°")
        self.get_logger().info(f"  Tilt threshold: {self.tilt_threshold}°")
        self.get_logger().info(f"  Sitting alert: {self.sitting_alert_minutes} minutes")
        self.get_logger().info("=" * 60)
    
    def _print_setup_instructions(self):
        """Print instructions for setting up MediaPipe."""
        self.get_logger().error("")
        self.get_logger().error("=== HOW TO FIX ===")
        self.get_logger().error("")
        self.get_logger().error("1. Install MediaPipe:")
        self.get_logger().error("   pip3 install mediapipe --break-system-packages")
        self.get_logger().error("")
        self.get_logger().error("2. Download the pose model:")
        self.get_logger().error("   mkdir -p ~/models")
        self.get_logger().error("   wget -O ~/models/pose_landmarker_lite.task \\")
        self.get_logger().error("     https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task")
        self.get_logger().error("")
        self.get_logger().error("3. Then run this node again")
        self.get_logger().error("")
    
    def _init_mediapipe(self):
        """Initialize MediaPipe Pose - try Tasks API first, fall back to legacy."""
        
        if not MEDIAPIPE_AVAILABLE:
            self.get_logger().error("MediaPipe not installed!")
            return
        
        # === TRY TASKS API FIRST (newer, more reliable) ===
        if MEDIAPIPE_TASKS_AVAILABLE:
            self.get_logger().info("Trying MediaPipe Tasks API...")
            
            # Check if model exists
            if not os.path.exists(self.model_path):
                self.get_logger().warn(f"Model not found at: {self.model_path}")
                
                # Try auto-download
                if self.auto_download:
                    url = MODEL_URLS.get(self.model_type, MODEL_URLS['lite'])
                    if download_model(url, self.model_path):
                        self.get_logger().info("Model downloaded successfully!")
                    else:
                        self.get_logger().error("Auto-download failed!")
            
            # Try to create detector
            if os.path.exists(self.model_path):
                try:
                    base_options = mp_tasks.BaseOptions(
                        model_asset_path=self.model_path
                    )
                    options = mp_vision.PoseLandmarkerOptions(
                        base_options=base_options,
                        running_mode=mp_vision.RunningMode.IMAGE,
                        num_poses=1,
                        min_pose_detection_confidence=self.detection_confidence,
                        min_tracking_confidence=self.detection_confidence,
                    )
                    self.pose_detector = mp_vision.PoseLandmarker.create_from_options(options)
                    self.using_tasks_api = True
                    self.get_logger().info("MediaPipe Tasks API initialized successfully!")
                    return
                except Exception as e:
                    self.get_logger().warn(f"Tasks API failed: {e}")
        
        # === FALL BACK TO LEGACY API ===
        if MEDIAPIPE_LEGACY_AVAILABLE:
            self.get_logger().info("Trying MediaPipe Legacy API...")
            try:
                self.mp_pose = mp.solutions.pose
                self.mp_drawing = mp.solutions.drawing_utils
                
                # This will try to auto-download the model
                self.pose_detector = self.mp_pose.Pose(
                    static_image_mode=False,
                    model_complexity=0,  # 0=lite for speed on RPi
                    smooth_landmarks=True,
                    enable_segmentation=False,
                    min_detection_confidence=self.detection_confidence,
                    min_tracking_confidence=self.detection_confidence
                )
                self.using_legacy_api = True
                self.get_logger().info("MediaPipe Legacy API initialized!")
                return
            except Exception as e:
                self.get_logger().error(f"Legacy API failed: {e}")
                self.pose_detector = None
        
        self.get_logger().error("All MediaPipe initialization methods failed!")
    
    def get_landmark(self, landmarks, idx, width, height) -> Optional[Tuple[int, int]]:
        """Get pixel coordinates for a landmark (works with both APIs)."""
        if landmarks is None:
            return None
        
        try:
            if self.using_tasks_api:
                # Tasks API: landmarks is a list of NormalizedLandmark
                if idx >= len(landmarks):
                    return None
                lm = landmarks[idx]
                if lm.visibility < 0.5:
                    return None
                return (int(lm.x * width), int(lm.y * height))
            else:
                # Legacy API: landmarks.landmark is a list
                lm = landmarks.landmark[idx]
                if lm.visibility < 0.5:
                    return None
                return (int(lm.x * width), int(lm.y * height))
        except (IndexError, AttributeError):
            return None
    
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
        nose = self.get_landmark(landmarks, LandmarkIdx.NOSE, width, height)
        left_ear = self.get_landmark(landmarks, LandmarkIdx.LEFT_EAR, width, height)
        right_ear = self.get_landmark(landmarks, LandmarkIdx.RIGHT_EAR, width, height)
        left_shoulder = self.get_landmark(landmarks, LandmarkIdx.LEFT_SHOULDER, width, height)
        right_shoulder = self.get_landmark(landmarks, LandmarkIdx.RIGHT_SHOULDER, width, height)
        left_hip = self.get_landmark(landmarks, LandmarkIdx.LEFT_HIP, width, height)
        right_hip = self.get_landmark(landmarks, LandmarkIdx.RIGHT_HIP, width, height)
        left_knee = self.get_landmark(landmarks, LandmarkIdx.LEFT_KNEE, width, height)
        right_knee = self.get_landmark(landmarks, LandmarkIdx.RIGHT_KNEE, width, height)
        left_ankle = self.get_landmark(landmarks, LandmarkIdx.LEFT_ANKLE, width, height)
        right_ankle = self.get_landmark(landmarks, LandmarkIdx.RIGHT_ANKLE, width, height)
        
        # Calculate confidence
        visible = sum(1 for lm in [nose, left_shoulder, right_shoulder, left_hip, right_hip] 
                     if lm is not None)
        confidence = visible / 5.0
        
        if confidence < 0.6:
            return PostureAnalysis(
                issues=[],
                head_forward_angle=0,
                shoulder_tilt_angle=0,
                spine_curve_angle=0,
                sitting_duration_minutes=self._get_sitting_duration(),
                confidence=confidence
            )
        
        # === 1. SLOUCHING / TECH NECK (驼背/头前伸) ===
        if all([nose, left_ear, right_ear, left_shoulder, right_shoulder]):
            head_forward = self._calculate_head_forward_angle(
                nose, left_ear, right_ear, left_shoulder, right_shoulder
            )
            if head_forward > self.slouch_threshold:
                issues.append(PostureIssue.SLOUCHING)
        
        # === 2. SHOULDER TILT / SIDE LEANING (单侧托腮/C形脊柱) ===
        if left_shoulder and right_shoulder:
            shoulder_tilt = calculate_horizontal_angle(left_shoulder, right_shoulder)
            if shoulder_tilt is not None:
                shoulder_tilt = abs(shoulder_tilt)
                if shoulder_tilt > self.tilt_threshold:
                    if left_shoulder[1] > right_shoulder[1]:
                        issues.append(PostureIssue.LEANING_LEFT)
                    else:
                        issues.append(PostureIssue.LEANING_RIGHT)
        
        # Spine curvature check
        if nose and left_hip and right_hip and left_shoulder and right_shoulder:
            hip_center_x = (left_hip[0] + right_hip[0]) // 2
            spine_deviation = nose[0] - hip_center_x
            spine_curve = (spine_deviation / width) * 100
            
            if abs(spine_curve) > self.lean_threshold:
                if spine_curve > 0 and PostureIssue.LEANING_RIGHT not in issues:
                    issues.append(PostureIssue.LEANING_RIGHT)
                elif spine_curve < 0 and PostureIssue.LEANING_LEFT not in issues:
                    issues.append(PostureIssue.LEANING_LEFT)
        
        # === 3. CROSSED LEGS (二郎腿) ===
        if all([left_knee, right_knee, left_ankle, right_ankle]):
            knee_height_diff = abs(left_knee[1] - right_knee[1])
            knee_horizontal_diff = abs(left_knee[0] - right_knee[0])
            ankle_height_diff = abs(left_ankle[1] - right_ankle[1])
            
            if knee_height_diff > 30 or (knee_horizontal_diff < 50 and ankle_height_diff > 50):
                issues.append(PostureIssue.CROSSED_LEGS)
        
        # === 4. SITTING TOO LONG (久坐不起) ===
        sitting_duration = self._get_sitting_duration()
        if sitting_duration > self.sitting_alert_minutes:
            issues.append(PostureIssue.SITTING_TOO_LONG)
        
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
        """Calculate how far forward the head is."""
        ear_center_y = (left_ear[1] + right_ear[1]) // 2
        shoulder_center_y = (left_shoulder[1] + right_shoulder[1]) // 2
        
        expected_nose_height = shoulder_center_y - 150
        
        if nose[1] > expected_nose_height:
            forward_angle = (nose[1] - expected_nose_height) / 5
            return min(forward_angle, 45)
        
        return 0
    
    def _get_sitting_duration(self) -> float:
        """Get sitting duration in minutes."""
        if self.sitting_start_time is None:
            return 0.0
        return (time.time() - self.sitting_start_time) / 60.0
    
    def _should_alert(self, issue: PostureIssue) -> bool:
        """Check alert cooldown."""
        if not self.alert_enabled:
            return False
        
        now = time.time()
        last_alert = self.last_alert_time.get(issue, 0)
        
        if now - last_alert >= self.alert_cooldown:
            self.last_alert_time[issue] = now
            return True
        return False
    
    def _send_alerts(self, analysis: PostureAnalysis):
        """Send alerts for detected issues."""
        for issue in analysis.issues:
            if issue == PostureIssue.NONE:
                continue
            
            if self._should_alert(issue):
                msg = ALERT_MESSAGES.get(issue, {})
                alert_text = msg.get(self.language, msg.get('en', 'Bad posture detected!'))
                
                alert_msg = String()
                alert_msg.data = json.dumps({
                    'issue': issue.value,
                    'message': alert_text,
                    'language': self.language
                })
                self.alert_pub.publish(alert_msg)
                
                speak_msg = String()
                speak_msg.data = alert_text
                self.speak_pub.publish(speak_msg)
                
                if self.movement_alert:
                    self._wiggle_alert()
                
                self.get_logger().warn(f"POSTURE ALERT: {issue.value}")
    
    def _wiggle_alert(self):
        """Robot wiggle alert."""
        twist = Twist()
        for _ in range(2):
            twist.angular.z = 0.5
            self.cmd_vel_pub.publish(twist)
            time.sleep(0.15)
            twist.angular.z = -0.5
            self.cmd_vel_pub.publish(twist)
            time.sleep(0.15)
        self.cmd_vel_pub.publish(Twist())
    
    def image_callback(self, msg):
        """Process incoming camera frame."""
        if self.pose_detector is None:
            return
        
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
        except Exception as e:
            self.get_logger().error(f"Image conversion failed: {e}")
            return
        
        height, width = frame.shape[:2]
        landmarks = None
        
        # Process based on which API we're using
        try:
            if self.using_tasks_api:
                # Tasks API
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
                result = self.pose_detector.detect(mp_image)
                if result.pose_landmarks and len(result.pose_landmarks) > 0:
                    landmarks = result.pose_landmarks[0]  # First person
            else:
                # Legacy API
                results = self.pose_detector.process(frame)
                landmarks = results.pose_landmarks
        except Exception as e:
            self.get_logger().error(f"Pose detection failed: {e}")
            return
        
        # Track sitting time
        if landmarks is not None:
            if not self.person_detected:
                self.person_detected = True
                self.sitting_start_time = time.time()
        else:
            if self.person_detected:
                self.person_detected = False
                self.sitting_start_time = None
        
        # Analyze posture
        analysis = self.analyze_posture(landmarks, width, height)
        
        # Publish status
        status_msg = String()
        status_msg.data = json.dumps(analysis.to_dict())
        self.status_pub.publish(status_msg)
        
        # Send alerts
        if analysis.has_issues():
            self._send_alerts(analysis)
        
        # Visualization
        if self.visualization:
            self._visualize(frame, landmarks, analysis, msg.header)
    
    def _visualize(self, frame, landmarks, analysis: PostureAnalysis, header):
        """Create visualization."""
        viz_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        height, width = viz_frame.shape[:2]
        
        # Draw skeleton
        if landmarks is not None:
            if self.using_tasks_api:
                # Draw manually for Tasks API
                self._draw_landmarks_tasks(viz_frame, landmarks, width, height)
            else:
                # Use built-in drawing for Legacy API
                self.mp_drawing.draw_landmarks(
                    viz_frame,
                    landmarks,
                    self.mp_pose.POSE_CONNECTIONS,
                    self.mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
                    self.mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2)
                )
        
        # Status panel
        cv2.rectangle(viz_frame, (5, 5), (350, 180), (0, 0, 0), -1)
        cv2.rectangle(viz_frame, (5, 5), (350, 180), (255, 255, 255), 2)
        
        y_offset = 30
        cv2.putText(viz_frame, "Posture Monitor", (15, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        y_offset += 25
        cv2.putText(viz_frame, "姿势监测", (15, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        y_offset += 30
        
        if analysis.has_issues():
            status_color = (0, 0, 255)
            status_text = "BAD POSTURE!"
        else:
            status_color = (0, 255, 0)
            status_text = "Good posture"
        
        cv2.putText(viz_frame, status_text, (15, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
        y_offset += 25
        
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
        
        # Publish
        try:
            viz_msg = self.bridge.cv2_to_imgmsg(viz_frame, encoding='bgr8')
            viz_msg.header = header
            self.viz_pub.publish(viz_msg)
        except Exception as e:
            self.get_logger().error(f"Viz publish failed: {e}")
    
    def _draw_landmarks_tasks(self, frame, landmarks, width, height):
        """Draw landmarks for Tasks API (manual drawing)."""
        # Define connections
        connections = [
            (LandmarkIdx.NOSE, LandmarkIdx.LEFT_EYE),
            (LandmarkIdx.NOSE, LandmarkIdx.RIGHT_EYE),
            (LandmarkIdx.LEFT_EYE, LandmarkIdx.LEFT_EAR),
            (LandmarkIdx.RIGHT_EYE, LandmarkIdx.RIGHT_EAR),
            (LandmarkIdx.LEFT_SHOULDER, LandmarkIdx.RIGHT_SHOULDER),
            (LandmarkIdx.LEFT_SHOULDER, LandmarkIdx.LEFT_ELBOW),
            (LandmarkIdx.LEFT_ELBOW, LandmarkIdx.LEFT_WRIST),
            (LandmarkIdx.RIGHT_SHOULDER, LandmarkIdx.RIGHT_ELBOW),
            (LandmarkIdx.RIGHT_ELBOW, LandmarkIdx.RIGHT_WRIST),
            (LandmarkIdx.LEFT_SHOULDER, LandmarkIdx.LEFT_HIP),
            (LandmarkIdx.RIGHT_SHOULDER, LandmarkIdx.RIGHT_HIP),
            (LandmarkIdx.LEFT_HIP, LandmarkIdx.RIGHT_HIP),
            (LandmarkIdx.LEFT_HIP, LandmarkIdx.LEFT_KNEE),
            (LandmarkIdx.LEFT_KNEE, LandmarkIdx.LEFT_ANKLE),
            (LandmarkIdx.RIGHT_HIP, LandmarkIdx.RIGHT_KNEE),
            (LandmarkIdx.RIGHT_KNEE, LandmarkIdx.RIGHT_ANKLE),
        ]
        
        # Draw connections
        for start_idx, end_idx in connections:
            start = self.get_landmark(landmarks, start_idx, width, height)
            end = self.get_landmark(landmarks, end_idx, width, height)
            if start and end:
                cv2.line(frame, start, end, (0, 255, 0), 2)
        
        # Draw points
        for i in range(33):
            pt = self.get_landmark(landmarks, i, width, height)
            if pt:
                cv2.circle(frame, pt, 4, (0, 0, 255), -1)
    
    def destroy_node(self):
        """Clean up."""
        if self.pose_detector:
            if self.using_tasks_api:
                self.pose_detector.close()
            elif self.using_legacy_api:
                self.pose_detector.close()
        self.cmd_vel_pub.publish(Twist())
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    
    if not MEDIAPIPE_AVAILABLE:
        print("=" * 60)
        print("ERROR: MediaPipe not installed!")
        print("Run: pip3 install mediapipe --break-system-packages")
        print("=" * 60)
        return
    
    node = PostureMonitor()
    
    # Check if initialization succeeded
    if node.pose_detector is None and node.mp_pose is None:
        print("\nNode failed to initialize. See error messages above.")
        node.destroy_node()
        rclpy.shutdown()
        return
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
