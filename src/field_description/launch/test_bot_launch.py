from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
from launch.actions import TimerAction
import os


def generate_launch_description():

    # ===============================
    # Paths
    # ===============================
    robot_pkg = get_package_share_directory('field_description')
    zed_pkg   = get_package_share_directory('zed_wrapper')

    urdf_file = os.path.join(
        robot_pkg,
        'urdf',
        'r2_base.urdf'
    )

    zed_params = os.path.join(
        robot_pkg,
        'config',
        'common_stereo.yaml'
    )

    rviz_config_dir = os.path.join(
            get_package_share_directory('field_description'),
            'config',
            'final_config.rviz')

    # ===============================
    # Robot State Publisher
    # ===============================
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

    # ===============================
    # ZED2i Camera (Hardware)
    # ===============================
    zed_camera = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                zed_pkg,
                'launch',
                'zed_camera.launch.py'
            )
        ),
        launch_arguments={
            'camera_model': 'zed2i',
            'pos_tracking': 'true',
            'publish_tf': 'false',
            'base_frame': 'base_link'
        }.items()
    )

    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=['/home/vignesh/robocon_ws/src/field_description/config/rbot_ekf_node.yaml']
    )

    rplidar_node = Node(
        package='rplidar_ros',
        executable='rplidar_node',
        name='rplidar_node',
        parameters=[{
            'serial_port': '/dev/ttyUSB1',
            'serial_baudrate': 115200,
            'frame_id': 'laser',
            'angle_compensate': True
        }],
        output='screen'
    )

    rviz_node = Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_dir],
    )
    

    return LaunchDescription([
        robot_state_publisher,
        zed_camera,ekf_node,rplidar_node,rviz_node
    ])
