#!/usr/bin/env python3
import json
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped
from std_msgs.msg import String

NAMESPACE = "a200_0867"

class PiInterceptNode(Node):
    def __init__(self):
        super().__init__("pi_intercept_logger")
        self.metrics_pub = self.create_publisher(String, "pi_test_metrics", 10)
        self.cmd_sub = self.create_subscription(TwistStamped, f"{NAMESPACE}/cmd_vel", self.cmd_callback, 10)


    def cmd_callback(self, msg):
        pi_recv_time = self.get_clock().now().nanoseconds / 1e9
        msg_stamp = msg.header.stamp.sec + (msg.header.stamp.nanosec / 1e9)

        payload = {
            "trial_id": msg.header.frame_id,
            "msg_stamp_sec": msg_stamp,
            "pi_recv_stamp": pi_recv_time,
            "command_send_delta_ms": (pi_recv_time - msg_stamp) * 1000.0
        }
        out_msg = String()
        out_msg.data = json.dumps(payload)
        self.metrics_pub.publish(out_msg)

def main(args=None):
    rclpy.init(args=args)
    node = PiInterceptNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()