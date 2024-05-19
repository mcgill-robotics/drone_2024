import rclpy
from rclpy.node import Node

from std_msgs.msg import String
from std_msgs.msg import Float32
from custom_msgs.msg import Waypoint
from custom_msgs.msg import Target
from custom_msgs.msg import ListTargets
from custom_msgs.msg import GlobalCoordinates
from custom_msgs.msg import ListGlobalCoordinates
from custom_msgs.msg import VehicleInfo
from geometry_msgs.msg import Polygon
from geometry_msgs.msg import Point32

from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy, QoSDurabilityPolicy

import pymap3d as pm


class MissionNode(Node):

    def __init__(self):
        super().__init__('mission_node')
        self.qos_profile = QoSProfile(
            reliability=QoSReliabilityPolicy.
            RMW_QOS_POLICY_RELIABILITY_BEST_EFFORT,
            durability=QoSDurabilityPolicy.
            RMW_QOS_POLICY_DURABILITY_TRANSIENT_LOCAL,
            history=QoSHistoryPolicy.RMW_QOS_POLICY_HISTORY_KEEP_LAST,
            depth=1)

        self.vehicle_info_sub = self.create_subscription(
            VehicleInfo, "/px4_monitoring/vehicle_info",
            self.vehicle_info_callback, self.qos_profile)
        self.curr_n, self.curr_e, self.curr_d = None, None, None
        self.lat0, self.lon0, self.alt0 = None, None, None

        self.mission_boundary_sub = self.create_subscription(
            ListGlobalCoordinates, "/mission_boundary",
            self.mission_boundary_callback, self.qos_profile)

        self.lap_points_sub = self.create_subscription(
            ListGlobalCoordinates, "/mission_lap", self.mission_lap_callback,
            self.qos_profile)
        self.lap = None
        self.curr_lap_point_index = 0

        self.target_list_sub = self.create_subscription(
            ListTargets, "/mission_targets", self.targets_callback,
            self.qos_profile)
        self.targets = None

        self.lap_tolerance_sub = self.create_subscription(
            Float32, "/mission_lap_tolerance", self.lap_tolerance_callback,
            self.qos_profile)
        self.curr_tolerance = 3.0

        self.mission_status_pub = self.create_publisher(
            String, "/mission_status", self.qos_profile)

        self.boundary_setter_pub = self.create_publisher(
            Polygon, "/boundary_setter", 10)

        self.goal_waypoint_pub = self.create_publisher(Waypoint,
                                                       "/goal_waypoint",
                                                       self.qos_profile)

        timer_period = 0.5
        self.timer_1 = self.create_timer(timer_period, self.perform_lap)

    def vehicle_info_callback(self, msg: VehicleInfo):
        self.curr_n, self.curr_e, self.curr_d = msg.x, msg.y, msg.z
        self.lat0, self.lon0, self.alt0 = msg.ref_lat, msg.ref_lon, msg.ref_alt

    def get_ned(self, lat, lon, alt):
        if self.lat0 is None:
            self.warn_pub(
                "Not quite ready to translate coordinates to ned, waiting on vehicle info..."
            )
            return None
        n, e, d = pm.geodetic2ned(lat, lon, alt, self.lat0, self.lon0,
                                  self.alt0)
        return n, e, d

    def mission_boundary_callback(self, msg: ListGlobalCoordinates):
        if self.lat0 is None:
            self.warn_pub(
                "Not quite ready to take in coordinates for boundary, waiting on vehicle info..."
            )
            return
        polygon = Polygon()
        polygon.points = []
        for glob in msg.coords:
            glob: GlobalCoordinates = glob
            n, e, d = self.get_ned(glob.latitude, glob.longitude,
                                   glob.altitude)
            point = Point32()
            point.x, point.y, point.z = n, e, d
            polygon.points.append(point)

        self.boundary_setter_pub.publish(polygon)

    def mission_lap_callback(self, msg: ListGlobalCoordinates):
        if self.lat0 is None:
            info_string = "Not quite ready to take in coordinates for laps, waiting on vehicle info..."
            self.warn_pub(info_string)
            return
        self.lap = []
        self.curr_lap_point_index = 0
        for glob in msg.coords:
            glob: GlobalCoordinates = glob
            n, e, d = self.get_ned(glob.latitude, glob.longitude,
                                   glob.altitude)
            self.lap.append((n, e, d))

    def targets_callback(self, msg: ListTargets):
        self.targets = []
        for target in msg.targets:
            self.targets.append(target)

    def lap_tolerance_callback(self, msg: Float32):
        if (msg.data <= 0.):
            self.warn_pub(
                "Lap tolerance must be a positive floating point number")
            return
        self.curr_tolerance = msg.data

    def distance_from_curr_lap_dest(self):
        target_n, target_e, target_d = self.lap[self.curr_lap_point_index]
        return ((target_n - self.curr_n)**2 + (target_e - self.curr_e)**2 +
                (target_d - self.curr_d)**2)**(1 / 2)

    def get_max_speed_h(self):
        return 8.0

    def perform_lap(self):
        if (self.curr_n is None):
            self.warn_pub(
                "Not quite ready to perform lap yet, waiting on vehicle info..."
            )
            return

        if (self.lap is None):
            self.warn_pub(
                "Not quite ready to perform lap yet, lap wasn't set.")
            return

        if (self.distance_from_curr_lap_dest() <= self.curr_tolerance):
            self.curr_lap_point_index = (self.curr_lap_point_index + 1) % len(
                self.lap)
        msg = Waypoint()
        (n, e, d) = self.lap[self.curr_lap_point_index]
        msg.x, msg.y, msg.z = n, e, d
        msg.max_speed_h = self.get_max_speed_h()
        self.goal_waypoint_pub.publish(msg)
        self.warn_pub(
            f"Trying to go to {self.lap[self.curr_lap_point_index]}, curr_index: {self.curr_lap_point_index}"
        )

    def warn_pub(self, string):
        self.get_logger().warn(string)
        string_msg = String()
        string_msg.data = string
        self.mission_status_pub.publish(string_msg)


def main(args=None):
    rclpy.init(args=args)

    minimal_publisher = MissionNode()

    rclpy.spin(minimal_publisher)

    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    minimal_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
