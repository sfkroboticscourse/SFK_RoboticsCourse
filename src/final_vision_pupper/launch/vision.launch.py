#!/usr/bin/env python3
"""
Main launch file for final_vision_pupper package (OV5647 / RPi Camera).

This launch file starts the camera node and one of the detection modes.

Usage:
    # Color detection (Task 1)
    ros2 launch final_vision_pupper vision.launch.py mode:=color
    
    # Shape detection (Task 2)
    ros2 launch final_vision_pupper vision.launch.py mode:=shape target_color:=green
    
    # Person detection (Task 3)
    ros2 launch final_vision_pupper vision.launch.py mode:=person
    
    # Pose detection (Task 4)
    ros2 launch final_vision_pupper vision.launch.py mode:=pose

    # With visualization (for PC viewing)
    ros2 launch final_vision_pupper vision.launch.py mode:=person visualization:=true

    # Simulation mode (no camera needed)
    ros2 launch final_vision_pupper vision.launch.py mode:=color simulation:=true

    # Adjust commitment timing
    ros2 launch final_vision_pupper vision.launch.py mode:=shape action_duration:=0.8 pause_duration:=0.4

    # Disable commitment mode (continuous tracking)
    ros2 launch final_vision_pupper vision.launch.py mode:=person commitment_mode:=false
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    # ===================
    # Launch Arguments
    # ===================
    mode_arg = DeclareLaunchArgument(
        'mode',
        default_value='color',
        description='Detection mode: color, shape, person, pose'
    )
    
    visualization_arg = DeclareLaunchArgument(
        'visualization',
        default_value='false',
        description='Enable visualization output'
    )
    
    simulation_arg = DeclareLaunchArgument(
        'simulation',
        default_value='false',
        description='Use simulated camera (for testing without hardware)'
    )
    
    target_color_arg = DeclareLaunchArgument(
        'target_color',
        default_value='green',
        description='Target color for shape detection'
    )
    
    flip_arg = DeclareLaunchArgument(
        'flip',
        default_value='true',
        description='Flip camera image 180 degrees'
    )
    
    confidence_arg = DeclareLaunchArgument(
        'confidence',
        default_value='0.5',
        description='Detection confidence threshold'
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
    simulation = LaunchConfiguration('simulation')
    target_color = LaunchConfiguration('target_color')
    flip = LaunchConfiguration('flip')
    confidence = LaunchConfiguration('confidence')
    commitment_mode = LaunchConfiguration('commitment_mode')
    action_duration = LaunchConfiguration('action_duration')
    pause_duration = LaunchConfiguration('pause_duration')
    forward_speed = LaunchConfiguration('forward_speed')
    turn_speed = LaunchConfiguration('turn_speed')
    
    # ===================
    # Nodes
    # ===================
    
    # Camera node
    camera_node = Node(
        package='final_vision_pupper',
        executable='camera_node',
        name='camera_node',
        parameters=[{
            'width': 640,
            'height': 480,
            'fps': 30,
            'flip': flip,
            'use_simulation': simulation,
        }],
        output='screen'
    )
    
    # Color detector (mode=color)
    color_detector_node = Node(
        package='final_vision_pupper',
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
        package='final_vision_pupper',
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
    
    # Person detector (mode=person)
    person_detector_node = Node(
        package='final_vision_pupper',
        executable='person_detector',
        name='person_detector',
        parameters=[{
            'visualization': visualization,
            'confidence_threshold': confidence,
            'control_enabled': True,
            'max_yaw_rate': 1.0,
            'model_type': 'hog',  # Use HOG by default (no model files needed)
            'commitment_mode': commitment_mode,
            'action_duration': action_duration,
            'pause_duration': pause_duration,
        }],
        condition=IfCondition(
            PythonExpression(["'", mode, "' == 'person'"])
        ),
        output='screen'
    )
    
    # Pose detector (mode=pose)
    pose_detector_node = Node(
        package='final_vision_pupper',
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
        simulation_arg,
        target_color_arg,
        flip_arg,
        confidence_arg,
        commitment_mode_arg,
        action_duration_arg,
        pause_duration_arg,
        forward_speed_arg,
        turn_speed_arg,
        # Nodes
        camera_node,
        color_detector_node,
        shape_detector_node,
        person_detector_node,
        pose_detector_node,
    ])
