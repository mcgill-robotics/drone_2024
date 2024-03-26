#!/usr/bin/env python

__autor__="Imad Issafras"
__contact__="imad.issafras@outlook.com"

# ROS imports
import rclpy
from rclpy.node import Node
from rclpy.clock import Clock
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy, QoSDurabilityPolicy

# ROS msgs and srvs types
from custom_msgs.msg import VehicleInfo
from custom_msgs.msg import Action
from custom_msgs.srv import SendAction
from custom_msgs.srv import RequestAction

# PX4 messages
## In
from px4_msgs.msg import VehicleLocalPosition
from px4_msgs.msg import VehicleStatus
from px4_msgs.msg import BatteryStatus
from px4_msgs.msg import VehicleCommandAck

## Out
from px4_msgs.msg import OffboardControlMode
from px4_msgs.msg import GotoSetpoint
from px4_msgs.msg import VehicleCommand

# Other PX4
from px4_msgs.msg import VtolVehicleStatus

# Other imports 
import collections
from typing import Deque
from enum import Enum
from mavsdk import System
from mavsdk.offboard import PositionNedYaw
import asyncio
import os 

class OffboardControl(Node):
    class Action:
        TAKE_OFF_ID = 1
        WAYPOINT_ID = 2
        LANDING_ID = 3
        TRANSITION_QC_ID = 4
        TRANSITION_FW_ID = 5
    
        def __init__(self, des : str, action_type : int) -> None:
            self.description = des
            self.action_type = action_type

        def perform(self, offboard_object : "OffboardControl"):
            pass
        
        @staticmethod
        def construct_action(action_type, x = None, y = None, z = None) -> "OffboardControl.Action":
            if (action_type == OffboardControl.Action.TAKE_OFF_ID):
                return OffboardControl.TakeOff()
            elif (action_type == OffboardControl.Action.WAYPOINT_ID):
                return OffboardControl.Waypoint(x, y, z)
            elif (action_type == OffboardControl.Action.LANDING_ID):
                return OffboardControl.Landing()
            elif (action_type == OffboardControl.Action.TRANSITION_QC_ID):
                return OffboardControl.TransitionQC()
            elif (action_type == OffboardControl.Action.TRANSITION_FW_ID):
                return OffboardControl.TransitionFW()
            else:
                print(f"[WARNING] {action_type} is not a valid action type id") 
    
    class TakeOff(Action):
        def __init__(self):
            super().__init__("Take off", OffboardControl.Action.TAKE_OFF_ID)
            self.setup_done = False
        
        def perform(self, offboard_object : "OffboardControl"):
            offboard_object.takeoff(self)
            
    class Waypoint(Action):
        def __init__(self, x, y, z) -> None:
            super().__init__(f"Waypoint to ({x}, {y}, {z})", OffboardControl.Action.WAYPOINT_ID)
            self.x = x
            self.y = y
            self.z = z

        def perform(self, offboard_object : "OffboardControl"):
            offboard_object.waypoint(self.x, self.y, self.z)

    class Landing(Action):
        def __init__(self):
            super().__init__("Landing", OffboardControl.Action.LANDING_ID)

        def perform(self, offboard_object : "OffboardControl"):
            offboard_object.land()

    class FlightConfiguration(Enum):
        QUAD_COPTER_CONFIGURATION = 1
        FIXED_WING_CONFIGURATION = 2

        def other(self)->"OffboardControl.FlightConfiguration":
            return OffboardControl.FlightConfiguration.QUAD_COPTER_CONFIGURATION if \
                self == OffboardControl.FlightConfiguration.FIXED_WING_CONFIGURATION else \
                      OffboardControl.FlightConfiguration.FIXED_WING_CONFIGURATION

        def get_vtol_status(self):
            if (self == OffboardControl.FlightConfiguration.QUAD_COPTER_CONFIGURATION):
                return VtolVehicleStatus.VEHICLE_VTOL_STATE_MC
            return VtolVehicleStatus.VEHICLE_VTOL_STATE_FW
        
        def get_tolerance(self):
            if (self == OffboardControl.FlightConfiguration.QUAD_COPTER_CONFIGURATION):
                return 3.
            if (self == OffboardControl.FlightConfiguration.FIXED_WING_CONFIGURATION):
                return 7.
            
    class TransitionQC(Action):
        def __init__(self):
            super().__init__("Transition to Quad Copter", OffboardControl.Action.TRANSITION_QC_ID)

        def perform(self, offboard_object : "OffboardControl"):
            offboard_object.transition(OffboardControl.FlightConfiguration.QUAD_COPTER_CONFIGURATION)

    class TransitionFW(Action):
        def __init__(self):
            super().__init__("Transition to Fixed wing", OffboardControl.Action.TRANSITION_FW_ID)

        def perform(self, offboard_object : "OffboardControl"):
            offboard_object.transition(OffboardControl.FlightConfiguration.FIXED_WING_CONFIGURATION)

    def exec_until_completion(self, coroutine):
        return self.loop.run_until_complete(coroutine)

    def __init__(self, loop):
        super().__init__('px4_controller')

        qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.RMW_QOS_POLICY_RELIABILITY_BEST_EFFORT,
            durability=QoSDurabilityPolicy.RMW_QOS_POLICY_DURABILITY_TRANSIENT_LOCAL,
            history=QoSHistoryPolicy.RMW_QOS_POLICY_HISTORY_KEEP_LAST,
            depth=1
        )

        # Used to synchify async activities in mavsdk
        self.loop = loop 
        ## MAV SDK
        self.drone = System()
        self.exec_until_completion(self.drone.connect())

        # PX4 pubs / subs
        ## PX4 SUBS
        self.vehicle_status_sub = self.create_subscription(
            VehicleStatus, '/fmu/out/vehicle_status',
            self.vehicle_status_callback, qos_profile=qos_profile
            )
        self.vehicle_status : VehicleStatus | None  = None
        
        self.vehicle_local_position_sub = self.create_subscription(
            VehicleLocalPosition, '/fmu/out/vehicle_local_position',
            self.vehicle_local_position_callback,
            qos_profile=qos_profile
        )
        self.vehicle_local_position : VehicleLocalPosition | None = None

        self.vehicle_battery_status_sub = self.create_subscription(
            BatteryStatus, '/fmu/out/battery_status',
            self.vehicle_battery_status_callback,
            qos_profile=qos_profile
        )
        self.vehicle_battery_status : BatteryStatus | None = None

        self.vehicle_command_ack_sub = self.create_subscription(
            VehicleCommandAck, '/fmu/out/vehicle_command_ack',
              self.vehicle_command_ack_callback,
              qos_profile
        )
        self.vehicle_command_ack : VehicleCommandAck | None = None

        ## PX4 PUBS
        self.offboard_mode_pub = self.create_publisher(
            OffboardControlMode, '/fmu/in/offboard_control_mode', qos_profile)

        self.goto_setpoint_pub = self.create_publisher(
            GotoSetpoint, '/fmu/in/goto_setpoint', qos_profile
        )

        self.vehicle_command_pub = self.create_publisher(
            VehicleCommand, '/fmu/in/vehicle_command', qos_profile
        )

        # custom pubs / subs
        self.vehicle_info_pub = self.create_publisher(
            VehicleInfo, '/px4_monitoring/vehicle_info', qos_profile
        )


        self.enqueue_action_service = self.create_service(
            SendAction, '/px4_action_queue/append_action', self.enqueue_action_callback
        )

        self.pop_action_service = self.create_service(
            RequestAction, '/px4_action_queue/popright_action', self.popright_action_callback
        )
        
        # publishers timing
        timer_period = 0.1
        self.timer = self.create_timer(timer_period, self.timer_callback)

        self.action_queue : Deque[OffboardControl.Action] = collections.deque([])

        timer_period_actions = 0.2
        self.timer_action = self.create_timer(timer_period_actions, self.action_executor)
        self.current_flight_configuration = OffboardControl.FlightConfiguration.QUAD_COPTER_CONFIGURATION
        self._transition_toggle = True

    def offboard_mode_publish(self):
        offboard_msg = OffboardControlMode()
        offboard_msg.timestamp = int(Clock().now().nanoseconds / 1000)
        offboard_msg.position=True
        offboard_msg.velocity=False
        offboard_msg.acceleration=False
        self.offboard_mode_pub.publish(offboard_msg)
    
    def print_vehicle_info(self, info : VehicleInfo):
        dash_length = os.get_terminal_size()[0]
        string = "\n" + ('-' * dash_length) + "\n"
        string += f"(N, E, D): ({info.x:.4f}, {info.y:.4f}, {info.z:.4f})\n"
        string += f"(VN, VE, VD): ({info.vx:.4f}, {info.vy:.4f}, {info.vz:.4f})\n"
        string += f"power level: {info.powerlevel:.2f}%\t"
        mode_string = "FW" if info.mode == VehicleStatus.VEHICLE_TYPE_FIXED_WING else \
                        "QC" if info.mode == VehicleStatus.VEHICLE_TYPE_ROTARY_WING else "OTHER"
        string += f"mode: {info.mode}, {mode_string}\n"
        string += f"current action: {info.current_action}\n"
        string += '-' * dash_length
        self.get_logger().info(string)

    def vehicle_info_publish(self):
        vehicle_info = VehicleInfo()

        # position and velocity
        if (self.vehicle_local_position is not None):
            vehicle_info.x = self.vehicle_local_position.x
            vehicle_info.y = self.vehicle_local_position.y
            vehicle_info.z = self.vehicle_local_position.z

            vehicle_info.vx = self.vehicle_local_position.vx
            vehicle_info.vy = self.vehicle_local_position.vy
            vehicle_info.vz = self.vehicle_local_position.vz
        # mode 
        if (self.vehicle_status is not None):
            vehicle_info.mode = self.vehicle_status.vehicle_type
        # power
        if (self.vehicle_battery_status is not None):
            vehicle_info.powerlevel = self.vehicle_battery_status.remaining * 100 
        # actions
        if (len(self.action_queue) == 0):
            vehicle_info.current_action = "No action to be done"
        else:
            vehicle_info.current_action = self.action_queue[0].description

        self.print_vehicle_info(vehicle_info)

        self.vehicle_info_pub.publish(vehicle_info)

    def timer_callback(self):
        self.offboard_mode_publish()
        self.vehicle_info_publish()

    def send_vehicle_command(self, cmd, param1=None, param2=None, param3=None, 
                             param4=None, param5=None, param6=None, param7=None):
        vehicle_command = VehicleCommand()
        vehicle_command.command = cmd  # command ID

        for i in range(1, 8):
            parameter_input = vars()[f"param{i}"]
            if parameter_input is not None:
                vehicle_command.__setattr__(f"param{i}", parameter_input)

        vehicle_command.target_system = 1  # system which should execute the command
        vehicle_command.target_component = 1  # component which should execute the command, 0 for all components
        vehicle_command.source_system = 1  # system sending the command
        vehicle_command.source_component = 1  # component sending the command
        vehicle_command.from_external = True
        vehicle_command.timestamp = int(Clock().now().nanoseconds / 1000) # time in microseconds

        self.vehicle_command_pub.publish(vehicle_command)

    def action_executor(self):
        if (len(self.action_queue) == 0): 
            self.exec_until_completion(self.drone.offboard.stop())
        else:
            if (not self.exec_until_completion(self.drone.offboard.is_active())):
                self.exec_until_completion(self.drone.offboard.set_position_ned(PositionNedYaw(-self.vehicle_local_position.x,
                                                                                                   -self.vehicle_local_position.y,
                                                                                                   -self.vehicle_local_position.z,
                                                                                                   -self.vehicle_local_position.heading)))
                self.exec_until_completion(self.drone.offboard.start())
            self.action_queue[0].perform(self)

    def takeoff(self, action_ob:TakeOff):
        """
            Takeoff action, only completes when within 0.1 m of the target height
        """
        if (not action_ob.setup_done):
            # Setup 
            ## ARM
            self.send_vehicle_command(VehicleCommand.VEHICLE_CMD_DO_SET_MODE, 1., 6.)
            self.send_vehicle_command(VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM, param1=float(VehicleCommand.ARMING_ACTION_ARM))
            action_ob.setup_done = True

        # set wapoint to be up high
        target_height = -10.
        
        trajectorySetpoint = GotoSetpoint()
        trajectorySetpoint.position = [0.0, 0.0, target_height]
        self.goto_setpoint_pub.publish(trajectorySetpoint)

        if (abs(self.vehicle_local_position.z - target_height) <= 0.1): 
            self.action_queue.popleft()
        
    def current_tolerance(self):
        """
            defines the distance tolerances for Quad Copter and fixed wing configuartion
        """
        if (self.current_flight_configuration == OffboardControl.FlightConfiguration.QUAD_COPTER_CONFIGURATION):
            return 3.
        if (self.current_flight_configuration == OffboardControl.FlightConfiguration.FIXED_WING_CONFIGURATION):
            return 7.

    def waypoint(self, x, y, z, yaw = 0.0):
        """
            Waypoint action, only completes when within current_tolarance from the target waypoint
        """
        if (self.current_flight_configuration == OffboardControl.FlightConfiguration.QUAD_COPTER_CONFIGURATION):
            trajectorySetpoint = GotoSetpoint()
            trajectorySetpoint.position = [x, y, z]
            self.goto_setpoint_pub.publish(trajectorySetpoint)
        else:
            self.exec_until_completion(self.drone.offboard.set_position_ned(PositionNedYaw(x, y, z, yaw)))
        if (((self.vehicle_local_position.x - x) ** (2) +
             (self.vehicle_local_position.y - y) ** (2) +
             (self.vehicle_local_position.z - z) ** (2)) ** (1/2) <= self.current_flight_configuration.get_tolerance()):
            self.action_queue.popleft()

    def land(self):
        """
            Landing Action, only completes when drone is disarmed
        """
        if (self.vehicle_command_ack.command != VehicleCommand.VEHICLE_CMD_NAV_LAND or 
                self.vehicle_command_ack.result != VehicleCommandAck.VEHICLE_CMD_RESULT_ACCEPTED):
            self.send_vehicle_command(VehicleCommand.VEHICLE_CMD_NAV_LAND)
        if (self.vehicle_status.arming_state == VehicleStatus.ARMING_STATE_DISARMED):
            self.action_queue.popleft()

    def transition(self, mode : FlightConfiguration):
        """
            Transition action, completes when the current flight mode is the same as the desired flight mode
        """
        if (mode == self.current_flight_configuration):
            self.action_queue.popleft()
            return
        
        self.send_vehicle_command(VehicleCommand.VEHICLE_CMD_DO_VTOL_TRANSITION, float(mode.get_vtol_status()))
        
        if (mode == OffboardControl.FlightConfiguration.FIXED_WING_CONFIGURATION):
            throtle_percentage = 0.80
            self.send_vehicle_command(VehicleCommand.VEHICLE_CMD_DO_CHANGE_SPEED, 1., -1., throtle_percentage)

        self.current_flight_configuration = mode

    def vehicle_status_callback(self, msg : VehicleStatus):
        self.vehicle_status = msg

    def vehicle_local_position_callback(self, msg : VehicleLocalPosition):
        self.vehicle_local_position = msg

    def vehicle_battery_status_callback(self, msg : BatteryStatus):
        self.vehicle_battery_status = msg

    def vehicle_command_ack_callback(self, msg : VehicleCommandAck):
        self.vehicle_command_ack = msg
    
    def enqueue_action_callback(self, req, res):
        action = OffboardControl.Action.construct_action(req.action.action, req.action.x, req.action.y, req.action.z)
        self.action_queue.append(action)
        res.success = True
        return res
    
    def popright_action_callback(self, req, res):
        if (len(self.action_queue) == 0):
            res.action.action = Action.ACTION_NONE
            return res
        action : OffboardControl.Action = self.action_queue.pop()
        res.action.action = action.action_type
        res.action.x = action.x
        res.action.y = action.y
        res.action.z = action.z
        return res


def main(args=None):

    rclpy.init(args=args)
    loop = asyncio.get_event_loop()
    offboard_control = OffboardControl(loop)
    rclpy.spin(offboard_control)

    loop.close()
    offboard_control.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
