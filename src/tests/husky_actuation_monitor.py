#!/usr/bin/env python3
import json
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped
from sensor_msgs.msg import JointState
from std_msgs.msg import String

NAMESPACE = "a200_0867"
# Velocity threshold to consider wheels as "moving" (rad/s or m/s depending on JointState config)
VELOCITY_THRESHOLD = 0.02  

class HuskyActuationMonitor(Node):
    def __init__(self):
        super().__init__("husky_actuation_monitor")

        self.current_trial_id = None
        self.cmd_recv_time = None
        self.msg_stamp = None
        self.waiting_for_motion = False

        self.metrics_pub = self.create_publisher(String, f"{NAMESPACE}/test_metrics", 10 )
        
        self.cmd_sub = self.create_subscription(TwistStamped, f"{NAMESPACE}/cmd_vel", self.cmd_callback, 10)
        
        self.joint_sub = self.create_subscription(JointState, f"{NAMESPACE}/platform/joint_states", self.joint_callback, 10)

    def cmd_callback(self, msg):
        # Ignore zero velocity stop commands for test triggers
        if msg.twist.linear.x > 0 and not self.waiting_for_motion:
            self.cmd_recv_time = self.get_clock().now().nanoseconds / 1e9
            self.msg_stamp = msg.header.stamp.sec + (msg.header.stamp.nanosec / 1e9)
            self.current_trial_id = msg.header.frame_id
            self.waiting_for_motion = True

    def joint_callback(self, msg):
        if self.waiting_for_motion:
            # JointState 'velocity' contains an array of wheel speeds.
            # We check if any of the wheels exceed the physical movement threshold.
            if msg.velocity:
                max_wheel_speed = max([abs(v) for v in msg.velocity])
            else:
                max_wheel_speed = 0.0
            
            if max_wheel_speed >= VELOCITY_THRESHOLD:
                motion_detected_time = self.get_clock().now().nanoseconds / 1e9
                actuation_delay_ms = (motion_detected_time - self.cmd_recv_time) * 1000.0

                payload = {
                    "trial_id": self.current_trial_id,
                    "msg_stamp": self.msg_stamp,
                    "husky_recv_stamp": self.cmd_recv_time,
                    "wheel_motion_stamp": motion_detected_time,
                    "actuation_delay_ms": round(actuation_delay_ms, 2)
                }
                out_msg = String()
                out_msg.data = json.dumps(payload)
                self.metrics_pub.publish(out_msg)
                
                self.get_logger().info(f"Motion detected for {self.current_trial_id}. Delay: {actuation_delay_ms:.2f} ms")
                self.waiting_for_motion = False  # Reset state for next iteration

def main(args=None):
    rclpy.init(args=args)
    monitor = HuskyActuationMonitor()
    rclpy.spin(monitor)
    rclpy.shutdown()

if __name__ == '__main__':
    main()