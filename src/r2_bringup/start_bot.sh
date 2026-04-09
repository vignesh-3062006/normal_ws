#!/bin/bash

trap 'echo "🛑 Stopping all processes..."; kill 0; pkill -f micro_ros_agent' SIGINT SIGTERM

echo "🚀 Starting Navigation System..."

# -------- SOURCE ROS --------
source /opt/ros/humble/setup.bash
source ~/robocon_ws/install/setup.bash

# -------- STEP 1: MICRO-ROS AGENT --------
echo "🔌 Starting micro-ROS agent..."
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyUSB0 &

echo "⏳ Waiting for ESP32 connection..."

until ros2 node list | grep -q "diff_drive_node"
do
  echo "Waiting for ESP32 node..."
  sleep 1
done

echo "✅ ESP32 node detected!"

# -------- STEP 2: ROBOT DESCRIPTION --------
echo "🤖 Launching robot description..."
ros2 launch field_description test_bot_launch.py &

echo "⏳ Waiting for robot topics..."

until ros2 topic list | grep -q "/zed/zed_node/odom"
do sleep 1; done

until ros2 topic list | grep -q "/scan"
do sleep 1; done

echo "✅ Robot description ready!"

# -------- STEP 3: LOCALIZATION --------
echo "🧭 Starting localization..."
ros2 launch field_description localization_launch.py map:=/home/vignesh/robocon_ws/src/field_description/config/nav_map_save.yaml &

echo "⏳ Waiting for localization topics..."

# Wait for required topics
until ros2 topic list | grep -q "/map"
do sleep 1; done

echo "✅ Localization topics ready!"

# -------- STEP 4: SET INITIAL POSE --------
echo "📍 Setting initial pose..."

python3 set_initial_pose.py &
sleep 3

echo "✅ Initial pose set!"

echo " To launch the navigation.... "

ros2 launch field_description navigation_launch.py &
sleep 1

echo "✅ R2 is ready to fly!"