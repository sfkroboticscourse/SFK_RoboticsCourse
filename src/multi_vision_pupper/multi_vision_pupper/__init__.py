# multi_vision_pupper - Multi-Camera Vision Package for Mini Pupper
# 
# Supports both OV5647 (RPi Camera) and OAK-D cameras.
#
# This package provides 4 detection modes:
# 1. Color Detection - detect specific colors from a dictionary
# 2. Shape Detection - detect colored circle stickers, control based on bounding box size
# 3. Person Detection - using MobileNet SSD (OAK-D) or HOG (OV5647)
# 4. Pose Detection - using PoseNet for directional control
#
# Launch files:
#   vision.launch.py      - For OV5647 (RPi Camera)
#   oakd_vision.launch.py - For OAK-D

__version__ = '1.0.0'
