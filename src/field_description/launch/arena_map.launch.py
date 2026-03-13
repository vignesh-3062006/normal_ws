from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


import os

def generate_launch_description():

    # Path to RViz config file
    rviz_config = os.path.expanduser(
        '~/robocon_ws/src/field_description/config/robocon_map1.rviz'
    )

    # Path to RTAB-Map launch file
    rtabmap_launch = os.path.join(
        get_package_share_directory('rtabmap_launch'),
        'launch',
        'rtabmap.launch.py'
    )
    # Path to ZED launch file
    zed_launch_path = os.path.join(
        get_package_share_directory('zed_wrapper'),
        'launch',
        'zed_camera.launch.py'
    )

    # Launch ZED2i camera
    zed_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(zed_launch_path),
        launch_arguments={
            'camera_model': 'zed2i'   # <-- Add ZED2i here
        }.items()
    )

    # Launch RTAB-Map with your parameters
    rtabmap_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(rtabmap_launch),
        launch_arguments={
            'rgb_topic': '/zed/zed_node/rgb/image_rect_color',
            'depth_topic': '/zed/zed_node/depth/depth_registered',
            'camera_info_topic': '/zed/zed_node/rgb/camera_info',
            'depth_camera_info_topic': '/zed/zed_node/depth/camera_info',
            'imu_topic': '/zed/zed_node/imu/data',
            'frame_id': 'zed_camera_link',
            'approx_sync': 'true',
            'wait_imu_to_init': 'true'
        }.items()
    )

    # Launch RViz with config
    rviz_node = ExecuteProcess(
        cmd=['rviz2', '-d', rviz_config],
        output='screen'
    )

    return LaunchDescription([
        zed_launch,
        rtabmap_node,
        rviz_node
    ])
