# teleop_legged_robots
Generic Keyboard Teleop for legged robots using ROS

# Launch
Launch Keyboard Teleop:
```
roslaunch teleop_legged_robots teleop.launch
```

Launch with user-defined values.
```
roslaunch teleop_legged_robots teleop.launch speed:=0.5 turn:=1.0 pose_speed:=0.01 pose_turn:=0.1
```
Launch with a different robot name to run multiple teleops for multi-robots simulation:
```
roslaunch teleop_legged_robots teleop.launch robot_name:="robot2"
```
Publishing to a different topic (in this case `my_cmd_vel` and `my_body_pose`).
```
roslaunch teleop_legged_robots teleop.launch twist_publisher_name:="my_cmd_vel" pose_publisher_name:="my_body_pose"
```

# Usage
```
Reading from the keyboard and Publishing to Twist and Pose!
---------------------------
Moving around:
   u    i    o
   j    k    l
   m    ,    .

For Holonomic mode (strafing), hold down the shift key:
---------------------------
   U    I    O
   J    K    L
   M    <    >

Body pose:
---------------------------
1/2 : move the body forward/back (+/-x)
3/4 : move the body right/left (+/-y)

5/6 : move the body up/down (+/-z)

a/s : body's roll
d/f : body's pitch
g/h : body's yaw

anything else : stop

q/z : increase/decrease max speeds by 10%
w/x : increase/decrease only linear speed by 10%
e/c : increase/decrease only angular speed by 10%

r/v : increase/decrease body's pose translation by 10%
t/b : increase/decrease body's pose angular speed by 10%

CTRL-C to quit
```

# Repeat Rate

If you need to constantly publish on the topic cmd_vel, the teleop_legged_keyboard can be adjusted to repeat the last command at a fixed interval using the `repeat_rate` parameter.
For example, to repeat the last command at 50Hz:

```
roslaunch teleop_legged_robots teleop.launch repeat_rate:=50.0
```

It is recommended to use the repeat rate in connection with the key timeout, in order to prevent runaway robots.

# Key Timeout

You can adjust teleop_legged_keyboard to stop your robot if no key presses in a configured time period, using the `key_timeout` parameter.

For example, to stop your robot if a keypress has not been received in 2.0 seconds:
```
roslaunch teleop_legged_robots teleop.launch key_timeout:=2.0
```

It is recommended to set `key_timeout` higher than the initial key repeat delay on your system (This delay is 0.5 seconds by default on Ubuntu, but can be adjusted).

# Print the usage message
Having teleop launched, the message on how to use teleop is printed. Also, the teleop prints the current values of the desired speeds and body's poses if they changed. 
When the terminal screen is full, the message of usage is refreshed. You can adjust the rate of refreshing using the `msg_max` parameter. 
For example, refresh usage message if the additional message were printed 16 times (default 14):
```
roslaunch teleop_legged_robots teleop.launch msg_max:=16.0
```

# Inspiration:
[teleop_twist_keyboard](https://github.com/ros-teleop/teleop_twist_keyboard/)
