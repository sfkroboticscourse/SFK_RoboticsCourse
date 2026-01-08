#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class SimplePublisher(Node):
    """
    A simple ROS2 publisher node that sends messages to a topic.
    This demonstrates the basic publish pattern in ROS2.
    """

    def __init__(self):
        super().__init__('simple_publisher')

        # TODO: Create a publisher
        # The create_publisher method takes 3 arguments:
        #   1. Message type (what kind of data you're sending)
        #   2. Topic name (the channel name - MUST match the subscriber!)
        #   3. Queue size (how many messages to buffer)
        #
        # Example format:
        # self.publisher_ = self.create_publisher(MessageType, 'topic_name', queue_size)
        #
        # STUDENT TODO: Fill in the topic name below (choose any name you like!)
        self.publisher_ = self.create_publisher(String, 'what?', 10)

        # Create a timer that calls timer_callback every 1.0 seconds
        self.timer = self.create_timer(1.0, self.timer_callback)

        # Counter to track how many messages we've sent
        self.counter = 0

        self.get_logger().info('Simple Publisher Node has started!')
        self.get_logger().info(f'Publishing to topic: YOUR_TOPIC_NAME_HERE')

    def timer_callback(self):
        """
        This function is called every second by the timer.
        It creates and publishes a message.
        """
        # Create a new message
        msg = String()
        msg.data = f'Hello from Mini Pupper! Message #{self.counter}'

        # Publish the message
        self.publisher_.publish(msg)

        # Log what we published
        self.get_logger().info(f'Publishing: "{msg.data}"')

        # Increment counter
        self.counter += 1


def main(args=None):
    # Initialize ROS2
    rclpy.init(args=args)

    # Create the node
    node = SimplePublisher()

    try:
        # Keep the node running
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Publisher stopped by user')
    finally:
        # Cleanup
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
