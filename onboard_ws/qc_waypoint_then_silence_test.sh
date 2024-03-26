#!/bin/bash

source ./install/setup.bash

## Takeoff
ros2 service call /px4_action_queue/append_action custom_msgs/srv/SendAction "{action: {action: 1, x: 0., y: 0., z: 0.}}"

ros2 service call /px4_action_queue/append_action custom_msgs/srv/SendAction "{action: {action: 2, x: 100., y: 10., z: -100.}}"

ros2 service call /px4_action_queue/append_action custom_msgs/srv/SendAction "{action: {action: 2, x: 0., y: 0., z: -100.}}"


