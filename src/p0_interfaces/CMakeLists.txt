cmake_minimum_required(VERSION 3.8)
project(p0_interfaces)

find_package(ament_cmake REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/ChassisCmd.msg"
  "msg/ChassisStatus.msg"
  "srv/ClearMotionLock.srv"
  "srv/ResetEmergency.srv"
  "srv/StopMotion.srv"
  "srv/TriggerEmergencyStop.srv"
  DEPENDENCIES builtin_interfaces std_msgs
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
