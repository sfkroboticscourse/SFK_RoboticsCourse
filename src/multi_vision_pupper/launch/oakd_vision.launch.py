#!/usr/bin/env python3
"""
OAK-D Vision Launch File for Mini Pupper

Use this when you have an OAK-D camera instead of the OV5647.

Usage:
    # Person detection with OAK-D neural accelerator (fast!)
    ros2 launch multi_vision_pupper oakd_vision.launch.py mode:=person
    
    # Just camera streaming (for use with other detectors)
    ros2 launch multi_vision_pupper oakd_vision.launch.py mode:=camera
    
    # Color detection (uses OAK-D camera, CPU color detection)
    ros2 launch multi_vision_pupper oakd_vision.launch.py mode:=color

    # Shape detection (visual servoing with colored circles)
    ros2 launch multi_vision_pupper oakd_vision.launch.py mode:=shape target_color:=green

    # Pose detection (gesture control)
    ros2 launch multi_vision_pupper oakd_vision.launch.py mode:=pose

    # With visualization
    ros2 launch multi_vision_pupper oakd_vision.launch.py mode:=person visualization:=true

    # Adjust commitment timing
    ros2 launch multi_vision_pupper oakd_vision.launch.py mode:=shape action_duration:=0.8 pause_duration:=0.4
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
import os


def generate_launch_description():
    # ===================
    # Launch Arguments
    # ===================
    mode_arg = DeclareLaunchArgument(
        'mode',
        default_value='person',
        description='Detection mode: person, camera, color, shape, pose'
    )
    
    visualization_arg = DeclareLaunchArgument(
        'visualization',
        default_value='false',
        description='Enable visualization output'
    )
    
    flip_arg = DeclareLaunchArgument(
        'flip',
        default_value='true',
        description='Flip camera image 180 degrees'
    )
    
    nn_blob_arg = DeclareLaunchArgument(
        'nn_blob_path',
        default_value=os.path.expanduser('~/models/mobilenet-ssd_openvino_2021.4_6shave.blob'),
        description='Path to MobileNet SSD blob file'
    )
    
    confidence_arg = DeclareLaunchArgument(
        'confidence',
        default_value='0.5',
        description='Detection confidence threshold'
    )
    
    target_color_arg = DeclareLaunchArgument(
        'target_color',
        default_value='green',
        description='Target color for shape detection'
    )
    
    # Commitment mode parameters
    commitment_mode_arg = DeclareLaunchArgument(
        'commitment_mode',
        default_value='true',
        description='Enable commitment mode (step-based movement)'
    )
    
    action_duration_arg = DeclareLaunchArgument(
        'action_duration',
        default_value='0.5',
        description='Duration to execute each action (seconds)'
    )
    
    pause_duration_arg = DeclareLaunchArgument(
        'pause_duration',
        default_value='0.3',
        description='Duration to pause between actions (seconds)'
    )
    
    # Speed parameters
    forward_speed_arg = DeclareLaunchArgument(
        'forward_speed',
        default_value='0.15',
        description='Forward/backward speed'
    )
    
    turn_speed_arg = DeclareLaunchArgument(
        'turn_speed',
        default_value='0.5',
        description='Turning speed'
    )
    
    # ===================
    # Get Configurations
    # ===================
    mode = LaunchConfiguration('mode')
    visualization = LaunchConfiguration('visualization')
    flip = LaunchConfiguration('flip')
    nn_blob_path = LaunchConfiguration('nn_blob_path')
    confidence = LaunchConfiguration('confidence')
    target_color = LaunchConfiguration('target_color')
    commitment_mode = LaunchConfiguration('commitment_mode')
    action_duration = LaunchConfiguration('action_duration')
    pause_duration = LaunchConfiguration('pause_duration')
    forward_speed = LaunchConfiguration('forward_speed')
    turn_speed = LaunchConfiguration('turn_speed')
    
    # ===================
    # Nodes
    # ===================
    
    # OAK-D Person Detector (mode=person)
    # This is the all-in-one node that does camera + NN detection
    oakd_person_node = Node(
        package='multi_vision_pupper',
        executable='oakd_person_detector',
        name='oakd_person_detector',
        parameters=[{
            'nn_blob_path': nn_blob_path,
            'confidence_threshold': confidence,
            'visualization': visualization,
            'control_enabled': True,
            'max_yaw_rate': 1.0,
            'kp': 0.8,
            'flip': flip,
            'fps': 30,
            'commitment_mode': commitment_mode,
            'action_duration': action_duration,
            'pause_duration': pause_duration,
        }],
        condition=IfCondition(
            PythonExpression(["'", mode, "' == 'person'"])
        ),
        output='screen'
    )
    
    # OAK-D Camera only node (for modes that need camera stream: camera, color, shape, pose)
    oakd_camera_node = Node(
        package='multi_vision_pupper',
        executable='oakd_camera_node',
        name='oakd_camera_node',
        parameters=[{
            'width': 640,
            'height': 480,
            'fps': 30,
            'flip': flip,
            'enable_depth': False,
            'enable_nn': False,
        }],
        condition=IfCondition(
            PythonExpression(["'", mode, "' in ['camera', 'color', 'shape', 'pose']"])
        ),
        output='screen'
    )
    
    # Color detector (mode=color)
    color_detector_node = Node(
        package='multi_vision_pupper',
        executable='color_detector',
        name='color_detector',
        parameters=[{
            'visualization': visualization,
            'min_area': 500,
            'color_follow': True,
            'turn_speed': turn_speed,
            'commitment_mode': commitment_mode,
            'action_duration': action_duration,
            'pause_duration': pause_duration,
        }],
        condition=IfCondition(
            PythonExpression(["'", mode, "' == 'color'"])
        ),
        output='screen'
    )
    
    # Shape detector (mode=shape)
    shape_detector_node = Node(
        package='multi_vision_pupper',
        executable='shape_detector',
        name='shape_detector',
        parameters=[{
            'visualization': visualization,
            'target_color': target_color,
            'target_radius': 80,
            'radius_tolerance': 15,
            'control_enabled': True,
            'forward_speed': forward_speed,
            'turn_speed': turn_speed,
            'commitment_mode': commitment_mode,
            'action_duration': action_duration,
            'pause_duration': pause_duration,
        }],
        condition=IfCondition(
            PythonExpression(["'", mode, "' == 'shape'"])
        ),
        output='screen'
    )
    
    # Pose detector (mode=pose)
    pose_detector_node = Node(
        package='multi_vision_pupper',
        executable='pose_detector',
        name='pose_detector',
        parameters=[{
            'visualization': visualization,
            'control_enabled': True,
            'forward_speed': forward_speed,
            'turn_speed': turn_speed,
            'detection_confidence': confidence,
            'commitment_mode': commitment_mode,
            'action_duration': action_duration,
            'pause_duration': pause_duration,
        }],
        condition=IfCondition(
            PythonExpression(["'", mode, "' == 'pose'"])
        ),
        output='screen'
    )
    
    return LaunchDescription([
        # Arguments
        mode_arg,
        visualization_arg,
        flip_arg,
        nn_blob_arg,
        confidence_arg,
        target_color_arg,
        commitment_mode_arg,
        action_duration_arg,
        pause_duration_arg,
        forward_speed_arg,
        turn_speed_arg,
        # Nodes
        oakd_person_node,
        oakd_camera_node,
        color_detector_node,
        shape_detector_node,
        pose_detector_node,
    ])
