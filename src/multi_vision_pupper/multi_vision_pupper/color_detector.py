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
# HSV ranges: H=0-180, S=0-255, V=0-255
# These are tuned to be more permissive for varying lighting conditions
#
# IMPORTANT NOTES:
# - Hue (H) determines the actual color (0=red, 30=yellow, 60=green, 90=cyan, 120=blue, 150=magenta)
# - Saturation (S) is color intensity - low S means washed out/grey
# - Value (V) is brightness - low V means dark/black
#
# For colors that appear "blue" when they shouldn't:
# - Usually means the lighting is too cool/fluorescent
# - Or the saturation threshold is too high (missing pastel colors)

COLOR_DICTIONARY = {
    # Red wraps around in HSV (0 and 180 are both red)
    'red': {
        'lower1': np.array([0, 70, 50]),      # Dark red to bright red
        'upper1': np.array([10, 255, 255]),
        'lower2': np.array([165, 70, 50]),    # Wraps around
        'upper2': np.array([180, 255, 255]),
    },
    'orange': {
        'lower': np.array([10, 70, 50]),
        'upper': np.array([25, 255, 255]),
    },
    'yellow': {
        'lower': np.array([20, 70, 50]),      # Overlaps slightly with orange
        'upper': np.array([40, 255, 255]),
    },
    'green': {
        'lower': np.array([35, 40, 40]),      # Lower saturation for pale greens
        'upper': np.array([90, 255, 255]),    # Wide range to catch teal
    },
    'blue': {
        'lower': np.array([90, 50, 50]),      # Cyan to blue
        'upper': np.array([130, 255, 255]),
    },
    'purple': {
        'lower': np.array([125, 40, 40]),     # Blue-purple to magenta
        'upper': np.array([165, 255, 255]),
    },
    'pink': {
        'lower': np.array([140, 30, 100]),    # Light magenta/pink - needs higher V
        'upper': np.array([175, 200, 255]),   # Lower saturation for pastel pink
    },
    # New additions for your color set
    'black': {
        'lower': np.array([0, 0, 0]),         # Any hue, any saturation
        'upper': np.array([180, 255, 50]),    # But very low value (dark)
    },
    'grey': {
        'lower': np.array([0, 0, 50]),        # Any hue
        'upper': np.array([180, 50, 200]),    # Low saturation (desaturated)
    },
    # White can also be useful
    'white': {
        'lower': np.array([0, 0, 200]),       # Any hue, low saturation, high value
        'upper': np.array([180, 50, 255]),
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
        self.declare_parameter('turn_speed', 0.5)
        
        # Commitment mode parameters
        self.declare_parameter('commitment_mode', True)
        self.declare_parameter('action_duration', 0.5)
        self.declare_parameter('pause_duration', 0.3)
        
        self.visualization = self.get_parameter('visualization').value
        self.min_area = self.get_parameter('min_area').value
        self.color_follow = self.get_parameter('color_follow').value
        self.enabled_colors = self.get_parameter('enabled_colors').value
        self.turn_speed = self.get_parameter('turn_speed').value
        self.commitment_mode = self.get_parameter('commitment_mode').value
        self.action_duration = self.get_parameter('action_duration').value
        self.pause_duration = self.get_parameter('pause_duration').value
        
        # Commitment state machine
        self.state = 'ASSESS'
        self.state_start_time = self.get_clock().now()
        self.current_action = Twist()
        
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
            f"visualization={self.visualization}, follow={self.color_follow}, "
            f"commitment_mode={self.commitment_mode}")
    
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
        if self.color_follow:
            desired_twist = Twist()
            
            if largest_detection:
                color_name, detection = largest_detection
                cx = detection['centroid'][0]
                
                # Calculate yaw rate based on x position
                error = (width/2 - cx) / (width/2)  # Normalized to [-1, 1]
                desired_twist.angular.z = error * self.turn_speed
            
            # === COMMITMENT MODE STATE MACHINE ===
            if self.commitment_mode:
                now = self.get_clock().now()
                elapsed = (now - self.state_start_time).nanoseconds / 1e9
                
                if self.state == 'ASSESS':
                    if largest_detection and abs(desired_twist.angular.z) > 0.1:
                        # Need to turn - commit to this action
                        self.current_action = desired_twist
                        self.state = 'EXECUTE'
                        self.state_start_time = now
                        self.get_logger().info(
                            f"COMMIT: turning toward {color_name}, angular.z={desired_twist.angular.z:.2f} "
                            f"for {self.action_duration}s")
                    else:
                        # Centered or no target - stop
                        self.current_action = Twist()
                        self.cmd_vel_pub.publish(self.current_action)
                
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
                        self.get_logger().info("ASSESS: looking for colors...")
            else:
                # Non-commitment mode - continuous control
                self.cmd_vel_pub.publish(desired_twist)
        
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
