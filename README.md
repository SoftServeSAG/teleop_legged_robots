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
Launch with a different node name to run multiple teleops:
```
roslaunch teleop_legged_robots teleop.launch node_name:="teleop_for_robot2"
```
Publishing to a different topic (in this case `robot1/cmd_vel` and `robot1/body_pose`).
```
roslaunch teleop_legged_robots teleop.launch twist_publisher_name:="robot1/cmd_vel" pose_publisher_name:="robot1/body_pose"
```

# Usage
```
Reading from the keyboard  and Publishing to Twist!
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
1/2 : (+/-) x
3/4 : (+/-) y

5 : up (+z)
6 : down (-z)

a/s : (+/-) roll
d/f : (+/-) pitch
g/h : (+/-) yaw

anything else : stop

q/z : increase/decrease max speeds by 10%
w/x : increase/decrease only linear speed by 10%
e/c : increase/decrease only angular speed by 10%

r/v : increase/decrease body pose translation by 10%
t/b : increase/decrease body pose angular speed by 10%

CTRL-C to quit

```

# Repeat Rate

If your mobile base requires constant updates on the cmd\_vel topic, teleop\_twist\_keyboard can be configured to repeat the last command at a fixed interval, using the `repeat_rate` private parameter.

For example, to repeat the last command at 10Hz:

```
roslaunch teleop_legged_robots teleop.launch repeat_rate:=10.0
```

It is _highly_ recommened that the repeat rate be used in conjunction with the key timeout, to prevent runaway robots.

# Key Timeout

Teleop\_twist\_keyboard can be configured to stop your robot if it does not receive any key presses in a configured time period, using the `key_timeout` private parameter.

For example, to stop your robot if a keypress has not been received in 0.6 seconds:
```
roslaunch teleop_legged_robots teleop.launch key_timeout:=0.6
```

It is recommended that you set `key_timeout` higher than the initial key repeat delay on your system (This delay is 0.5 seconds by default on Ubuntu, but can be adjusted).

# Credits:
[teleop_twist_keyboard](https://github.com/ros-teleop/teleop_twist_keyboard/)