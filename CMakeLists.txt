cmake_minimum_required(VERSION 2.8.3)
project(teleop_legged_robots)

find_package(catkin REQUIRED)

catkin_package()

## Mark executable scripts (Python etc.) for installation
## in contrast to setup.py, you can choose the destination
catkin_install_python(PROGRAMS
   scripts/teleop_legged_keyboard.py
   DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

