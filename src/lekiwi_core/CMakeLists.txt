cmake_minimum_required(VERSION 3.8)
project(lekiwi_core)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(tf2_ros REQUIRED)

# Generate messages and services
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/WholeBodyCommand.msg"
  "msg/RobotState.msg"
  "srv/SetOperationMode.srv"
  DEPENDENCIES
    std_msgs
    sensor_msgs
    geometry_msgs
    nav_msgs
)

# Install Python utility modules (as non-package Python scripts)
install(DIRECTORY
  ${PROJECT_NAME}/
  DESTINATION lib/python3/dist-packages/${PROJECT_NAME}
  FILES_MATCHING PATTERN "*.py"
)

# Install config files
install(DIRECTORY
  config
  DESTINATION share/${PROJECT_NAME}/
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
