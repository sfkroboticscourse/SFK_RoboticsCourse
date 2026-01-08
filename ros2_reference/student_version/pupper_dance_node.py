#!/usr/bin/env python3
#
# SPDX-License-Identifier: Apache-2.0
#
# Copyright (c) 2025 MangDang
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import math


class PupperDanceNode(Node):
    """
    A ROS2 node that makes the Mini Pupper dance by publishing choreographed
    joint positions to the /joint_states topic for visualization in RViz.
    """

    def __init__(self):
        super().__init__('pupper_dance_node')

        # Publisher for joint states
        self.joint_pub = self.create_publisher(JointState, '/joint_states', 10)

        # Joint names for Mini Pupper 2 (12 joints - 3 per leg × 4 legs)
        # Naming: lf=left front, rf=right front, lb=left back, rb=right back
        # Numbers: 1=hip ab/ad, 2=hip flex/extend, 3=knee
        self.joint_names = [
            'base_lf1', 'lf1_lf2', 'lf2_lf3',  # Left front leg
            'base_rf1', 'rf1_rf2', 'rf2_rf3',  # Right front leg
            'base_lb1', 'lb1_lb2', 'lb2_lb3',  # Left back leg
            'base_rb1', 'rb1_rb2', 'rb2_rb3',  # Right back leg
        ]

        # Joint limits from URDF (for safety)
        self.joint_limits = [
            [-0.550, 0.425],   # base_lf1
            [0.55, 2.40],      # lf1_lf2
            [-2.18, -0.22],    # lf2_lf3
            [-0.425, 0.550],   # base_rf1
            [0.55, 2.40],      # rf1_rf2
            [-2.18, -0.22],    # rf2_rf3
            [-0.550, 0.425],   # base_lb1
            [0.55, 2.40],      # lb1_lb2
            [-2.18, -0.22],    # lb2_lb3
            [-0.425, 0.550],   # base_rb1
            [0.55, 2.40],      # rb1_rb2
            [-2.18, -0.22],    # rb2_rb3
        ]

        # Standing pose (neutral position)
        self.standing_pose = [0.0, 1.2, -1.2] * 4  # Repeated for all 4 legs

        # Timer for dance loop (30 Hz update rate)
        self.timer = self.create_timer(1.0 / 30.0, self.dance_callback)

        # Time tracking
        self.start_time = self.get_clock().now()

        # Dance parameters
        self.current_dance = 'wave'  # Default dance
        self.dance_duration = 0.0

        self.get_logger().info('Pupper Dance Node started! Let the show begin!')
        self.get_logger().info(f'Current dance: {self.current_dance}')

    def clamp_joint_positions(self, positions):
        """Ensure all joint positions are within safe limits."""
        clamped = []
        for i, pos in enumerate(positions):
            lower, upper = self.joint_limits[i]
            clamped.append(max(lower, min(upper, pos)))
        return clamped

    def publish_joint_state(self, positions):
        """Publish joint positions to /joint_states topic."""
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = self.joint_names
        msg.position = self.clamp_joint_positions(positions)
        self.joint_pub.publish(msg)

    def wave_dance(self, t):
        """
        Wave pattern: legs move in a wave-like motion from front to back.
        """
        positions = []

        # Create a traveling wave through the legs
        for leg_idx in range(4):  # 4 legs
            phase = leg_idx * math.pi / 2  # Each leg is 90 degrees out of phase

            # Hip ab/ad (joint 1) - side to side wave
            hip_abduction = 0.2 * math.sin(2 * math.pi * 0.5 * t + phase)

            # Hip flex/extend (joint 2) - up and down motion
            hip_flex = 1.2 + 0.4 * math.sin(2 * math.pi * 0.5 * t + phase)

            # Knee (joint 3) - coordinated with hip
            knee = -1.2 - 0.4 * math.sin(2 * math.pi * 0.5 * t + phase)

            positions.extend([hip_abduction, hip_flex, knee])

        return positions

    def bounce_dance(self, t):
        """
        Bounce pattern: all legs move up and down together.
        """
        positions = []

        # Synchronized bouncing motion
        bounce = 0.5 * math.sin(2 * math.pi * 1.0 * t)

        for leg_idx in range(4):
            hip_abduction = 0.0  # Keep legs neutral
            hip_flex = 1.2 + bounce
            knee = -1.2 - bounce

            positions.extend([hip_abduction, hip_flex, knee])

        return positions

    def twist_dance(self, t):
        """
        Twist pattern: left and right sides move in opposite directions.
        """
        positions = []

        twist = 0.3 * math.sin(2 * math.pi * 0.8 * t)

        for leg_idx in range(4):
            # Left legs (0, 2) twist one way, right legs (1, 3) twist the other
            direction = 1 if leg_idx % 2 == 0 else -1

            hip_abduction = direction * twist
            hip_flex = 1.2 + 0.2 * abs(twist)
            knee = -1.2 - 0.2 * abs(twist)

            positions.extend([hip_abduction, hip_flex, knee])

        return positions

    def trot_dance(self, t):
        """
        Trot pattern: diagonal legs move together (like a trotting gait).
        """
        positions = []

        # Diagonal pairs: (LF, RB) and (RF, LB)
        for leg_idx in range(4):
            # Legs 0 and 3 (LF, RB) are in phase
            # Legs 1 and 2 (RF, LB) are 180 degrees out of phase
            phase = 0 if (leg_idx == 0 or leg_idx == 3) else math.pi

            lift = 0.4 * math.sin(2 * math.pi * 1.0 * t + phase)

            hip_abduction = 0.0
            hip_flex = 1.2 + max(0, lift)  # Only lift up, not down
            knee = -1.2 - max(0, lift)

            positions.extend([hip_abduction, hip_flex, knee])

        return positions

    def sit_dance(self, t):
        """
        Sit pattern: robot performs a sitting motion repeatedly.
        """
        positions = []

        # Smooth sitting motion using cosine for smooth interpolation
        sit_amount = 0.5 * (1 - math.cos(2 * math.pi * 0.3 * t))

        for leg_idx in range(4):
            hip_abduction = 0.0

            # Front legs (0, 1) less bent, back legs (2, 3) more bent
            if leg_idx < 2:  # Front legs
                hip_flex = 1.2 + 0.3 * sit_amount
                knee = -1.2 - 0.3 * sit_amount
            else:  # Back legs
                hip_flex = 1.2 + 0.6 * sit_amount
                knee = -1.2 - 0.6 * sit_amount

            positions.extend([hip_abduction, hip_flex, knee])

        return positions

    def dance_callback(self):
        """
        Main callback that cycles through different dance moves.

        STUDENT TODO: Add the remaining dance moves after 'wave' in your chosen order!

        Currently, only the 'wave' dance is implemented. Your task is to:
        1. Add elif conditions for the other dances: bounce, twist, trot, sit
        2. Arrange them in the order YOU want them to appear
        3. Update the dances list to match your chosen order

        Use the 'wave' implementation below as an example!
        """
        current_time = self.get_clock().now()
        elapsed = (current_time - self.start_time).nanoseconds / 1e9  # Convert to seconds

        # Cycle through dances every 10 seconds
        dance_cycle_duration = 10.0

        # TODO: Update this list with all 5 dances in YOUR preferred order!
        # Currently only 'wave' is in the list. Add: 'bounce', 'twist', 'trot', 'sit'
        dances = ['wave']  # STUDENT TODO: Add the other 4 dances here!

        dance_index = int(elapsed / dance_cycle_duration) % len(dances)
        new_dance = dances[dance_index]

        # Log when dance changes
        if new_dance != self.current_dance:
            self.current_dance = new_dance
            self.get_logger().info(f'Now dancing: {self.current_dance.upper()}!')

        # Get time within current dance cycle
        t = elapsed % dance_cycle_duration

        # Execute the current dance
        # This is an EXAMPLE for 'wave' - use this as a template for adding the others!
        if self.current_dance == 'wave':
            positions = self.wave_dance(t)
        # TODO: Add elif conditions for the other dances here!
        # elif self.current_dance == 'your_chosen_dance':
        #     positions = self.your_chosen_dance_function(t)
        else:
            positions = self.standing_pose

        # Publish the joint states
        self.publish_joint_state(positions)


def main(args=None):
    rclpy.init(args=args)
    node = PupperDanceNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Dance party is over!')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
