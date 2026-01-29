#!/usr/bin/env python3
"""
OAK-D Vision Launch File for Mini Pupper

Use this when you have an OAK-D camera instead of the OV5647.

Usage:
    # Person detection with OAK-D neural accelerator (fast!)
    ros2 launch final_vision_pupper oakd_vision.launch.py mode:=person
    
    # Just camera streaming (for use with other detectors)
    ros2 launch final_vision_pupper oakd_vision.launch.py mode:=camera
    
    # Color detection (uses OAK-D camera, CPU color detection)
    ros2 launch final_vision_pupper oakd_vision.launch.py mode:=color

    # Shape detection (visual servoing with colored circles)
    ros2 launch final_vision_pupper oakd_vision.launch.py mode:=shape target_color:=green

    # Pose detection (gesture control)
    ros2 launch final_vision_pupper oakd_vision.launch.py mode:=pose

    # === NEW: Pose Behavior Tracker Modes ===
    
    # Gesture control (same as pose but with more gestures)
    ros2 launch final_vision_pupper oakd_vision.launch.py mode:=behavior behavior_mode:=gesture_control
    
    # Exercise counter (count squats, jumping jacks, arm raises)
    ros2 launch final_vision_pupper oakd_vision.launch.py mode:=behavior behavior_mode:=exercise_counter exercise_type:=squats
    ros2 launch final_vision_pupper oakd_vision.launch.py mode:=behavior behavior_mode:=exercise_counter exercise_type:=jumping_jacks
    ros2 launch final_vision_pupper oakd_vision.launch.py mode:=behavior behavior_mode:=exercise_counter exercise_type:=arm_raises
    
    # Activity tracker (detect standing, sitting, walking, jumping)
    ros2 launch final_vision_pupper oakd_vision.launch.py mode:=behavior behavior_mode:=activity_tracker

    # === SCOLIOSIS PREVENTION: Posture Monitor ===
    
    # Monitor sitting posture for scoliosis prevention
    ros2 launch final_vision_pupper oakd_vision.launch.py mode:=posture visualization:=true
    
    # With Chinese alerts
    ros2 launch final_vision_pupper oakd_vision.launch.py mode:=posture language:=zh
    
    # Adjust sensitivity
    ros2 launch final_vision_pupper oakd_vision.launch.py mode:=posture slouch_threshold:=15.0 tilt_threshold:=10.0

    # With visualization
    ros2 launch final_vision_pupper oakd_vision.launch.py mode:=person visualization:=true

    # Adjust commitment timing
    ros2 launch final_vision_pupper oakd_vision.launch.py mode:=shape action_duration:=0.8 pause_duration:=0.4
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
        description='Detection mode: person, camera, color, shape, pose, behavior, posture'
    )
    
    # Behavior tracker parameters
    behavior_mode_arg = DeclareLaunchArgument(
        'behavior_mode',
        default_value='gesture_control',
        description='Behavior mode: gesture_control, exercise_counter, activity_tracker'
    )
    
    exercise_type_arg = DeclareLaunchArgument(
        'exercise_type',
        default_value='squats',
        description='Exercise type: squats, jumping_jacks, arm_raises'
    )
    
    # Posture monitor parameters (scoliosis prevention)
    language_arg = DeclareLaunchArgument(
        'language',
        default_value='en',
        description='Alert language: en (English) or zh (Chinese)'
    )
    
    slouch_threshold_arg = DeclareLaunchArgument(
        'slouch_threshold',
        default_value='20.0',
        description='Slouching detection threshold (degrees)'
    )
    
    tilt_threshold_arg = DeclareLaunchArgument(
        'tilt_threshold',
        default_value='8.0',
        description='Shoulder tilt threshold (degrees)'
    )
    
    sitting_alert_arg = DeclareLaunchArgument(
        'sitting_alert_minutes',
        default_value='30',
        description='Minutes before sitting-too-long alert'
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
    behavior_mode = LaunchConfiguration('behavior_mode')
    exercise_type = LaunchConfiguration('exercise_type')
    language = LaunchConfiguration('language')
    slouch_threshold = LaunchConfiguration('slouch_threshold')
    tilt_threshold = LaunchConfiguration('tilt_threshold')
    sitting_alert_minutes = LaunchConfiguration('sitting_alert_minutes')
    
    # ===================
    # Nodes
    # ===================
    
    # OAK-D Person Detector (mode=person)
    # This is the all-in-one node that does camera + NN detection
    oakd_person_node = Node(
        package='final_vision_pupper',
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
    
    # OAK-D Camera only node (for modes that need camera stream: camera, color, shape, pose, behavior, posture)
    oakd_camera_node = Node(
        package='final_vision_pupper',
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
            PythonExpression(["'", mode, "' in ['camera', 'color', 'shape', 'pose', 'behavior', 'posture']"])
        ),
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
    
    # Pose Behavior Tracker (mode=behavior)
    # Supports: gesture_control, exercise_counter, activity_tracker
    pose_behavior_node = Node(
        package='final_vision_pupper',
        executable='pose_behavior_tracker',
        name='pose_behavior_tracker',
        parameters=[{
            'visualization': visualization,
            'control_enabled': True,
            'forward_speed': forward_speed,
            'turn_speed': turn_speed,
            'detection_confidence': confidence,
            'behavior_mode': behavior_mode,
            'exercise_type': exercise_type,
            'commitment_mode': commitment_mode,
            'action_duration': action_duration,
            'pause_duration': pause_duration,
        }],
        condition=IfCondition(
            PythonExpression(["'", mode, "' == 'behavior'"])
        ),
        output='screen'
    )
    
    # Posture Monitor for Scoliosis Prevention (mode=posture)
    # Detects: crossed legs, slouching, side leaning, sitting too long
    posture_monitor_node = Node(
        package='final_vision_pupper',
        executable='posture_monitor',
        name='posture_monitor',
        parameters=[{
            'visualization': visualization,
            'alert_enabled': True,
            'language': language,
            'slouch_threshold': slouch_threshold,
            'tilt_threshold': tilt_threshold,
            'sitting_alert_minutes': sitting_alert_minutes,
            'movement_alert': True,
            'detection_confidence': confidence,
        }],
        condition=IfCondition(
            PythonExpression(["'", mode, "' == 'posture'"])
        ),
        output='screen'
    )
    
    return LaunchDescription([
        # Arguments
        mode_arg,
        behavior_mode_arg,
        exercise_type_arg,
        language_arg,
        slouch_threshold_arg,
        tilt_threshold_arg,
        sitting_alert_arg,
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
        pose_behavior_node,
        posture_monitor_node,
    ])
