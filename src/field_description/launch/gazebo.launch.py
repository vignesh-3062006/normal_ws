from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess
from launch.actions import TimerAction
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():

    pkg_name = 'field_description'
    pkg_path = get_package_share_directory(pkg_name)

    urdf_path = os.path.join(pkg_path, 'urdf', 'r2_bot.urdf')
    with open(urdf_path, 'r') as infp:
        robot_description = infp.read()

    world_path = os.path.join(pkg_path, 'worlds', 'game_field.sdf')
    
    gazebo = ExecuteProcess(
        cmd=['ign', 'gazebo', world_path],
        output='screen'
    )

    ros_gz_bridge = Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='ros_gz_bridge',
            output='screen',
            arguments=[
                '/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist'
            ]
        )

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{'robot_description': robot_description}]
    )

    joint_state_publisher_gui_node = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui"
    )

    spawn_robot = TimerAction(
        period=5.0,  # wait 5 seconds
        actions=[
            ExecuteProcess(
                cmd=[
                    'ign', 'service',
                    '-s', '/world/robocon_arena/create',
                    '--reqtype', 'ignition.msgs.EntityFactory',
                    '--reptype', 'ignition.msgs.Boolean',
                    '--timeout', '5000',
                    '--req', f'sdf_filename: "{urdf_path}", name: "r2_bot"'
                ],
                output='screen'
            )
        ]
    )

    return LaunchDescription([
        robot_state_publisher_node,
        joint_state_publisher_gui_node,
        spawn_robot,
        ros_gz_bridge,
        gazebo
    ])