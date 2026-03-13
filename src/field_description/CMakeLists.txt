cmake_minimum_required(VERSION 3.8)
project(field_description)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)

#Install py modules


# If you have launch files, URDF, meshes, etc., install them:
install(
  DIRECTORY launch urdf meshes worlds config
  DESTINATION share/${PROJECT_NAME}
)
ament_package()
