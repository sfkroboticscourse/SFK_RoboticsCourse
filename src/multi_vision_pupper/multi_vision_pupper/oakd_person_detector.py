#!/usr/bin/env python3
"""
OAK-D Person Detector for Mini Pupper

This uses the OAK-D's built-in neural accelerator (Myriad X) to run MobileNet SSD
for person detection. Much faster than CPU-based detection!

This is essentially your original P1-LetThereBSight implementation, but as a proper ROS2 node.

Topics:
    Publishes:
        /vision/person_detected (std_msgs/String): Detection info (JSON)
        /vision/visualization (sensor_msgs/Image): Annotated frame (optional)
        /cmd_vel (geometry_msgs/Twist): Yaw rate to track person
        /camera/image_raw (sensor_msgs/Image): Raw camera frames

Parameters:
    nn_blob_path (str): Path to MobileNet SSD blob file
    confidence_threshold (float): Detection confidence threshold (default: 0.5)
    visualization (bool): Enable visualization output
    control_enabled (bool): Enable movement control
    max_yaw_rate (float): Maximum yaw rate (default: 1.0 rad/s)
    flip (bool): Flip image 180 degrees
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

try:
    import depthai as dai
    DEPTHAI_AVAILABLE = True
except ImportError:
    DEPTHAI_AVAILABLE = False
    print("Warning: depthai not available. Install with: pip3 install depthai")


class OakDPersonDetector(Node):
    """
    ROS2 node for person detection using OAK-D's neural accelerator.
    
    This runs MobileNet SSD on the Myriad X chip for fast inference.
    Based on the working P1-LetThereBSight implementation.
    """
    
    # MobileNet SSD labels (COCO)
    LABELS = ["background", "aeroplane", "bicycle", "bird", "boat",
              "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
              "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
              "sofa", "train", "tvmonitor"]
    
    def __init__(self):
        super().__init__('oakd_person_detector')
        
        # Parameters
        self.declare_parameter('nn_blob_path', 
            os.path.expanduser('~/models/mobilenet-ssd_openvino_2021.4_6shave.blob'))
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('visualization', False)
        self.declare_parameter('control_enabled', True)
        self.declare_parameter('max_yaw_rate', 1.0)
        self.declare_parameter('kp', 0.8)
        self.declare_parameter('flip', True)
        self.declare_parameter('width', 300)  # MobileNet SSD input size
        self.declare_parameter('height', 300)
        self.declare_parameter('preview_width', 640)  # Preview/visualization size
        self.declare_parameter('preview_height', 480)
        self.declare_parameter('fps', 30)
        
        # Commitment mode parameters
        self.declare_parameter('commitment_mode', True)
        self.declare_parameter('action_duration', 0.5)
        self.declare_parameter('pause_duration', 0.3)
        
        self.nn_blob_path = self.get_parameter('nn_blob_path').value
        self.confidence_threshold = self.get_parameter('confidence_threshold').value
        self.visualization = self.get_parameter('visualization').value
        self.control_enabled = self.get_parameter('control_enabled').value
        self.max_yaw_rate = self.get_parameter('max_yaw_rate').value
        self.kp = self.get_parameter('kp').value
        self.flip = self.get_parameter('flip').value
        self.nn_width = self.get_parameter('width').value
        self.nn_height = self.get_parameter('height').value
        self.preview_width = self.get_parameter('preview_width').value
        self.preview_height = self.get_parameter('preview_height').value
        self.fps = self.get_parameter('fps').value
        self.commitment_mode = self.get_parameter('commitment_mode').value
        self.action_duration = self.get_parameter('action_duration').value
        self.pause_duration = self.get_parameter('pause_duration').value
        
        # Commitment state machine
        self.state = 'ASSESS'
        self.state_start_time = self.get_clock().now()
        self.current_action = Twist()
        
        # CV Bridge
        self.bridge = CvBridge()
        
        # Publishers
        self.person_pub = self.create_publisher(String, '/vision/person_detected', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.image_pub = self.create_publisher(Image, '/camera/image_raw', 10)
        if self.visualization:
            self.viz_pub = self.create_publisher(Image, '/vision/visualization', 10)
        
        # DepthAI
        self.device = None
        self.rgb_queue = None
        self.nn_queue = None
        
        if not DEPTHAI_AVAILABLE:
            self.get_logger().error("DepthAI not available!")
            return
        
        if not os.path.exists(self.nn_blob_path):
            self.get_logger().error(f"NN blob not found: {self.nn_blob_path}")
            self.get_logger().error("Download from: https://github.com/luxonis/depthai-model-zoo")
            return
        
        # Initialize pipeline
        self._init_pipeline()
        
        # Processing timer
        self.timer = self.create_timer(1.0 / self.fps, self.process_frame)
        
        self.get_logger().info(
            f"OAK-D Person Detector started. Blob: {self.nn_blob_path}, "
            f"threshold={self.confidence_threshold}, control={self.control_enabled}")
    
    def _init_pipeline(self):
        """Initialize the DepthAI pipeline with camera + neural network."""
        try:
            pipeline = dai.Pipeline()
            
            # Color camera - try different API versions
            try:
                # Newer API (depthai >= 2.22)
                cam_rgb = pipeline.create(dai.node.ColorCamera)
            except AttributeError:
                # Older API
                cam_rgb = pipeline.createColorCamera()
            
            cam_rgb.setPreviewSize(self.nn_width, self.nn_height)
            cam_rgb.setInterleaved(False)
            cam_rgb.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
            cam_rgb.setFps(self.fps)
            
            # Also output larger preview for visualization
            cam_rgb.setVideoSize(self.preview_width, self.preview_height)
            
            # Neural network (MobileNet SSD)
            try:
                nn = pipeline.create(dai.node.MobileNetDetectionNetwork)
            except AttributeError:
                nn = pipeline.createMobileNetDetectionNetwork()
            
            nn.setBlobPath(self.nn_blob_path)
            nn.setConfidenceThreshold(self.confidence_threshold)
            nn.input.setBlocking(False)
            nn.setNumInferenceThreads(2)
            nn.setNumNCEPerInferenceThread(1)
            
            # Link camera to NN
            cam_rgb.preview.link(nn.input)
            
            # Output streams
            try:
                xout_rgb = pipeline.create(dai.node.XLinkOut)
                xout_nn = pipeline.create(dai.node.XLinkOut)
            except AttributeError:
                xout_rgb = pipeline.createXLinkOut()
                xout_nn = pipeline.createXLinkOut()
            
            xout_rgb.setStreamName("rgb")
            cam_rgb.video.link(xout_rgb.input)
            
            xout_nn.setStreamName("nn")
            nn.out.link(xout_nn.input)
            
            # Connect to device
            self.device = dai.Device(pipeline)
            self.rgb_queue = self.device.getOutputQueue(name="rgb", maxSize=4, blocking=False)
            self.nn_queue = self.device.getOutputQueue(name="nn", maxSize=4, blocking=False)
            
            self.get_logger().info("OAK-D pipeline initialized successfully")
            
        except Exception as e:
            self.get_logger().error(f"Failed to initialize OAK-D pipeline: {e}")
            import traceback
            self.get_logger().error(traceback.format_exc())
            self.device = None
    
    def process_frame(self):
        """Process camera frame and NN detections."""
        if self.device is None:
            return
        
        try:
            # Get RGB frame
            rgb_data = self.rgb_queue.tryGet()
            nn_data = self.nn_queue.tryGet()
            
            if rgb_data is None:
                return
            
            frame = rgb_data.getCvFrame()
            height, width = frame.shape[:2]
            
            # Flip if needed
            if self.flip:
                frame = cv2.rotate(frame, cv2.ROTATE_180)
            
            # Publish raw image
            try:
                # Convert BGR to RGB for ROS
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img_msg = self.bridge.cv2_to_imgmsg(frame_rgb, encoding='rgb8')
                img_msg.header.stamp = self.get_clock().now().to_msg()
                img_msg.header.frame_id = 'oakd_camera_frame'
                self.image_pub.publish(img_msg)
            except Exception as e:
                self.get_logger().error(f"Failed to publish image: {e}")
            
            # Process detections
            persons = []
            
            if nn_data is not None:
                detections = nn_data.detections
                
                for detection in detections:
                    label_idx = detection.label
                    confidence = detection.confidence
                    
                    # Check if it's a person (label 15 in COCO)
                    if label_idx == 15 and confidence >= self.confidence_threshold:
                        # Bounding box (normalized 0-1)
                        x1 = int(detection.xmin * width)
                        y1 = int(detection.ymin * height)
                        x2 = int(detection.xmax * width)
                        y2 = int(detection.ymax * height)
                        
                        # Handle flip
                        if self.flip:
                            x1, x2 = width - x2, width - x1
                            y1, y2 = height - y2, height - y1
                        
                        cx = (x1 + x2) // 2
                        cy = (y1 + y2) // 2
                        
                        persons.append({
                            'bbox': (x1, y1, x2 - x1, y2 - y1),
                            'center': (cx, cy),
                            'confidence': float(confidence),
                            'area': (x2 - x1) * (y2 - y1)
                        })
            
            # Sort by area (largest first)
            persons.sort(key=lambda x: x['area'], reverse=True)
            
            # Build result
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
                
                # Calculate yaw rate
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
                        f"center={persons[0]['center']}, yaw={desired_twist.angular.z:.3f}")
            
            # Visualization
            if self.visualization:
                viz_frame = frame.copy()
                
                # Draw center line
                cv2.line(viz_frame, (width//2, 0), (width//2, height), (128, 128, 128), 1)
                
                for i, person in enumerate(persons):
                    x, y, w, h = person['bbox']
                    cx, cy = person['center']
                    conf = person['confidence']
                    
                    color = (0, 255, 0) if i == 0 else (128, 128, 128)
                    
                    cv2.rectangle(viz_frame, (x, y), (x + w, y + h), color, 2)
                    cv2.circle(viz_frame, (cx, cy), 5, color, -1)
                    
                    if i == 0:
                        cv2.line(viz_frame, (cx, cy), (width//2, cy), (0, 255, 255), 2)
                    
                    label = f"Person {conf:.2f}"
                    if i == 0:
                        label += " [TRACKING]"
                    cv2.putText(viz_frame, label, (x, y - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                # Status
                cv2.putText(viz_frame, f"OAK-D | Persons: {len(persons)}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                
                if persons and self.control_enabled:
                    cv2.putText(viz_frame, f"Yaw: {twist.angular.z:.3f}", (10, 60),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                
                try:
                    viz_msg = self.bridge.cv2_to_imgmsg(viz_frame, encoding='bgr8')
                    viz_msg.header.stamp = self.get_clock().now().to_msg()
                    self.viz_pub.publish(viz_msg)
                except Exception as e:
                    self.get_logger().error(f"Failed to publish viz: {e}")
                    
        except Exception as e:
            self.get_logger().error(f"Error in process_frame: {e}")
    
    def destroy_node(self):
        """Clean up."""
        twist = Twist()
        self.cmd_vel_pub.publish(twist)
        if self.device is not None:
            self.device.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    
    if not DEPTHAI_AVAILABLE:
        print("ERROR: depthai not installed. Run: pip3 install depthai")
        return
    
    node = OakDPersonDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
