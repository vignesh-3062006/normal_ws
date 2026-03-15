from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.actions import ExecuteProcess
from launch.substitutions import Command
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    # ---- Robot URDF ----
    pkg_share = get_package_share_directory('field_description')
    zed_cam = get_package_share_directory('zed_wrapper')
    urdf_file = os.path.join(pkg_share, 'urdf', 'r2_base.urdf')

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': open(urdf_file).read(),
            'use_sim_time': False
        }]
    )

    # ---- ZED Camera ----
    zed = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                zed_cam,
                'launch',
                'zed_camera.launch.py'
            )
        ),
        launch_arguments={
            'camera_model': 'zed2i',
            'publish_tf': 'false',
        }.items()
    )

    # ---- EKF ----
    ekf_config = os.path.join(pkg_share, 'config', 'rbot_ekf_node.yaml')

    ekf = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_config]
    )

    lidar = Node(
    package='rplidar_ros',
    executable='rplidar_node',
    parameters=[{
        'serial_port': '/dev/ttyUSB1',
        'frame_id': 'laser',
        'serial_baudrate': 115200
    }],
    output='screen'
)

    return LaunchDescription([
        robot_state_publisher,
        zed,
        ekf,
        lidar
    ])