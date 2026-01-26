#!/usr/bin/env python3
"""
Color Detection Node for Mini Pupper

Task 1: Detect specific colors from a predefined dictionary and announce what colors are detected.

This node subscribes to camera images and detects colors from the configured dictionary.
It publishes detection results and optionally visualization images.

Topics:
    Subscribes:
        /camera/image_raw (sensor_msgs/Image): Camera frames
    
    Publishes:
        /vision/colors_detected (std_msgs/String): JSON list of detected colors
        /vision/visualization (sensor_msgs/Image): Annotated frame (if visualization enabled)
        /cmd_vel (geometry_msgs/Twist): Velocity commands (optional, for color-following mode)

Parameters:
    visualization (bool): Enable visualization output (default: False for onboard, True for PC)
    min_area (int): Minimum contour area to consider (default: 500)
    color_follow (bool): If True, turn towards largest detected color region
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


# Color dictionary: name -> (lower_hsv, upper_hsv)
# These are tuned for typical indoor lighting - may need adjustment
COLOR_DICTIONARY = {
    'red': {
        'lower1': np.array([0, 100, 100]),
        'upper1': np.array([10, 255, 255]),
        'lower2': np.array([160, 100, 100]),  # Red wraps around in HSV
        'upper2': np.array([180, 255, 255]),
    },
    'orange': {
        'lower': np.array([10, 100, 100]),
        'upper': np.array([25, 255, 255]),
    },
    'yellow': {
        'lower': np.array([25, 100, 100]),
        'upper': np.array([35, 255, 255]),
    },
    'green': {
        'lower': np.array([35, 100, 100]),
        'upper': np.array([85, 255, 255]),
    },
    'blue': {
        'lower': np.array([85, 100, 100]),
        'upper': np.array([130, 255, 255]),
    },
    'purple': {
        'lower': np.array([130, 100, 100]),
        'upper': np.array([160, 255, 255]),
    },
    'pink': {
        'lower': np.array([140, 50, 100]),
        'upper': np.array([170, 255, 255]),
    },
}


class ColorDetector(Node):
    """ROS2 node for detecting colors from a predefined dictionary."""
    
    def __init__(self):
        super().__init__('color_detector')
        
        # Parameters
        self.declare_parameter('visualization', False)
        self.declare_parameter('min_area', 500)
        self.declare_parameter('color_follow', False)
        self.declare_parameter('enabled_colors', list(COLOR_DICTIONARY.keys()))
        
        self.visualization = self.get_parameter('visualization').value
        self.min_area = self.get_parameter('min_area').value
        self.color_follow = self.get_parameter('color_follow').value
        self.enabled_colors = self.get_parameter('enabled_colors').value
        
        # CV Bridge
        self.bridge = CvBridge()
        
        # Subscribers
        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10)
        
        # Publishers
        self.color_pub = self.create_publisher(String, '/vision/colors_detected', 10)
        if self.visualization:
            self.viz_pub = self.create_publisher(Image, '/vision/visualization', 10)
        if self.color_follow:
            self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        self.get_logger().info(
            f"Color detector started. Detecting: {self.enabled_colors}, "
            f"visualization={self.visualization}, follow={self.color_follow}")
    
    def detect_color(self, hsv_frame, color_name, color_params):
        """
        Detect a specific color in the HSV frame.
        Returns list of (contour, area, centroid) tuples.
        """
        detections = []
        
        # Handle red which wraps around in HSV
        if 'lower1' in color_params:
            mask1 = cv2.inRange(hsv_frame, color_params['lower1'], color_params['upper1'])
            mask2 = cv2.inRange(hsv_frame, color_params['lower2'], color_params['upper2'])
            mask = cv2.bitwise_or(mask1, mask2)
        else:
            mask = cv2.inRange(hsv_frame, color_params['lower'], color_params['upper'])
        
        # Clean up mask
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area >= self.min_area:
                M = cv2.moments(contour)
                if M['m00'] > 0:
                    cx = int(M['m10'] / M['m00'])
                    cy = int(M['m01'] / M['m00'])
                    detections.append({
                        'contour': contour,
                        'area': area,
                        'centroid': (cx, cy),
                        'bbox': cv2.boundingRect(contour)
                    })
        
        return detections
    
    def image_callback(self, msg):
        """Process incoming camera frame."""
        try:
            # Convert ROS Image to OpenCV
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        except Exception as e:
            self.get_logger().error(f"Failed to convert image: {e}")
            return
        
        height, width = frame.shape[:2]
        all_detections = {}
        largest_detection = None
        largest_area = 0
        
        # Detect each enabled color
        for color_name in self.enabled_colors:
            if color_name not in COLOR_DICTIONARY:
                continue
            
            detections = self.detect_color(hsv, color_name, COLOR_DICTIONARY[color_name])
            
            if detections:
                all_detections[color_name] = [{
                    'area': d['area'],
                    'centroid': d['centroid'],
                    'bbox': d['bbox']
                } for d in detections]
                
                # Track largest for following mode
                for d in detections:
                    if d['area'] > largest_area:
                        largest_area = d['area']
                        largest_detection = (color_name, d)
        
        # Publish detection results
        result_msg = String()
        if all_detections:
            colors_found = list(all_detections.keys())
            result = {
                'detected': True,
                'colors': colors_found,
                'details': {k: [{'area': d['area'], 'centroid': d['centroid']} 
                               for d in v] for k, v in all_detections.items()}
            }
            self.get_logger().info(f"Colors detected: {colors_found}")
        else:
            result = {'detected': False, 'colors': []}
        
        result_msg.data = json.dumps(result)
        self.color_pub.publish(result_msg)
        
        # Color following mode - turn towards largest color region
        if self.color_follow and largest_detection:
            color_name, detection = largest_detection
            cx = detection['centroid'][0]
            
            # Calculate yaw rate based on x position
            # Negative when target is on left, positive when on right
            error = (cx - width/2) / (width/2)  # Normalized to [-1, 1]
            yaw_rate = -error * 0.8  # Proportional control, max 0.8 rad/s
            
            twist = Twist()
            twist.angular.z = yaw_rate
            self.cmd_vel_pub.publish(twist)
        
        # Visualization
        if self.visualization:
            viz_frame = frame_bgr.copy()
            
            # Draw all detections
            color_bgr_map = {
                'red': (0, 0, 255),
                'orange': (0, 165, 255),
                'yellow': (0, 255, 255),
                'green': (0, 255, 0),
                'blue': (255, 0, 0),
                'purple': (128, 0, 128),
                'pink': (203, 192, 255),
            }
            
            for color_name, detections in all_detections.items():
                bgr = color_bgr_map.get(color_name, (255, 255, 255))
                for det in detections:
                    x, y, w, h = det['bbox']
                    cv2.rectangle(viz_frame, (x, y), (x+w, y+h), bgr, 2)
                    cv2.putText(viz_frame, f"{color_name}", (x, y-10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, bgr, 2)
                    cv2.circle(viz_frame, det['centroid'], 5, bgr, -1)
            
            # Publish visualization
            try:
                viz_msg = self.bridge.cv2_to_imgmsg(viz_frame, encoding='bgr8')
                viz_msg.header = msg.header
                self.viz_pub.publish(viz_msg)
            except Exception as e:
                self.get_logger().error(f"Failed to publish visualization: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = ColorDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
