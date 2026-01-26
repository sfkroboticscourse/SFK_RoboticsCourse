#!/usr/bin/env python3
"""
OAK-D Camera Node for Mini Pupper

This node captures frames from the OAK-D camera using DepthAI and publishes them as ROS2 Image messages.
Use this instead of camera_node.py when you have an OAK-D camera attached.

Topics:
    /camera/image_raw (sensor_msgs/Image): Raw camera frames (RGB)
    /camera/depth (sensor_msgs/Image): Depth frames (optional)
    /camera/image_raw/compressed (sensor_msgs/CompressedImage): Compressed frames (optional)

Parameters:
    width (int): Image width (default: 640)
    height (int): Image height (default: 480)
    fps (int): Frames per second (default: 30)
    flip (bool): Flip image 180 degrees if camera is upside down (default: True)
    enable_depth (bool): Enable depth stream (default: False)
    enable_nn (bool): Enable neural network for person detection (default: False)
    nn_blob_path (str): Path to MobileNet SSD blob file
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CompressedImage
from cv_bridge import CvBridge
import cv2
import numpy as np

# Try to import depthai
try:
    import depthai as dai
    DEPTHAI_AVAILABLE = True
except ImportError:
    DEPTHAI_AVAILABLE = False
    print("Warning: depthai not available. Install with: pip3 install depthai")


class OakDCameraNode(Node):
    """ROS2 node for OAK-D camera capture and publishing using DepthAI."""
    
    def __init__(self):
        super().__init__('oakd_camera_node')
        
        # Declare parameters
        self.declare_parameter('width', 640)
        self.declare_parameter('height', 480)
        self.declare_parameter('fps', 30)
        self.declare_parameter('flip', True)
        self.declare_parameter('publish_compressed', False)
        self.declare_parameter('enable_depth', False)
        self.declare_parameter('enable_nn', False)
        self.declare_parameter('nn_blob_path', '')
        
        # Get parameters
        self.width = self.get_parameter('width').value
        self.height = self.get_parameter('height').value
        self.fps = self.get_parameter('fps').value
        self.flip = self.get_parameter('flip').value
        self.publish_compressed = self.get_parameter('publish_compressed').value
        self.enable_depth = self.get_parameter('enable_depth').value
        self.enable_nn = self.get_parameter('enable_nn').value
        self.nn_blob_path = self.get_parameter('nn_blob_path').value
        
        # CV Bridge
        self.bridge = CvBridge()
        
        # Publishers
        self.image_pub = self.create_publisher(Image, '/camera/image_raw', 10)
        if self.publish_compressed:
            self.compressed_pub = self.create_publisher(
                CompressedImage, '/camera/image_raw/compressed', 10)
        if self.enable_depth:
            self.depth_pub = self.create_publisher(Image, '/camera/depth', 10)
        
        # DepthAI device and queues
        self.device = None
        self.rgb_queue = None
        self.depth_queue = None
        self.nn_queue = None
        
        if not DEPTHAI_AVAILABLE:
            self.get_logger().error("DepthAI not available! Install with: pip3 install depthai")
            return
        
        # Initialize OAK-D
        self._init_oakd()
        
        # Timer for frame capture
        period = 1.0 / self.fps
        self.timer = self.create_timer(period, self.capture_and_publish)
        
        self.get_logger().info(
            f"OAK-D camera node started: {self.width}x{self.height} @ {self.fps}fps, "
            f"flip={self.flip}, depth={self.enable_depth}, nn={self.enable_nn}")
    
    def _init_oakd(self):
        """Initialize the OAK-D camera pipeline."""
        try:
            # Create pipeline
            pipeline = dai.Pipeline()
            
            # Create RGB camera node
            cam_rgb = pipeline.create(dai.node.ColorCamera)
            xout_rgb = pipeline.create(dai.node.XLinkOut)
            xout_rgb.setStreamName("rgb")
            
            # RGB camera properties
            cam_rgb.setPreviewSize(self.width, self.height)
            cam_rgb.setInterleaved(False)
            cam_rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.RGB)
            cam_rgb.setFps(self.fps)
            
            # Link RGB
            cam_rgb.preview.link(xout_rgb.input)
            
            # Depth stream (optional)
            if self.enable_depth:
                mono_left = pipeline.create(dai.node.MonoCamera)
                mono_right = pipeline.create(dai.node.MonoCamera)
                stereo = pipeline.create(dai.node.StereoDepth)
                xout_depth = pipeline.create(dai.node.XLinkOut)
                xout_depth.setStreamName("depth")
                
                mono_left.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
                mono_left.setBoardSocket(dai.CameraBoardSocket.LEFT)
                mono_right.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
                mono_right.setBoardSocket(dai.CameraBoardSocket.RIGHT)
                
                stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
                stereo.setDepthAlign(dai.CameraBoardSocket.RGB)
                
                mono_left.out.link(stereo.left)
                mono_right.out.link(stereo.right)
                stereo.depth.link(xout_depth.input)
            
            # Neural network for person detection (optional)
            if self.enable_nn and self.nn_blob_path:
                nn = pipeline.create(dai.node.MobileNetDetectionNetwork)
                xout_nn = pipeline.create(dai.node.XLinkOut)
                xout_nn.setStreamName("nn")
                
                nn.setBlobPath(self.nn_blob_path)
                nn.setConfidenceThreshold(0.5)
                nn.input.setBlocking(False)
                
                cam_rgb.preview.link(nn.input)
                nn.out.link(xout_nn.input)
            
            # Connect to device
            self.device = dai.Device(pipeline)
            
            # Get output queues
            self.rgb_queue = self.device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
            
            if self.enable_depth:
                self.depth_queue = self.device.getOutputQueue(name="depth", maxSize=4, blocking=False)
            
            if self.enable_nn and self.nn_blob_path:
                self.nn_queue = self.device.getOutputQueue(name="nn", maxSize=4, blocking=False)
            
            self.get_logger().info("OAK-D initialized successfully")
            
        except Exception as e:
            self.get_logger().error(f"Failed to initialize OAK-D: {e}")
            self.device = None
    
    def capture_and_publish(self):
        """Capture frames and publish them."""
        if self.device is None or self.rgb_queue is None:
            return
        
        try:
            # Get RGB frame
            rgb_data = self.rgb_queue.tryGet()
            if rgb_data is not None:
                frame = rgb_data.getCvFrame()
                
                # Flip if needed
                if self.flip:
                    frame = cv2.rotate(frame, cv2.ROTATE_180)
                
                # Publish RGB
                try:
                    msg = self.bridge.cv2_to_imgmsg(frame, encoding='rgb8')
                    msg.header.stamp = self.get_clock().now().to_msg()
                    msg.header.frame_id = 'oakd_camera_frame'
                    self.image_pub.publish(msg)
                except Exception as e:
                    self.get_logger().error(f"Failed to publish RGB: {e}")
                
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
                        self.get_logger().error(f"Failed to publish compressed: {e}")
            
            # Get depth frame
            if self.enable_depth and self.depth_queue is not None:
                depth_data = self.depth_queue.tryGet()
                if depth_data is not None:
                    depth_frame = depth_data.getFrame()
                    
                    if self.flip:
                        depth_frame = cv2.rotate(depth_frame, cv2.ROTATE_180)
                    
                    try:
                        depth_msg = self.bridge.cv2_to_imgmsg(depth_frame, encoding='16UC1')
                        depth_msg.header.stamp = self.get_clock().now().to_msg()
                        depth_msg.header.frame_id = 'oakd_camera_frame'
                        self.depth_pub.publish(depth_msg)
                    except Exception as e:
                        self.get_logger().error(f"Failed to publish depth: {e}")
                        
        except Exception as e:
            self.get_logger().error(f"Error in capture loop: {e}")
    
    def destroy_node(self):
        """Clean up OAK-D resources."""
        if self.device is not None:
            self.device.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    
    if not DEPTHAI_AVAILABLE:
        print("ERROR: depthai not installed. Run: pip3 install depthai")
        return
    
    node = OakDCameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
