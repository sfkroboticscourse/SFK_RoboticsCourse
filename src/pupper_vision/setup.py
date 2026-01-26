from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'pupper_vision'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Include launch files
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        # Include config files
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        # Include model files
        (os.path.join('share', package_name, 'models'), glob('models/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Baccus Lab',
    maintainer_email='your@email.com',
    description='Vision package for Mini Pupper - color, shape, person, pose detection',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # Camera node
            'camera_node = pupper_vision.camera_node:main',
            # Detection modes
            'color_detector = pupper_vision.color_detector:main',
            'shape_detector = pupper_vision.shape_detector:main',
            'person_detector = pupper_vision.person_detector:main',
            'pose_detector = pupper_vision.pose_detector:main',
            # Controller
            'vision_controller = pupper_vision.vision_controller:main',
        ],
    },
)
