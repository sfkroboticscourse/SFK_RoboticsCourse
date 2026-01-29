from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'final_vision_pupper'

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
    description='Final vision package with MediaPipe pose support for Mini Pupper - OV5647 and OAK-D support',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # Camera nodes
            'camera_node = final_vision_pupper.camera_node:main',
            'oakd_camera_node = final_vision_pupper.oakd_camera_node:main',
            # Detection modes (CPU-based, works with any camera)
            'color_detector = final_vision_pupper.color_detector:main',
            'shape_detector = final_vision_pupper.shape_detector:main',
            'person_detector = final_vision_pupper.person_detector:main',
            'pose_detector = final_vision_pupper.pose_detector:main',
            # OAK-D specific (uses neural accelerator)
            'oakd_person_detector = final_vision_pupper.oakd_person_detector:main',
            # Advanced pose tracking
            'pose_behavior_tracker = final_vision_pupper.pose_behavior_tracker:main',
            # Posture monitor for scoliosis prevention
            'posture_monitor = final_vision_pupper.posture_monitor:main',
            # Tools
            'hsv_calibrator = final_vision_pupper.hsv_calibrator:main',
            # Student project nodes
            'find_and_stop = final_vision_pupper.find_and_stop:main',
            'email_notifier = final_vision_pupper.email_notifier:main',
            # Controller
            'vision_controller = final_vision_pupper.vision_controller:main',
        ],
    },
)
