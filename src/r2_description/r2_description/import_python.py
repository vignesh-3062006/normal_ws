#! usr/bin/env python3

import rclpy 
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped
from builtin_interfaces.msg import Time

class MyNode(Node):

    def __init__(self):
        super().__init__('cmd_vel_stamped_publisher')
        self.pub = self.create_publisher(TwistStamped, 'cmd_vel', 10)
        self.timer = self.create_timer(0.1, self.publish_cmd)

    def publish_cmd(self):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"
        msg.twist.linear.x = 0.0
        msg.twist.angular.z = 5.0
        self.pub.publish(msg)
        self.get_logger().info("Publishing TwistStamped: linear=0.5 angular=0.0")

     
