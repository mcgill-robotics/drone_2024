#!/bin/bash

source ./install/setup.bash


## Transition To FW
ros2 service call /px4_action_queue/append_action custom_msgs/srv/SendAction "{action: {action: 5, x: 0., y: 0., z: 0.}}"

## Waypoints
ros2 service call /px4_action_queue/append_action custom_msgs/srv/SendAction "{action: {action: 2, x: 100., y: 10., z: -100.}}"

ros2 service call /px4_action_queue/append_action custom_msgs/srv/SendAction "{action: {action: 2, x: 200., y: 10., z: -100.}}"

ros2 service call /px4_action_queue/append_action custom_msgs/srv/SendAction "{action: {action: 2, x: 100., y: 10., z: -100.}}"

ros2 service call /px4_action_queue/append_action custom_msgs/srv/SendAction "{action: {action: 2, x: 0., y: 0., z: -100.}}"

## transition to QC
ros2 service call /px4_action_queue/append_action custom_msgs/srv/SendAction "{action: {action: 4, x: 0., y: 0., z: 0.}}"

# go lower
ros2 service call /px4_action_queue/append_action custom_msgs/srv/SendAction "{action: {action: 2, x: 0., y: 0., z: -10.}}"

# land
ros2 service call /px4_action_queue/append_action custom_msgs/srv/SendAction "{action: {action: 3, x: 0., y: 0., z: 0.}}"
