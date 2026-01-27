#!/usr/bin/env python3
"""
HSV Calibration Tool for Mini Pupper

This tool helps you see what HSV values the camera is actually detecting.
Point the camera at a colored object and see the HSV values in real-time.

Usage:
    ros2 run multi_vision_pupper hsv_calibrator

The tool will:
1. Subscribe to /camera/image_raw
2. Show the center pixel's HSV values
3. Show a color swatch of what that HSV looks like
4. Print recommendations for color ranges

Press Ctrl+C to exit.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np


class HSVCalibrator(Node):
    """Tool to help calibrate HSV color ranges."""
    
    def __init__(self):
        super().__init__('hsv_calibrator')
        
        self.bridge = CvBridge()
        
        # Parameters
        self.declare_parameter('sample_size', 20)  # Size of center sample area
        self.sample_size = self.get_parameter('sample_size').value
        
        # Subscribe to camera
        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self.image_callback, 10)
        
        # Store recent HSV values for averaging
        self.hsv_history = []
        self.history_size = 10
        
        self.get_logger().info("HSV Calibrator started!")
        self.get_logger().info("Point the camera at a colored object.")
        self.get_logger().info("The center region's HSV values will be displayed.")
        self.get_logger().info("-" * 50)
    
    def image_callback(self, msg):
        """Process image and extract HSV from center."""
        try:
            # Convert to OpenCV format
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
        except Exception as e:
            self.get_logger().error(f"Failed to convert image: {e}")
            return
        
        height, width = frame.shape[:2]
        
        # Sample center region
        cx, cy = width // 2, height // 2
        half = self.sample_size // 2
        
        # Extract center region
        region = hsv[cy-half:cy+half, cx-half:cx+half]
        
        # Calculate mean HSV values
        mean_h = int(np.mean(region[:, :, 0]))
        mean_s = int(np.mean(region[:, :, 1]))
        mean_v = int(np.mean(region[:, :, 2]))
        
        # Also get min/max for range estimation
        min_h, max_h = int(np.min(region[:, :, 0])), int(np.max(region[:, :, 0]))
        min_s, max_s = int(np.min(region[:, :, 1])), int(np.max(region[:, :, 1]))
        min_v, max_v = int(np.min(region[:, :, 2])), int(np.max(region[:, :, 2]))
        
        # Add to history for smoothing
        self.hsv_history.append((mean_h, mean_s, mean_v))
        if len(self.hsv_history) > self.history_size:
            self.hsv_history.pop(0)
        
        # Calculate smoothed average
        avg_h = int(np.mean([h[0] for h in self.hsv_history]))
        avg_s = int(np.mean([h[1] for h in self.hsv_history]))
        avg_v = int(np.mean([h[2] for h in self.hsv_history]))
        
        # Determine likely color name
        color_name = self.guess_color(avg_h, avg_s, avg_v)
        
        # Print results
        self.get_logger().info(
            f"HSV: [{avg_h:3d}, {avg_s:3d}, {avg_v:3d}] | "
            f"Range: H[{min_h:3d}-{max_h:3d}] S[{min_s:3d}-{max_s:3d}] V[{min_v:3d}-{max_v:3d}] | "
            f"Likely: {color_name}"
        )
        
        # Suggest range for this color
        margin_h = 15
        margin_sv = 50
        suggested_lower = f"[{max(0, avg_h - margin_h)}, {max(0, avg_s - margin_sv)}, {max(0, avg_v - margin_sv)}]"
        suggested_upper = f"[{min(180, avg_h + margin_h)}, 255, 255]"
        
        self.get_logger().info(
            f"  Suggested range: lower={suggested_lower}, upper={suggested_upper}"
        )
    
    def guess_color(self, h, s, v):
        """Guess the color name based on HSV values."""
        # Check for black/grey/white first (based on S and V)
        if v < 50:
            return "BLACK"
        if s < 50:
            if v > 200:
                return "WHITE"
            return "GREY"
        
        # Now check hue for chromatic colors
        if h < 10 or h > 165:
            return "RED"
        elif h < 25:
            return "ORANGE"
        elif h < 40:
            return "YELLOW"
        elif h < 90:
            return "GREEN"
        elif h < 130:
            return "BLUE"
        elif h < 150:
            return "PURPLE"
        else:
            return "PINK/MAGENTA"


def main(args=None):
    rclpy.init(args=args)
    node = HSVCalibrator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
