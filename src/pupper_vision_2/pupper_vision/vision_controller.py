#!/usr/bin/env python3
"""
Vision Controller for Mini Pupper

This node acts as a velocity command multiplexer/filter:
- Subscribes to /cmd_vel from vision nodes
- Applies safety limits and smoothing
- Publishes to the robot's actual cmd_vel topic

This mirrors your original control.py approach but as a proper ROS2 node.

Features:
- Velocity smoothing to prevent jerky motion
- Safety limits (max linear/angular velocities)
- Deadzone filtering
- Optional velocity scaling
- Watchdog timer (stops if no commands received)

Topics:
    Subscribes:
        /cmd_vel (geometry_msgs/Twist): Commands from vision nodes
    
    Publishes:
        /robot/cmd_vel (geometry_msgs/Twist): Filtered commands to robot
        (or directly to /cmd_vel if no multiplexer needed)

Parameters:
    max_linear (float): Maximum linear velocity (default: 0.3 m/s)
    max_angular (float): Maximum angular velocity (default: 1.0 rad/s)
    smoothing (float): Exponential smoothing factor 0-1 (default: 0.3)
    deadzone (float): Velocity deadzone (default: 0.01)
    timeout (float): Command timeout in seconds (default: 0.5)
    publish_topic (str): Output topic (default: /cmd_vel - passthrough mode)
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import time


class VisionController(Node):
    """ROS2 node for filtering and forwarding velocity commands."""
    
    def __init__(self):
        super().__init__('vision_controller')
        
        # Parameters
        self.declare_parameter('max_linear', 0.3)
        self.declare_parameter('max_angular', 1.0)
        self.declare_parameter('smoothing', 0.3)  # Lower = more smoothing
        self.declare_parameter('deadzone', 0.01)
        self.declare_parameter('timeout', 0.5)
        self.declare_parameter('input_topic', '/vision/cmd_vel')
        self.declare_parameter('output_topic', '/cmd_vel')
        self.declare_parameter('passthrough', False)  # If True, no filtering
        
        self.max_linear = self.get_parameter('max_linear').value
        self.max_angular = self.get_parameter('max_angular').value
        self.smoothing = self.get_parameter('smoothing').value
        self.deadzone = self.get_parameter('deadzone').value
        self.timeout = self.get_parameter('timeout').value
        self.input_topic = self.get_parameter('input_topic').value
        self.output_topic = self.get_parameter('output_topic').value
        self.passthrough = self.get_parameter('passthrough').value
        
        # State
        self.smoothed_linear_x = 0.0
        self.smoothed_angular_z = 0.0
        self.last_cmd_time = time.time()
        
        # Subscribers
        self.cmd_sub = self.create_subscription(
            Twist, self.input_topic, self.cmd_callback, 10)
        
        # Publishers
        self.cmd_pub = self.create_publisher(Twist, self.output_topic, 10)
        
        # Timer for watchdog and publishing
        self.timer = self.create_timer(0.04, self.timer_callback)  # 25 Hz
        
        self.get_logger().info(
            f"Vision controller started. {self.input_topic} -> {self.output_topic}, "
            f"max_v={self.max_linear}, max_w={self.max_angular}, "
            f"smoothing={self.smoothing}, passthrough={self.passthrough}")
    
    def cmd_callback(self, msg):
        """Process incoming velocity command."""
        self.last_cmd_time = time.time()
        
        if self.passthrough:
            # Direct passthrough, just clamp
            out_msg = Twist()
            out_msg.linear.x = max(-self.max_linear, 
                                   min(self.max_linear, msg.linear.x))
            out_msg.angular.z = max(-self.max_angular, 
                                    min(self.max_angular, msg.angular.z))
            self.cmd_pub.publish(out_msg)
            return
        
        # Apply limits
        linear_x = max(-self.max_linear, min(self.max_linear, msg.linear.x))
        angular_z = max(-self.max_angular, min(self.max_angular, msg.angular.z))
        
        # Apply deadzone
        if abs(linear_x) < self.deadzone:
            linear_x = 0.0
        if abs(angular_z) < self.deadzone:
            angular_z = 0.0
        
        # Exponential smoothing
        self.smoothed_linear_x = (self.smoothing * linear_x + 
                                  (1 - self.smoothing) * self.smoothed_linear_x)
        self.smoothed_angular_z = (self.smoothing * angular_z + 
                                   (1 - self.smoothing) * self.smoothed_angular_z)
    
    def timer_callback(self):
        """Periodic callback to publish commands and check watchdog."""
        # Check timeout
        if time.time() - self.last_cmd_time > self.timeout:
            # No recent commands, decay to zero
            self.smoothed_linear_x *= 0.9
            self.smoothed_angular_z *= 0.9
            
            # Stop completely if very slow
            if abs(self.smoothed_linear_x) < 0.01:
                self.smoothed_linear_x = 0.0
            if abs(self.smoothed_angular_z) < 0.01:
                self.smoothed_angular_z = 0.0
        
        # Publish smoothed command
        if not self.passthrough:
            out_msg = Twist()
            out_msg.linear.x = self.smoothed_linear_x
            out_msg.angular.z = self.smoothed_angular_z
            self.cmd_pub.publish(out_msg)
    
    def destroy_node(self):
        """Send stop command before shutting down."""
        stop_msg = Twist()
        self.cmd_pub.publish(stop_msg)
        self.get_logger().info("Vision controller stopped, sent stop command")
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = VisionController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
