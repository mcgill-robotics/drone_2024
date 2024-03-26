# How to run offboard_node
You will need PX4, gazebo, ROS2 and the Micro XRCE-DDS Agent to run the simulation and the node. 
[Refer to this to install all those tools](https://docs.px4.io/main/en/ros/ros2_comm.html), [refer to the wiki to install gazebo](https://github.com/mcgill-robotics/drone_2024/wiki/1.-Cheat-Sheets).
## Note
The custom types, used by all the topics and services exposed by the offboard_node node can be found under the custom_msgs package, under msg and srv for the message types and service types respectively. 
## Steps
### Step 0 
You need to build the workspace. In the onboard_ws directory, run ```colcon build --symlink-install```. Close the terminal when the command is done. Thanks to the symlink install flag, modifying the python files in each package under this workspace do not require the package in which the modified python file resides to be re-built for the changes to take effect.
### Step 1
In a new terminal, run ```MicroXRCEAgent udp4 -p 8888```. This will run the the agent that allows the offboard node to access PX4 topics.
### Step 2 
In an another terminal, navigate to the PX4 folder and run ```make px4_sitl gazebo-classic_standard_vtol```. This should do some stuff for a bit (will take some time if you have never done this command before). Then it will open gazebo and give you access to the PX4 shell/console.
### Step 3
In yet another terminal, navigate to your onboard_ws folder, and run ```source ./install/setup.bash```. Then run ```ros2 run px4_offboard_control offboard_node```
### Extra step
You can now interact with the offboard node's action queue through the services it exposes. Example : ```ros2 service call /px4_action_queue/append_action custom_msgs/srv/SendAction "{action: 1, x: 0., y: 0., z: 0.}"``` will enqueue a take off into the action queue. You can also refer to the various testing scripts to see more use cases.
### Required packages
mavsdk

OpenCV
