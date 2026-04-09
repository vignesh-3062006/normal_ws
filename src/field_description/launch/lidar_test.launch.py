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

    rviz_config_dir = os.path.join(
            get_package_share_directory('field_description'),
            'config',
            'final_config.rviz')


    urdf_file = os.path.join(
        robot_pkg,
        'urdf',
        'r2_base.urdf'
    )

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

    rf2o_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('rf2o_laser_odometry'),
                'launch',
                'rf2o_laser_odometry.launch.py'
            )
        )
    )

    rviz_node = Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_dir],
    )
    
    

    return LaunchDescription([
        robot_state_publisher,
        rplidar_node,rf2o_launch,rviz_node
    ])
