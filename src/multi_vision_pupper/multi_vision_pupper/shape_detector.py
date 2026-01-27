#!/usr/bin/env python3
"""
Shape Detection Node for Mini Pupper

Task 2: Detect colored circle stickers and control movement based on bounding box size.
- Move FORWARD if the detected circle is smaller than target size (too far)
- Move BACKWARD if the detected circle is larger than target size (too close)
- Turn LEFT/RIGHT to center the circle

This is a classic visual servoing approach that works well for teaching.

Topics:
    Subscribes:
        /camera/image_raw (sensor_msgs/Image): Camera frames
    
    Publishes:
        /vision/shape_detected (std_msgs/String): Detection info (JSON)
        /vision/visualization (sensor_msgs/Image): Annotated frame (optional)
        /cmd_vel (geometry_msgs/Twist): Velocity commands

Parameters:
    target_color (str): Color of the circle sticker to track (default: 'green')
    target_radius (int): Target bounding box radius in pixels (default: 80)
    radius_tolerance (int): Tolerance for radius (default: 15)
    visualization (bool): Enable visualization output
    forward_speed (float): Max forward/backward speed (default: 0.1)
    turn_speed (float): Max turning speed (default: 0.5)
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


# Color ranges for circle stickers (same as color_detector)
STICKER_COLORS = {
    'red': {
        'lower1': np.array([0, 120, 100]),
        'upper1': np.array([10, 255, 255]),
        'lower2': np.array([160, 120, 100]),
        'upper2': np.array([180, 255, 255]),
    },
    'orange': {
        'lower': np.array([10, 120, 100]),
        'upper': np.array([25, 255, 255]),
    },
    'yellow': {
        'lower': np.array([25, 120, 100]),
        'upper': np.array([35, 255, 255]),
    },
    'green': {
        'lower': np.array([35, 120, 100]),
        'upper': np.array([85, 255, 255]),
    },
    'blue': {
        'lower': np.array([85, 120, 100]),
        'upper': np.array([130, 255, 255]),
    },
}


class ShapeDetector(Node):
    """ROS2 node for detecting colored circle stickers and visual servoing."""
    
    def __init__(self):
        super().__init__('shape_detector')
        
        # Parameters
        self.declare_parameter('target_color', 'green')
        self.declare_parameter('target_radius', 80)  # Target bounding box size in pixels
        self.declare_parameter('radius_tolerance', 15)
        self.declare_parameter('visualization', False)
        self.declare_parameter('forward_speed', 0.15)
        self.declare_parameter('turn_speed', 0.5)
        self.declare_parameter('min_circularity', 0.7)  # 0-1, 1 is perfect circle
        self.declare_parameter('control_enabled', True)  # Enable movement control
        
        # Commitment mode parameters
        self.declare_parameter('commitment_mode', True)  # Enable step-based movement
        self.declare_parameter('action_duration', 0.5)   # How long to execute action (seconds)
        self.declare_parameter('pause_duration', 0.3)    # How long to pause and reassess (seconds)
        
        self.target_color = self.get_parameter('target_color').value
        self.target_radius = self.get_parameter('target_radius').value
        self.radius_tolerance = self.get_parameter('radius_tolerance').value
        self.visualization = self.get_parameter('visualization').value
        self.forward_speed = self.get_parameter('forward_speed').value
        self.turn_speed = self.get_parameter('turn_speed').value
        self.min_circularity = self.get_parameter('min_circularity').value
        self.control_enabled = self.get_parameter('control_enabled').value
        self.commitment_mode = self.get_parameter('commitment_mode').value
        self.action_duration = self.get_parameter('action_duration').value
        self.pause_duration = self.get_parameter('pause_duration').value
        
        # Commitment state machine
        self.state = 'ASSESS'  # ASSESS, EXECUTE, PAUSE
        self.state_start_time = self.get_clock().now()
        self.current_action = Twist()  # The committed action
        
        # CV Bridge
        self.bridge = CvBridge()
        
        # Subscribers
        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10)
        
        # Publishers
        self.shape_pub = self.create_publisher(String, '/vision/shape_detected', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        if self.visualization:
            self.viz_pub = self.create_publisher(Image, '/vision/visualization', 10)
        
        self.get_logger().info(
            f"Shape detector started. Tracking {self.target_color} circles, "
            f"target_radius={self.target_radius}px, control={self.control_enabled}")
    
    def detect_circles(self, hsv_frame, color_params):
        """
        Detect circular shapes of the specified color.
        Returns list of circle detections with position, radius, and circularity.
        """
        # Create color mask
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
        
        circles = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 200:  # Skip tiny contours
                continue
            
            # Calculate circularity: 4*pi*area / perimeter^2
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue
            circularity = 4 * np.pi * area / (perimeter * perimeter)
            
            # Only accept circular shapes
            if circularity >= self.min_circularity:
                # Fit minimum enclosing circle
                (cx, cy), radius = cv2.minEnclosingCircle(contour)
                cx, cy, radius = int(cx), int(cy), int(radius)
                
                circles.append({
                    'center': (cx, cy),
                    'radius': radius,
                    'area': area,
                    'circularity': circularity,
                    'contour': contour
                })
        
        # Sort by area (largest first)
        circles.sort(key=lambda x: x['area'], reverse=True)
        return circles
    
    def compute_control(self, circle, frame_width, frame_height):
        """
        Compute velocity command to track the circle.
        
        Returns (linear_x, angular_z):
            linear_x: positive = forward, negative = backward
            angular_z: positive = turn left, negative = turn right
        """
        cx, cy = circle['center']
        radius = circle['radius']
        
        # Centering control (turn left/right)
        # Error is positive when target is on the left
        x_error = (frame_width/2 - cx) / (frame_width/2)  # Normalized [-1, 1]
        angular_z = x_error * self.turn_speed
        
        # Distance control (forward/backward based on circle size)
        radius_error = self.target_radius - radius
        
        if abs(radius_error) < self.radius_tolerance:
            # Within tolerance, don't move forward/backward
            linear_x = 0.0
            distance_status = "OK"
        elif radius_error > 0:
            # Circle is smaller than target = too far away = move forward
            # Use fixed forward speed (like teleop: 0.15)
            linear_x = self.forward_speed
            distance_status = "TOO_FAR"
        else:
            # Circle is larger than target = too close = move backward
            # Use fixed backward speed (negative)
            linear_x = -self.forward_speed
            distance_status = "TOO_CLOSE"
        
        return linear_x, angular_z, distance_status
    
    def image_callback(self, msg):
        """Process incoming camera frame with commitment-based control."""
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        except Exception as e:
            self.get_logger().error(f"Failed to convert image: {e}")
            return
        
        height, width = frame.shape[:2]
        
        # Check if target color is valid
        if self.target_color not in STICKER_COLORS:
            self.get_logger().error(f"Unknown target color: {self.target_color}")
            return
        
        # Detect circles of target color
        circles = self.detect_circles(hsv, STICKER_COLORS[self.target_color])
        
        # Build result message
        result = {
            'detected': False,
            'color': self.target_color,
            'circles': []
        }
        
        distance_status = "NO_TARGET"
        desired_twist = Twist()  # What we WANT to do based on current detection
        
        if circles:
            result['detected'] = True
            result['circles'] = [{
                'center': c['center'],
                'radius': c['radius'],
                'circularity': round(c['circularity'], 2)
            } for c in circles]
            
            # Track the largest circle
            target = circles[0]
            
            if self.control_enabled:
                linear_x, angular_z, distance_status = self.compute_control(
                    target, width, height)
                desired_twist.linear.x = linear_x
                desired_twist.angular.z = angular_z
        
        # Publish detection result
        result_msg = String()
        result_msg.data = json.dumps(result)
        self.shape_pub.publish(result_msg)
        
        # === COMMITMENT MODE STATE MACHINE ===
        if self.commitment_mode and self.control_enabled:
            now = self.get_clock().now()
            elapsed = (now - self.state_start_time).nanoseconds / 1e9  # seconds
            
            if self.state == 'ASSESS':
                # Look at the scene and decide what to do
                if circles and distance_status != "OK":
                    # Need to move - commit to this action
                    self.current_action = desired_twist
                    self.state = 'EXECUTE'
                    self.state_start_time = now
                    self.get_logger().info(
                        f"COMMIT: {distance_status} -> linear.x={desired_twist.linear.x:.2f}, "
                        f"angular.z={desired_twist.angular.z:.2f} for {self.action_duration}s")
                elif circles and distance_status == "OK":
                    # Target acquired, just do minor adjustments for turning
                    if abs(desired_twist.angular.z) > 0.1:
                        self.current_action = Twist()
                        self.current_action.angular.z = desired_twist.angular.z
                        self.state = 'EXECUTE'
                        self.state_start_time = now
                    else:
                        # We're good! Stay stopped
                        self.current_action = Twist()
                        self.cmd_vel_pub.publish(self.current_action)
                else:
                    # No target - stop
                    self.current_action = Twist()
                    self.cmd_vel_pub.publish(self.current_action)
            
            elif self.state == 'EXECUTE':
                # Execute the committed action
                if elapsed < self.action_duration:
                    self.cmd_vel_pub.publish(self.current_action)
                else:
                    # Done executing - pause
                    self.state = 'PAUSE'
                    self.state_start_time = now
                    # Send stop command
                    stop = Twist()
                    self.cmd_vel_pub.publish(stop)
                    self.get_logger().info(f"PAUSE: stopping to reassess for {self.pause_duration}s")
            
            elif self.state == 'PAUSE':
                # Pausing to let robot settle and reassess
                stop = Twist()
                self.cmd_vel_pub.publish(stop)
                
                if elapsed >= self.pause_duration:
                    # Done pausing - reassess
                    self.state = 'ASSESS'
                    self.state_start_time = now
                    self.get_logger().info("ASSESS: looking at target...")
        
        elif self.control_enabled:
            # Non-commitment mode - continuous control (old behavior)
            self.cmd_vel_pub.publish(desired_twist)
            if circles:
                self.get_logger().info(
                    f"{self.target_color} circle: radius={circles[0]['radius']}px, "
                    f"status={distance_status}, linear.x={desired_twist.linear.x:.3f}, "
                    f"angular.z={desired_twist.angular.z:.3f}")
        
        # Visualization
        if self.visualization:
            viz_frame = frame_bgr.copy()
            
            # Draw target zone
            center_x, center_y = width // 2, height // 2
            cv2.circle(viz_frame, (center_x, center_y), self.target_radius, 
                      (0, 255, 0), 2)  # Target size ring
            cv2.circle(viz_frame, (center_x, center_y), 
                      self.target_radius - self.radius_tolerance, (255, 255, 0), 1)
            cv2.circle(viz_frame, (center_x, center_y), 
                      self.target_radius + self.radius_tolerance, (255, 255, 0), 1)
            
            # Draw detected circles
            for i, circle in enumerate(circles):
                cx, cy = circle['center']
                radius = circle['radius']
                
                # Color based on status
                if i == 0:  # Target circle
                    if distance_status == "OK":
                        color = (0, 255, 0)  # Green = good
                    elif distance_status == "TOO_FAR":
                        color = (0, 165, 255)  # Orange = move forward
                    else:
                        color = (0, 0, 255)  # Red = move backward
                else:
                    color = (128, 128, 128)  # Gray for non-primary detections
                
                cv2.circle(viz_frame, (cx, cy), radius, color, 2)
                cv2.circle(viz_frame, (cx, cy), 3, color, -1)
                
                # Label
                label = f"r={radius} {'[TARGET]' if i == 0 else ''}"
                cv2.putText(viz_frame, label, (cx - 40, cy - radius - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Status text
            cv2.putText(viz_frame, f"Status: {distance_status}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(viz_frame, f"Target: {self.target_color} r={self.target_radius}px", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Publish
            try:
                viz_msg = self.bridge.cv2_to_imgmsg(viz_frame, encoding='bgr8')
                viz_msg.header = msg.header
                self.viz_pub.publish(viz_msg)
            except Exception as e:
                self.get_logger().error(f"Failed to publish visualization: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = ShapeDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Send stop command
        twist = Twist()
        node.cmd_vel_pub.publish(twist)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
