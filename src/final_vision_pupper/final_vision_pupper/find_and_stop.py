#!/usr/bin/env python3
"""
Find and Stop Node for Mini Pupper

Student Project: Follow a color/shape until found, then STOP and stay stopped.

This node subscribes to shape detection and implements a simple state machine:
1. SEARCHING - Turn/move to find the target
2. APPROACHING - Move toward the target until close enough
3. FOUND - Stop and stay stopped (mission complete!)

The robot will NOT continue tracking after finding the target.
To reset, restart the node.

Usage:
    # First start the camera and shape detector
    ros2 launch final_vision_pupper vision.launch.py mode:=shape target_color:=green
    
    # Then in another terminal, run this node (it will take over control)
    ros2 run final_vision_pupper find_and_stop --ros-args -p target_color:=green

Parameters:
    target_color (str): Color to find (default: 'green')
    target_radius (int): Target size in pixels when "found" (default: 100)
    radius_tolerance (int): How close to target_radius is "good enough" (default: 20)
    search_turn_speed (float): How fast to turn when searching (default: 0.3)
    approach_speed (float): How fast to approach (default: 0.15)
    center_tolerance (float): How centered is "good enough" 0-1 (default: 0.15)
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist
import json


class FindAndStop(Node):
    """Find a colored shape, approach it, then stop permanently."""
    
    def __init__(self):
        super().__init__('find_and_stop')
        
        # Parameters
        self.declare_parameter('target_color', 'green')
        self.declare_parameter('target_radius', 100)  # "Found" when circle is this big
        self.declare_parameter('radius_tolerance', 20)
        self.declare_parameter('search_turn_speed', 0.3)
        self.declare_parameter('approach_speed', 0.15)
        self.declare_parameter('center_tolerance', 0.15)  # 15% of frame width
        
        self.target_color = self.get_parameter('target_color').value
        self.target_radius = self.get_parameter('target_radius').value
        self.radius_tolerance = self.get_parameter('radius_tolerance').value
        self.search_turn_speed = self.get_parameter('search_turn_speed').value
        self.approach_speed = self.get_parameter('approach_speed').value
        self.center_tolerance = self.get_parameter('center_tolerance').value
        
        # State machine
        self.state = 'SEARCHING'  # SEARCHING, APPROACHING, FOUND
        
        # Subscribe to shape detection
        self.detection_sub = self.create_subscription(
            String, '/vision/shape_detected', self.detection_callback, 10)
        
        # Publisher for velocity
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Timer for search behavior (when no detection)
        self.last_detection_time = self.get_clock().now()
        self.search_timer = self.create_timer(0.1, self.search_timeout_check)
        
        self.get_logger().info(f"=== FIND AND STOP ===")
        self.get_logger().info(f"Looking for {self.target_color} circle")
        self.get_logger().info(f"Will stop when radius >= {self.target_radius - self.radius_tolerance}px")
        self.get_logger().info(f"State: {self.state}")
    
    def detection_callback(self, msg):
        """Handle detection results."""
        # If already found, do nothing
        if self.state == 'FOUND':
            return
        
        try:
            data = json.loads(msg.data)
        except json.JSONDecodeError:
            return
        
        twist = Twist()
        
        if data.get('detected') and data.get('circles'):
            self.last_detection_time = self.get_clock().now()
            
            # Get the largest circle
            circle = data['circles'][0]
            cx, cy = circle['center']
            radius = circle['radius']
            
            # Assume 640px width - calculate center error
            frame_width = 640
            center_error = (cx - frame_width/2) / (frame_width/2)  # -1 to 1
            
            # Check if we're close enough (FOUND condition)
            if radius >= self.target_radius - self.radius_tolerance:
                # Check if centered enough
                if abs(center_error) < self.center_tolerance:
                    # FOUND! Stop permanently
                    self.state = 'FOUND'
                    twist = Twist()  # Stop
                    self.cmd_vel_pub.publish(twist)
                    self.get_logger().info("=" * 50)
                    self.get_logger().info(f"🎉 FOUND! {self.target_color} target acquired!")
                    self.get_logger().info(f"Final radius: {radius}px")
                    self.get_logger().info("Stopping permanently. Restart node to search again.")
                    self.get_logger().info("=" * 50)
                    return
                else:
                    # Close enough in distance, but need to center
                    self.state = 'APPROACHING'
                    twist.angular.z = -center_error * 0.5  # Gentle centering
            else:
                # Not close enough - approach
                self.state = 'APPROACHING'
                
                # Turn to center
                twist.angular.z = -center_error * 0.5
                
                # Move forward
                twist.linear.x = self.approach_speed
            
            self.get_logger().info(
                f"[{self.state}] radius={radius}px, center_err={center_error:.2f}, "
                f"vx={twist.linear.x:.2f}, wz={twist.angular.z:.2f}")
        
        else:
            # No detection - handled by search_timeout_check
            pass
        
        if self.state != 'FOUND':
            self.cmd_vel_pub.publish(twist)
    
    def search_timeout_check(self):
        """If no detection for a while, spin to search."""
        if self.state == 'FOUND':
            return
        
        elapsed = (self.get_clock().now() - self.last_detection_time).nanoseconds / 1e9
        
        if elapsed > 0.5:  # No detection for 0.5 seconds
            self.state = 'SEARCHING'
            twist = Twist()
            twist.angular.z = self.search_turn_speed  # Spin to search
            self.cmd_vel_pub.publish(twist)
            
            if int(elapsed) % 2 == 0:  # Log every 2 seconds
                self.get_logger().info(f"[SEARCHING] No {self.target_color} detected, spinning...")
    
    def destroy_node(self):
        """Stop robot on shutdown."""
        twist = Twist()
        self.cmd_vel_pub.publish(twist)
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = FindAndStop()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
