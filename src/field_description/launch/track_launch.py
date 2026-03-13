# Copyright 2022 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import os


def generate_launch_description():

    # Launch Arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default=True)

    # Get URDF via xacro
    # Read URDF file directly
    urdf_file = os.path.join(
        get_package_share_directory('field_description'),
        'urdf',
        'r2_track.urdf'
    )

    with open(urdf_file, 'r') as infp:
        robot_description_content = infp.read()

    robot_description = {'robot_description': robot_description_content}
    robot_controllers = PathJoinSubstitution(
        [
            FindPackageShare('field_description'),
            'config',
            'four_wheeled_controller.yaml',
        ]
    )

    world_path = PathJoinSubstitution([
    FindPackageShare('field_description'),
    'worlds',
    'game_field.sdf'
    ])

    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[
            robot_description,
            {'use_sim_time': True}
        ]
    )

    gz_spawn_entity = Node(
    package='ros_gz_sim',
    executable='create',
    output='screen',
    arguments=[
        '-topic', 'robot_description',
        '-name', 'R2',
        '-allow_renaming', 'true',

        # ✅ WORLD POSITION (THIS IS THE RIGHT PLACE)
        '-x', '1.4',
        '-y', '-5.5',
        '-z', '0.1',

        # optional: initial yaw (rotation about Z)
        '-Y', '1.5708'
    ],
)


    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster'],
    )
    diff_drive_base_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'diff_drive_controller',
            '--param-file',
            robot_controllers,
        ],
        output='screen',
    )

    return LaunchDescription([
        # Launch gazebo environment
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare('ros_gz_sim'),
                    'launch',
                    'gz_sim.launch.py'
                ])
            ),
            launch_arguments={
                'gz_args': ['-r -v 1 ',world_path]
            }.items()
        ),
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=gz_spawn_entity,
                on_exit=[joint_state_broadcaster_spawner],
            )
        ),
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=joint_state_broadcaster_spawner,
                on_exit=[diff_drive_base_controller_spawner],
            )
        ),
        node_robot_state_publisher,
        gz_spawn_entity,
        # Launch Arguments
        DeclareLaunchArgument(
            'use_sim_time',
            default_value=use_sim_time,
            description='If true, use simulated clock'),
    ])
