#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class SimpleSubscriber(Node):
    """
    A simple ROS2 subscriber node that receives messages from a topic.
    This demonstrates the basic subscribe pattern in ROS2.
    """

    def __init__(self):
        super().__init__('simple_subscriber')

        # Create a subscriber
        # The create_subscription method takes 4 arguments:
        #   1. Message type (what kind of data you're receiving)
        #   2. Topic name (the channel name - MUST match the publisher!)
        #   3. Callback function (what to do when a message arrives)
        #   4. Queue size (how many messages to buffer)
        self.subscription = self.create_subscription(
            String,
            '/mini_pupper/chatter',
            self.listener_callback,
            10
        )

        self.get_logger().info('Simple Subscriber Node has started!')
        self.get_logger().info(f'Listening to topic: /mini_pupper/chatter')

    def listener_callback(self, msg):
        """
        This function is called whenever a message arrives on the topic.

        Args:
            msg: The message received (in this case, a String message)
        """
        # Log the received message
        self.get_logger().info(f'I heard: "{msg.data}"')


def main(args=None):
    # Initialize ROS2
    rclpy.init(args=args)

    # Create the node
    node = SimpleSubscriber()

    try:
        # Keep the node running and listening for messages
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Subscriber stopped by user')
    finally:
        # Cleanup
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
