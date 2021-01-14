#!/usr/bin/env python

from __future__ import print_function

import threading

import roslib

roslib.load_manifest('teleop_legged_robots')
import rospy

from geometry_msgs.msg import Twist
from geometry_msgs.msg import Pose

import sys, select, termios, tty

import tf

msg = """
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
"""

moveBindings = {
    'i': (1, 0, 0, 0),
    'o': (1, 0, 0, -1),
    'j': (0, 0, 0, 1),
    'l': (0, 0, 0, -1),
    'u': (1, 0, 0, 1),
    ',': (-1, 0, 0, 0),
    '.': (-1, 0, 0, 1),
    'm': (-1, 0, 0, -1),
    'O': (1, -1, 0, 0),
    'I': (1, 0, 0, 0),
    'J': (0, 1, 0, 0),
    'L': (0, -1, 0, 0),
    'U': (1, 1, 0, 0),
    '<': (-1, 0, 0, 0),
    '>': (-1, -1, 0, 0),
    'M': (-1, 1, 0, 0),
}

speedBindings = {
    'q': (1.1, 1.1),
    'z': (.9, .9),
    'w': (1.1, 1),
    'x': (.9, 1),
    'e': (1, 1.1),
    'c': (1, .9),
}

poseBindings = {
    '1': (1, 0, 0, 0, 0, 0),
    '2': (-1, 0, 0, 0, 0, 0),
    '3': (0, 1, 0, 0, 0, 0),
    '4': (0, -1, 0, 0, 0, 0),
    '5': (0, 0, 1, 0, 0, 0),
    '6': (0, 0, -1, 0, 0, 0),
    'a': (0, 0, 0, 1, 0, 0),
    's': (0, 0, 0, -1, 0, 0),
    'd': (0, 0, 0, 0, 1, 0),
    'f': (0, 0, 0, 0, -1, 0),
    'g': (0, 0, 0, 0, 0, 1),
    'h': (0, 0, 0, 0, 0, -1),
}

speedPoseBindings = {
    'r': (1.1, 1),
    'v': (.9, 1),
    't': (1, 1.1),
    'b': (1, .9),
}


class PublishThread(threading.Thread):
    def __init__(self, rate):
        super(PublishThread, self).__init__()
        robot_name = rospy.get_param("~/robot_name", "/")
        twist_publisher_name = rospy.get_param("~/twist_publisher_name", robot_name + "/cmd_vel")
        pose_publisher_name = rospy.get_param("~/pose_publisher_name", robot_name + "/body_pose")
        self.twist_publisher = rospy.Publisher(twist_publisher_name, Twist, queue_size=1)
        self.pose_publisher = rospy.Publisher(pose_publisher_name, Pose, queue_size=1)
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.th = 0.0
        self.speed = 0.0
        self.turn = 0.0
        self.pose_x = 0.0
        self.pose_y = 0.0
        self.pose_z = 0.0
        self.pose_roll = 0.0
        self.pose_pitch = 0.0
        self.pose_yaw = 0.0
        self.pose_speed = 0.0
        self.pose_turn = 0.0
        self.condition = threading.Condition()
        self.done = False
        self.delay_wait_print = 4

        # Set timeout to None if rate is 0 (causes new_message to wait forever
        # for new data to publish)
        if rate != 0.0:
            self.timeout = 1.0 / rate
        else:
            self.timeout = None

        self.start()

    def wait_for_subscribers(self):
        i = 0
        while not rospy.is_shutdown() and (self.twist_publisher.get_num_connections() == 0 or
                                           self.pose_publisher.get_num_connections() == 0):
            if i == self.delay_wait_print:
                if self.twist_publisher.get_num_connections() == 0 and self.pose_publisher.get_num_connections() == 0:
                    rospy.loginfo("Waiting for subscriber to connect to {}".format(self.twist_publisher.name))
                    rospy.loginfo("Waiting for subscriber to connect to {}".format(self.pose_publisher.name))
                elif self.twist_publisher.get_num_connections() == 0:
                    rospy.loginfo("Waiting for subscriber to connect to {}".format(self.twist_publisher.name))
                else:
                    rospy.loginfo("Waiting for subscriber to connect to {}".format(self.pose_publisher.name))
            rospy.sleep(0.5)
            i += 1
            i = i % (self.delay_wait_print + 1)
        if rospy.is_shutdown():
            raise Exception("Got shutdown request before subscribers connected")

    def update(self, x, y, z, th, speed, turn, pose_x, pose_y, pose_z, pose_roll, pose_pitch, pose_yaw, pose_speed,
               pose_turn):
        self.condition.acquire()
        self.x = x
        self.y = y
        self.z = z
        self.th = th
        self.speed = speed
        self.turn = turn
        self.pose_x = pose_x
        self.pose_y = pose_y
        self.pose_z = pose_z
        self.pose_roll = pose_roll
        self.pose_pitch = pose_pitch
        self.pose_yaw = pose_yaw
        self.pose_speed = pose_speed
        self.pose_turn = pose_turn
        # Notify publish thread that we have a new message.
        self.condition.notify()
        self.condition.release()

    def stop(self):
        self.done = True
        self.update(0, 0, 0, 0, 0, 0, self.pose_x, self.pose_y, self.pose_z, self.pose_roll, self.pose_pitch,
                    self.pose_yaw, self.pose_speed, self.pose_turn)
        self.join()

    def run(self):
        twist = Twist()
        pose = Pose()
        while not self.done:
            self.condition.acquire()
            # Wait for a new message or timeout.
            self.condition.wait(self.timeout)

            # Copy state into twist message.
            twist.linear.x = self.x * self.speed
            twist.linear.y = self.y * self.speed
            twist.linear.z = self.z * self.speed
            twist.angular.x = 0
            twist.angular.y = 0
            twist.angular.z = self.th * self.turn

            # Copy state into pose message.
            pose.position.x = self.pose_x
            pose.position.y = self.pose_y
            pose.position.z = self.pose_z
            pose_roll_euler = self.pose_roll
            pose_pitch_euler = self.pose_pitch
            pose_yaw_euler = self.pose_yaw

            quaternion = tf.transformations.quaternion_from_euler(pose_roll_euler, pose_pitch_euler, pose_yaw_euler)
            pose.orientation.x = quaternion[0]
            pose.orientation.y = quaternion[1]
            pose.orientation.z = quaternion[2]
            pose.orientation.w = quaternion[3]

            self.condition.release()

            # Publish.
            self.twist_publisher.publish(twist)
            self.pose_publisher.publish(pose)

        # Publish stop message when thread exits.
        twist.linear.x = 0
        twist.linear.y = 0
        twist.linear.z = 0
        twist.angular.x = 0
        twist.angular.y = 0
        twist.angular.z = 0
        pose.position.x = self.pose_x
        pose.position.y = self.pose_y
        pose.position.z = self.pose_z
        pose_roll_euler = self.pose_roll
        pose_pitch_euler = self.pose_pitch
        pose_yaw_euler = self.pose_yaw

        quaternion = tf.transformations.quaternion_from_euler(pose_roll_euler, pose_pitch_euler, pose_yaw_euler)
        pose.orientation.x = quaternion[0]
        pose.orientation.y = quaternion[1]
        pose.orientation.z = quaternion[2]
        pose.orientation.w = quaternion[3]
        self.twist_publisher.publish(twist)
        self.pose_publisher.publish(pose)


def getKey(key_timeout):
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], key_timeout)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


def vels(speed, turn):
    return "currently:\tspeed %s\tturn %s " % (speed, turn)


def pose_vel(pose_speed, pose_turn):
    return "currently:\tpose_speed %s\tpose_turn %s " % (pose_speed, pose_turn)


def pose_print(pose_x, pose_y, pose_z, pose_roll, pose_pitch, pose_yaw):
    return "currently:\tx %s\ty %s\tz %s\troll %s\tpitch %s\tyaw %s " % (
        pose_x, pose_y, pose_z, pose_roll, pose_pitch, pose_yaw)


def check_status_msg(status_msg, msg_max):
    if status_msg == msg_max:
        rospy.loginfo(msg)
    return (status_msg + 1) % (msg_max + 1)


if __name__ == "__main__":
    settings = termios.tcgetattr(sys.stdin)

    rospy.init_node("teleop_legged")

    speed = rospy.get_param("~/speed", 0.5)
    turn = rospy.get_param("~/turn", 1.0)
    pose_speed = rospy.get_param("~/pose_speed", 0.01)
    pose_turn = rospy.get_param("~/pose_turn", 0.1)
    repeat = rospy.get_param("~/repeat_rate", 0.0)
    key_timeout = rospy.get_param("~/key_timeout", 0.0)
    msg_max = rospy.get_param("~/msg_max", 14)
    if key_timeout == 0.0:
        key_timeout = None

    pub_thread = PublishThread(repeat)

    x = 0
    y = 0
    z = 0
    th = 0
    pose_x = 0
    pose_y = 0
    pose_z = 0
    pose_roll = 0
    pose_pitch = 0
    pose_yaw = 0
    status_msg = 0  # number of printed additional messages

    try:
        pub_thread.wait_for_subscribers()
        pub_thread.update(x, y, z, th, speed, turn, pose_x, pose_y, pose_z, pose_roll, pose_pitch, pose_yaw, pose_speed,
                          pose_turn)

        rospy.loginfo(msg)
        rospy.loginfo(vels(speed, turn))
        while (1):
            key = getKey(key_timeout)
            if key in moveBindings.keys():
                x = moveBindings[key][0]
                y = moveBindings[key][1]
                z = moveBindings[key][2]
                th = moveBindings[key][3]
            elif key in speedBindings.keys():
                speed = speed * speedBindings[key][0]
                turn = turn * speedBindings[key][1]
                x = 0
                y = 0
                z = 0
                th = 0
                rospy.loginfo(vels(speed, turn))
                status_msg = check_status_msg(status_msg, msg_max)

            elif key in poseBindings.keys():
                pose_x += pose_speed * poseBindings[key][0]
                pose_y += pose_speed * poseBindings[key][1]
                pose_z += pose_speed * poseBindings[key][2]
                pose_roll += pose_turn * poseBindings[key][3]
                pose_pitch += pose_turn * poseBindings[key][4]
                pose_yaw += pose_turn * poseBindings[key][5]
                x = 0
                y = 0
                z = 0
                th = 0

                rospy.loginfo(pose_print(pose_x, pose_y, pose_z, pose_roll, pose_pitch, pose_yaw))
                status_msg = check_status_msg(status_msg, msg_max)

            elif key in speedPoseBindings.keys():
                pose_speed = pose_speed * speedPoseBindings[key][0]
                pose_turn = pose_turn * speedPoseBindings[key][1]
                x = 0
                y = 0
                z = 0
                th = 0

                rospy.loginfo(pose_vel(pose_speed, pose_turn))
                status_msg = check_status_msg(status_msg, msg_max)

            else:
                # Skip updating cmd_vel if key timeout and robot already
                # stopped.
                if key == '' and x == 0 and y == 0 and z == 0 and th == 0:
                    continue
                x = 0
                y = 0
                z = 0
                th = 0
                if key == '\x03':      # Ctrl + C
                    break

            pub_thread.update(x, y, z, th, speed, turn, pose_x, pose_y, pose_z, pose_roll, pose_pitch, pose_yaw,
                              pose_speed, pose_turn)

    except Exception as e:
        rospy.logerr(e)

    finally:
        pub_thread.stop()

        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
