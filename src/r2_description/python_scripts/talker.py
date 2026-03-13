#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from r2_description.import_python import MyNode


def main(args=None):
    rclpy.init(args=args)
    node = MyNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
