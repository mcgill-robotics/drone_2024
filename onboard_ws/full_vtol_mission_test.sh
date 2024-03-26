#!/bin/bash

source ./install/setup.bash

## Takeoff
ros2 service call /px4_action_queue/append_action custom_msgs/srv/SendAction "{action: {action: 1, x: 0., y: 0., z: 0.}}"

## Transition To FW
ros2 service call /px4_action_queue/append_action custom_msgs/srv/SendAction "{action: {action: 5, x: 0., y: 0., z: 0.}}"

## Waypoints
ros2 service call /px4_action_queue/append_action custom_msgs/srv/SendAction "{action: {action: 2, x: 0., y: 100., z: -100.}}"

ros2 service call /px4_action_queue/append_action custom_msgs/srv/SendAction "{action: {action: 2, x: 200., y: 10., z: -100.}}"

ros2 service call /px4_action_queue/append_action custom_msgs/srv/SendAction "{action: {action: 2, x: 100., y: 10., z: -100.}}"

ros2 service call /px4_action_queue/append_action custom_msgs/srv/SendAction "{action: {action: 2, x: 0., y: 0., z: -100.}}"


## Transition To QC
ros2 service call /px4_action_queue/append_action custom_msgs/srv/SendAction "{action: {action: 4, x: 0., y: 0., z: 0.}}"

ros2 service call /px4_action_queue/append_action custom_msgs/srv/SendAction "{action: {action: 2, x: 100., y: 10., z: -100.}}"

ros2 service call /px4_action_queue/append_action custom_msgs/srv/SendAction "{action: {action: 2, x: 0., y: 0., z: -100.}}"

## Land
ros2 service call /px4_action_queue/append_action custom_msgs/srv/SendAction "{action: {action: 3, x: 0., y: 0., z: 0.}}"
