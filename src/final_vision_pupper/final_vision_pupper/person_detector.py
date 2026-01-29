#!/usr/bin/env python3
"""
Person Detection Node for Mini Pupper

Task 3: Person detection and tracking.
This is based on your working implementation from P1-LetThereBSight, adapted for:
- ROS2 proper topics instead of file-based IPC
- OV5647 camera instead of OAK-D (using picamera2)
- MobileNet SSD running on CPU (OpenCV DNN) instead of OAK's neural accelerator

For better performance on RPi, we use:
- Smaller input size (300x300)
- OpenCV's DNN module with MobileNet SSD
- Option to use TFLite for better performance

Topics:
    Subscribes:
        /camera/image_raw (sensor_msgs/Image): Camera frames
    
    Publishes:
        /vision/person_detected (std_msgs/String): Detection info (JSON)
        /vision/visualization (sensor_msgs/Image): Annotated frame (optional)
        /cmd_vel (geometry_msgs/Twist): Yaw rate to track person

Parameters:
    model_path (str): Path to model file (default: MobileNet SSD from OpenCV)
    confidence_threshold (float): Detection confidence threshold (default: 0.5)
    visualization (bool): Enable visualization output
    control_enabled (bool): Enable movement control
    max_yaw_rate (float): Maximum yaw rate (default: 1.0 rad/s)
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
import os


class PersonDetector(Node):
    """ROS2 node for person detection and tracking using MobileNet SSD."""
    
    # COCO class labels (MobileNet SSD trained on COCO)
    CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
               "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
               "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
               "sofa", "train", "tvmonitor"]
    
    def __init__(self):
        super().__init__('person_detector')
        
        # Parameters
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('visualization', False)
        self.declare_parameter('control_enabled', True)
        self.declare_parameter('max_yaw_rate', 1.0)
        self.declare_parameter('kp', 0.8)  # Proportional gain for yaw control
        self.declare_parameter('model_type', 'hog')  # 'hog' or 'mobilenet_ssd'
        
        # Commitment mode parameters
        self.declare_parameter('commitment_mode', True)
        self.declare_parameter('action_duration', 0.5)
        self.declare_parameter('pause_duration', 0.3)
        
        self.confidence_threshold = self.get_parameter('confidence_threshold').value
        self.visualization = self.get_parameter('visualization').value
        self.control_enabled = self.get_parameter('control_enabled').value
        self.max_yaw_rate = self.get_parameter('max_yaw_rate').value
        self.kp = self.get_parameter('kp').value
        self.model_type = self.get_parameter('model_type').value
        self.commitment_mode = self.get_parameter('commitment_mode').value
        self.action_duration = self.get_parameter('action_duration').value
        self.pause_duration = self.get_parameter('pause_duration').value
        
        # Commitment state machine
        self.state = 'ASSESS'
        self.state_start_time = self.get_clock().now()
        self.current_action = Twist()
        
        # CV Bridge
        self.bridge = CvBridge()
        
        # Initialize detector
        self.net = None
        self.hog = None
        self._init_detector()
        
        # Subscribers
        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10)
        
        # Publishers
        self.person_pub = self.create_publisher(String, '/vision/person_detected', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        if self.visualization:
            self.viz_pub = self.create_publisher(Image, '/vision/visualization', 10)
        
        self.get_logger().info(
            f"Person detector started. Model={self.model_type}, "
            f"threshold={self.confidence_threshold}, control={self.control_enabled}")
    
    def _init_detector(self):
        """Initialize the person detection model."""
        if self.model_type == 'mobilenet_ssd':
            # Use OpenCV's DNN module with MobileNet SSD
            # These model files can be downloaded from:
            # https://github.com/chuanqi305/MobileNet-SSD
            proto_path = os.path.expanduser(
                '~/models/MobileNetSSD_deploy.prototxt')
            model_path = os.path.expanduser(
                '~/models/MobileNetSSD_deploy.caffemodel')
            
            if os.path.exists(proto_path) and os.path.exists(model_path):
                self.net = cv2.dnn.readNetFromCaffe(proto_path, model_path)
                self.get_logger().info("Loaded MobileNet SSD model")
            else:
                self.get_logger().warn(
                    f"MobileNet SSD model not found at {model_path}, "
                    "falling back to HOG detector")
                self.model_type = 'hog'
        
        if self.model_type == 'hog':
            # Fall back to OpenCV's HOG person detector
            # This is slower but doesn't require external model files
            self.hog = cv2.HOGDescriptor()
            self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            self.get_logger().info("Using HOG person detector (no model files needed)")
    
    def detect_persons_mobilenet(self, frame):
        """Detect persons using MobileNet SSD."""
        h, w = frame.shape[:2]
        
        # Prepare input blob
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)), 
            0.007843, (300, 300), 127.5)
        
        self.net.setInput(blob)
        detections = self.net.forward()
        
        persons = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            class_id = int(detections[0, 0, i, 1])
            
            # Check if it's a person with sufficient confidence
            if class_id == 15 and confidence > self.confidence_threshold:  # 15 = person
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                x1, y1, x2, y2 = box.astype("int")
                
                # Clamp to frame bounds
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(w, x2)
                y2 = min(h, y2)
                
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                
                persons.append({
                    'bbox': (x1, y1, x2 - x1, y2 - y1),
                    'center': (cx, cy),
                    'confidence': float(confidence),
                    'area': (x2 - x1) * (y2 - y1)
                })
        
        return persons
    
    def detect_persons_hog(self, frame):
        """Detect persons using HOG detector."""
        # Resize for faster processing
        scale = 0.5
        small = cv2.resize(frame, None, fx=scale, fy=scale)
        
        # Detect
        boxes, weights = self.hog.detectMultiScale(
            small, winStride=(8, 8), padding=(4, 4), scale=1.05)
        
        persons = []
        for i, (x, y, w, h) in enumerate(boxes):
            # Scale back to original size
            x = int(x / scale)
            y = int(y / scale)
            w = int(w / scale)
            h = int(h / scale)
            
            cx = x + w // 2
            cy = y + h // 2
            
            persons.append({
                'bbox': (x, y, w, h),
                'center': (cx, cy),
                'confidence': float(weights[i]) if i < len(weights) else 0.5,
                'area': w * h
            })
        
        return persons
    
    def image_callback(self, msg):
        """Process incoming camera frame."""
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f"Failed to convert image: {e}")
            return
        
        height, width = frame.shape[:2]
        
        # Detect persons
        if self.model_type == 'mobilenet_ssd' and self.net is not None:
            persons = self.detect_persons_mobilenet(frame)
        else:
            persons = self.detect_persons_hog(frame)
        
        # Sort by area (largest/closest first)
        persons.sort(key=lambda x: x['area'], reverse=True)
        
        # Build result message
        result = {
            'detected': len(persons) > 0,
            'count': len(persons),
            'persons': [{
                'bbox': p['bbox'],
                'center': p['center'],
                'confidence': round(p['confidence'], 2)
            } for p in persons]
        }
        
        # Calculate desired action
        desired_twist = Twist()
        
        if persons and self.control_enabled:
            target = persons[0]
            cx = target['center'][0]
            
            # Calculate yaw rate to center person in frame
            error = (width/2 - cx) / (width/2)
            yaw_rate = self.kp * error
            yaw_rate = max(-self.max_yaw_rate, min(self.max_yaw_rate, yaw_rate))
            desired_twist.angular.z = yaw_rate
        
        # Publish detection results
        result_msg = String()
        result_msg.data = json.dumps(result)
        self.person_pub.publish(result_msg)
        
        # === COMMITMENT MODE STATE MACHINE ===
        if self.commitment_mode and self.control_enabled:
            now = self.get_clock().now()
            elapsed = (now - self.state_start_time).nanoseconds / 1e9
            
            if self.state == 'ASSESS':
                if persons and abs(desired_twist.angular.z) > 0.1:
                    # Need to turn - commit to this action
                    self.current_action = desired_twist
                    self.state = 'EXECUTE'
                    self.state_start_time = now
                    self.get_logger().info(
                        f"COMMIT: person detected, turning angular.z={desired_twist.angular.z:.2f} "
                        f"for {self.action_duration}s")
                else:
                    # Centered or no person - stop
                    self.current_action = Twist()
                    self.cmd_vel_pub.publish(self.current_action)
                    if persons:
                        self.get_logger().info(f"Person centered, holding position")
            
            elif self.state == 'EXECUTE':
                if elapsed < self.action_duration:
                    self.cmd_vel_pub.publish(self.current_action)
                else:
                    self.state = 'PAUSE'
                    self.state_start_time = now
                    self.cmd_vel_pub.publish(Twist())
                    self.get_logger().info(f"PAUSE: stopping to reassess for {self.pause_duration}s")
            
            elif self.state == 'PAUSE':
                self.cmd_vel_pub.publish(Twist())
                if elapsed >= self.pause_duration:
                    self.state = 'ASSESS'
                    self.state_start_time = now
                    self.get_logger().info("ASSESS: looking for person...")
        
        elif self.control_enabled:
            # Non-commitment mode - continuous control
            self.cmd_vel_pub.publish(desired_twist)
            if persons:
                self.get_logger().info(
                    f"Person detected: conf={persons[0]['confidence']:.2f}, "
                    f"center={persons[0]['center']}, yaw_rate={desired_twist.angular.z:.3f}")
        
        # Visualization
        if self.visualization:
            viz_frame = frame.copy()
            
            # Draw center line
            cv2.line(viz_frame, (width//2, 0), (width//2, height), (128, 128, 128), 1)
            
            for i, person in enumerate(persons):
                x, y, w, h = person['bbox']
                cx, cy = person['center']
                conf = person['confidence']
                
                # Color: green for target, gray for others
                color = (0, 255, 0) if i == 0 else (128, 128, 128)
                
                # Draw bounding box
                cv2.rectangle(viz_frame, (x, y), (x + w, y + h), color, 2)
                
                # Draw center
                cv2.circle(viz_frame, (cx, cy), 5, color, -1)
                
                # Draw line from center to frame center (tracking error)
                if i == 0:
                    cv2.line(viz_frame, (cx, cy), (width//2, cy), (0, 255, 255), 2)
                
                # Label
                label = f"Person {conf:.2f}"
                if i == 0:
                    label += " [TRACKING]"
                cv2.putText(viz_frame, label, (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # Status text
            status = f"Detected: {len(persons)} person(s)"
            cv2.putText(viz_frame, status, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
            if persons and self.control_enabled:
                yaw_text = f"Yaw rate: {twist.angular.z:.3f} rad/s"
                cv2.putText(viz_frame, yaw_text, (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Publish
            try:
                viz_msg = self.bridge.cv2_to_imgmsg(viz_frame, encoding='bgr8')
                viz_msg.header = msg.header
                self.viz_pub.publish(viz_msg)
            except Exception as e:
                self.get_logger().error(f"Failed to publish visualization: {e}")
    
    def destroy_node(self):
        """Clean up - send stop command."""
        twist = Twist()
        self.cmd_vel_pub.publish(twist)
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = PersonDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
