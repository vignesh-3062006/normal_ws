#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from r2_bringup.srv import ArmService   # change if using different package

import time


class ArmServiceServer(Node):

    def __init__(self):
        super().__init__('arm_service_server')

        self.srv = self.create_service(
            ArmService,
            'arm_execute_task',
            self.callback
        )

        self.get_logger().info("✅ Arm Service is READY")

    def callback(self, request, response):
        self.get_logger().info(f"📩 Received request: {request.task_name}")

        self.get_logger().info("⏳ Executing arm task (10 sec)...")
        time.sleep(10)   # simulate arm working

        response.success = True
        response.message = "Arm work is done ✅"

        self.get_logger().info("✅ Task completed, sending response")

        return response


def main(args=None):
    rclpy.init(args=args)
    node = ArmServiceServer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()