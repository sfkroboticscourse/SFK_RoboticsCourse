#!/usr/bin/env python3
"""
Main launch file for pupper_vision package.

This launch file starts the camera node and one of the detection modes.

Usage:
    # Color detection (Task 1)
    ros2 launch pupper_vision vision.launch.py mode:=color
    
    # Shape detection (Task 2)
    ros2 launch pupper_vision vision.launch.py mode:=shape target_color:=green
    
    # Person detection (Task 3)
    ros2 launch pupper_vision vision.launch.py mode:=person
    
    # Pose detection (Task 4)
    ros2 launch pupper_vision vision.launch.py mode:=pose

    # With visualization (for PC viewing)
    ros2 launch pupper_vision vision.launch.py mode:=person visualization:=true

    # Simulation mode (no camera needed)
    ros2 launch pupper_vision vision.launch.py mode:=color simulation:=true
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    # Declare launch arguments
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
    
    # Get launch configurations
    mode = LaunchConfiguration('mode')
    visualization = LaunchConfiguration('visualization')
    simulation = LaunchConfiguration('simulation')
    target_color = LaunchConfiguration('target_color')
    flip = LaunchConfiguration('flip')
    
    # Camera node
    camera_node = Node(
        package='multi_vision_pupper',
        executable='camera_node',
        name='camera_node',
        parameters=[{
            'width': 640,
            'height': 480,
            'fps': 30,
            'flip': LaunchConfiguration('flip'),
            'use_simulation': LaunchConfiguration('simulation'),
        }],
        output='screen'
    )
    
    # Color detector (mode=color)
    color_detector_node = Node(
        package='multi_vision_pupper',
        executable='color_detector',
        name='color_detector',
        parameters=[{
            'visualization': LaunchConfiguration('visualization'),
            'min_area': 500,
            'color_follow': True,
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
            'visualization': LaunchConfiguration('visualization'),
            'target_color': LaunchConfiguration('target_color'),
            'target_radius': 80,
            'radius_tolerance': 15,
            'control_enabled': True,
        }],
        condition=IfCondition(
            PythonExpression(["'", mode, "' == 'shape'"])
        ),
        output='screen'
    )
    
    # Person detector (mode=person)
    person_detector_node = Node(
        package='multi_vision_pupper',
        executable='person_detector',
        name='person_detector',
        parameters=[{
            'visualization': LaunchConfiguration('visualization'),
            'confidence_threshold': 0.5,
            'control_enabled': True,
            'max_yaw_rate': 1.0,
            'model_type': 'hog',  # Use HOG by default (no model files needed)
        }],
        condition=IfCondition(
            PythonExpression(["'", mode, "' == 'person'"])
        ),
        output='screen'
    )
    
    # Pose detector (mode=pose)
    pose_detector_node = Node(
        package='multi_vision_pupper',
        executable='pose_detector',
        name='pose_detector',
        parameters=[{
            'visualization': LaunchConfiguration('visualization'),
            'control_enabled': True,
            'forward_speed': 0.15,
            'turn_speed': 0.6,
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
        # Nodes
        camera_node,
        color_detector_node,
        shape_detector_node,
        person_detector_node,
        pose_detector_node,
    ])
