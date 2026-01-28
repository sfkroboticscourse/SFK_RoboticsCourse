from setuptools import setup

package_name = 'pupper_ai_voice'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Mini Pupper Lab',
    maintainer_email='lab@example.com',
    description='Clean AI voice control for Mini Pupper using Google Gemini',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'ai_voice_control = pupper_ai_voice.ai_voice_control:main',
            'tts_node = pupper_ai_voice.tts_node:main',
            'keyboard_control = pupper_ai_voice.keyboard_control:main',
        ],
    },
)
