#!/usr/bin/env python3

from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import rclpy
from rclpy.node import Node
from rclpy.duration import Duration

# 👉 Import your service
from r2_bringup.srv import ArmService   # CHANGE this


class TaskManager(Node):

    def __init__(self):
        super().__init__('task_manager')

        # Arm service client
        self.arm_client = self.create_client(ArmService, 'arm_execute_task')

        while not self.arm_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for arm service...')

    def call_arm(self, task_name):
        request = ArmService.Request()
        request.task_name = task_name

        future = self.arm_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)

        if future.result() is not None:
            response = future.result()

            if response.success:
                self.get_logger().info(f"✅ Arm done: {response.message}")
                return True
            else:
                self.get_logger().error("❌ Arm failed")
                return False
        else:
            self.get_logger().error("Service call failed")
            return False


def create_pose(navigator, x, y, z=0.0, w=1.0):
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = navigator.get_clock().now().to_msg()
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.orientation.z = z
    pose.pose.orientation.w = w
    return pose


def main():
    rclpy.init()

    navigator = BasicNavigator()
    task_manager = TaskManager()

    # Initial pose
    initial_pose = create_pose(navigator, 0.8, 4.8)
    navigator.setInitialPose(initial_pose)

    navigator.waitUntilNav2Active()

    # 🔥 Waypoints list (YOU CAN MODIFY)
    waypoints = [
        (1.2, 4.8, "pick")
    ]

    for i, (x, y, arm_task) in enumerate(waypoints):

        print(f"\n🚀 Going to waypoint {i+1}: ({x}, {y})")

        goal_pose = create_pose(navigator, x, y)
        task = navigator.goToPose(goal_pose)

        # Wait until navigation completes
        while not navigator.isTaskComplete(task=task):
            feedback = navigator.getFeedback(task=task)

            if feedback:
                print(f"Distance remaining: {feedback.distance_remaining:.2f}")

                # Optional timeout
                if Duration.from_msg(feedback.navigation_time) > Duration(seconds=300.0):
                    navigator.cancelTask()

        # Check result
        result = navigator.getResult()

        if result == TaskResult.SUCCEEDED:
            print(f"✅ Reached waypoint {i+1}")

            # 🔥 👉 CALL ARM AFTER REACHING
            print(f"🤖 Executing arm task: {arm_task}")

            success = task_manager.call_arm(arm_task)

            if not success:
                print("❌ Arm failed → stopping mission")
                break

            print("✅ Arm completed → moving to next waypoint")

        elif result == TaskResult.FAILED:
            print("❌ Navigation failed → stopping")
            break

        elif result == TaskResult.CANCELED:
            print("⚠️ Navigation canceled → stopping")
            break

    print("\n🎯 Mission Completed")

    navigator.lifecycleShutdown()
    rclpy.shutdown()


if __name__ == '__main__':
    main()