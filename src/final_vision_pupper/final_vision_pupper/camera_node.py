#!/usr/bin/env python3
"""
Camera Node for Mini Pupper OV5647 (Raspberry Pi Camera v1.3)

This node captures frames from the OV5647 camera and publishes them as ROS2 Image messages.
It uses picamera2 which is the modern library for RPi cameras on Ubuntu 22.04+.

Topics:
    /camera/image_raw (sensor_msgs/Image): Raw camera frames
    /camera/image_raw/compressed (sensor_msgs/CompressedImage): Compressed frames (optional)

Parameters:
    width (int): Image width (default: 640)
    height (int): Image height (default: 480)
    fps (int): Frames per second (default: 30)
    flip (bool): Flip image 180 degrees if camera is upside down (default: True)
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CompressedImage
from cv_bridge import CvBridge
import cv2
import numpy as np

# Try to import picamera2, fall back to OpenCV VideoCapture for testing
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False
    print("Warning: picamera2 not available, falling back to OpenCV VideoCapture")


class CameraNode(Node):
    """ROS2 node for OV5647 camera capture and publishing."""
    
    def __init__(self):
        super().__init__('camera_node')
        
        # Declare parameters
        self.declare_parameter('width', 640)
        self.declare_parameter('height', 480)
        self.declare_parameter('fps', 30)
        self.declare_parameter('flip', True)  # Camera often mounted upside down
        self.declare_parameter('publish_compressed', False)
        self.declare_parameter('use_simulation', False)  # For testing without camera
        
        # Get parameters
        self.width = self.get_parameter('width').value
        self.height = self.get_parameter('height').value
        self.fps = self.get_parameter('fps').value
        self.flip = self.get_parameter('flip').value
        self.publish_compressed = self.get_parameter('publish_compressed').value
        self.use_simulation = self.get_parameter('use_simulation').value
        
        # CV Bridge for ROS <-> OpenCV conversion
        self.bridge = CvBridge()
        
        # Publishers
        self.image_pub = self.create_publisher(Image, '/camera/image_raw', 10)
        if self.publish_compressed:
            self.compressed_pub = self.create_publisher(
                CompressedImage, '/camera/image_raw/compressed', 10)
        
        # Initialize camera
        self.camera = None
        self._init_camera()
        
        # Timer for frame capture
        period = 1.0 / self.fps
        self.timer = self.create_timer(period, self.capture_and_publish)
        
        self.get_logger().info(
            f"Camera node started: {self.width}x{self.height} @ {self.fps}fps, "
            f"flip={self.flip}, simulation={self.use_simulation}")
    
    def _init_camera(self):
        """Initialize the camera based on available hardware."""
        if self.use_simulation:
            self.get_logger().info("Running in simulation mode - generating test frames")
            return
        
        if PICAMERA2_AVAILABLE:
            try:
                self.camera = Picamera2()
                config = self.camera.create_preview_configuration(
                    main={"format": 'RGB888', "size": (self.width, self.height)}
                )
                self.camera.configure(config)
                self.camera.start()
                self.get_logger().info("picamera2 initialized successfully")
            except Exception as e:
                self.get_logger().error(f"Failed to initialize picamera2: {e}")
                self.camera = None
        else:
            # Fall back to OpenCV VideoCapture (for webcam testing)
            try:
                self.camera = cv2.VideoCapture(0)
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                self.camera.set(cv2.CAP_PROP_FPS, self.fps)
                self.get_logger().info("OpenCV VideoCapture initialized (fallback mode)")
            except Exception as e:
                self.get_logger().error(f"Failed to initialize OpenCV camera: {e}")
                self.camera = None
    
    def _generate_test_frame(self):
        """Generate a test frame for simulation mode."""
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        # Draw a colored circle that moves
        import time
        t = time.time()
        cx = int(self.width/2 + 100 * np.sin(t))
        cy = int(self.height/2 + 50 * np.cos(t))
        cv2.circle(frame, (cx, cy), 50, (0, 255, 0), -1)
        cv2.putText(frame, "SIMULATION MODE", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        return frame
    
    def capture_and_publish(self):
        """Capture a frame and publish it."""
        frame = None
        
        if self.use_simulation:
            frame = self._generate_test_frame()
        elif self.camera is None:
            return
        elif PICAMERA2_AVAILABLE and isinstance(self.camera, Picamera2):
            try:
                frame = self.camera.capture_array()
            except Exception as e:
                self.get_logger().error(f"Failed to capture frame: {e}")
                return
        else:
            # OpenCV VideoCapture
            ret, frame = self.camera.read()
            if not ret:
                self.get_logger().warn("Failed to capture frame from VideoCapture")
                return
        
        if frame is None:
            return
        
        # Flip if needed (camera often mounted upside down on Mini Pupper)
        if self.flip:
            frame = cv2.rotate(frame, cv2.ROTATE_180)
        
        # Publish raw image
        try:
            msg = self.bridge.cv2_to_imgmsg(frame, encoding='rgb8')
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'camera_frame'
            self.image_pub.publish(msg)
        except Exception as e:
            self.get_logger().error(f"Failed to publish image: {e}")
        
        # Publish compressed if enabled
        if self.publish_compressed:
            try:
                compressed_msg = CompressedImage()
                compressed_msg.header = msg.header
                compressed_msg.format = 'jpeg'
                compressed_msg.data = cv2.imencode('.jpg', 
                    cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))[1].tobytes()
                self.compressed_pub.publish(compressed_msg)
            except Exception as e:
                self.get_logger().error(f"Failed to publish compressed image: {e}")
    
    def destroy_node(self):
        """Clean up camera resources."""
        if self.camera is not None:
            if PICAMERA2_AVAILABLE and isinstance(self.camera, Picamera2):
                self.camera.stop()
            elif hasattr(self.camera, 'release'):
                self.camera.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
