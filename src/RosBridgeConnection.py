import roslibpy
import time
from PyQt6.QtCore import (
    QObject,
    QTimer,
    pyqtSignal,
)

class RosBridgeConnection(QObject):
    """
    [ADD COMMENT]
    """

    connected = pyqtSignal()
    disconnected = pyqtSignal()
    connection_error = pyqtSignal(str)

    odom_received = pyqtSignal(dict)
    battery_received = pyqtSignal(dict)

    NAMESPACE = '/a200_0867'
    CMD_VEL_RATE_HZ = 10

    def __init__(self):
        super().__init__()
        self.client: roslibpy.Ros | None = None
        self.cmd_vel_topic: roslibpy.Topic | None = None
        self.odom_topic: roslibpy.Topic | None = None
        self.battery_topic: roslibpy.Topic | None = None
        self._is_connected = False

        #Robot Idle
        self._current_linear_x = 0.0
        self._current_angular_z = 0.0

        self._cmd_vel_timer = QTimer(self)
        self._cmd_vel_timer.setInterval(int(1000 / self.CMD_VEL_RATE_HZ))
        self._cmd_vel_timer.timeout.connect(self._publish_current_velocity)

    def is_connected(self) -> bool:
        return self._is_connected

    def connect_to_bridge(self, host: str, port: int):
        """
        Create client and connect to RosBridge server
        """
        if self.client is not None:
            self.disconnect_from_bridge()
        try:
            self.client = roslibpy.Ros(host, port)
            self.client.on_ready(self._on_ready)
            self.client.on('close', self._on_close)
            self.client.on('error', self._on_error)
        except Exception as exc:
            print(f"[RosBridgeConnection.py]: (connect_to_bridge) {str(exc)}")
            self.connection_error.emit(str(exc))
            return

        try:
            self.client.run(timeout=5)
        except Exception as exc:
            print(f"[RosBridgeConnection.py]: (connect_to_bridge) {str(exc)}")
            self.connection_error.emit(str(exc))
            return

    def disconnect_from_bridge(self):
        self._cmd_vel_timer.stop()
        self._current_linear_x = 0.0
        self._current_angular_z = 0.0

        if self.cmd_vel_topic is not None:
            self.cmd_vel_topic.unadvertise()
            self.cmd_vel_topic = None

        if self.odom_topic is not None:
            self.odom_topic.unsubscribe()
            self.odom_topic = None

        if self.battery_topic is not None:
            self.battery_topic.unsubscribe()
            self.battery_topic = None

        if self.client is not None:
            try:
                self.client.terminate()
            except Exception:
                pass
            self.client = None

        self._is_connected = False

    def _on_ready(self):
        self._is_connected = True

        self.cmd_vel_topic = roslibpy.Topic(
            self.client, f"{self.NAMESPACE}/cmd_vel",
            "geometry_msgs/msg/TwistStamped"
        )
        self.cmd_vel_topic.advertise()

        self.odom_topic = roslibpy.Topic(
            self.client, f"{self.NAMESPACE}/platform/odom/filtered",
            "nav_msgs/msg/Odometry"
        )
        self.odom_topic.subscribe(self._on_odom_message)

        self.battery_topic = roslibpy.Topic(
            self.client, f"{self.NAMESPACE}/platform/bms/state",
            "sensor_msgs/msg/BatteryState"
        )
        self.battery_topic.subscribe(self._on_battery_message)

        self._cmd_vel_timer.start()

        # Signals to the app that it is ready
        self.connected.emit()

    def _on_close(self, *args):
        self._is_connected = False
        self.disconnected.emit()

    def _on_error(self, error, *args):
        self.connection_error.emit(str(error))

    def _on_odom_message(self, message: dict):
        self.odom_received.emit(message)

    def _on_battery_message(self, message: dict):
        self.battery_received.emit(message)

    def publish_velocity(self, linear_x: float, angular_z: float):
        self._current_linear_x = linear_x
        self._current_angular_z = angular_z
        print(f"[RosBridgeConnection.py]: (publish_velocity) Linear.x: {linear_x} | Angular.z: {angular_z}")

        self._publish_current_velocity()

    def _publish_current_velocity(self):
        if not self._is_connected or self.cmd_vel_topic is None:
            return

        now = time.time()
        msg = roslibpy.Message({
            "header": {
                "stamp": {
                    "sec": int(now),
                    "nanosec": int((now % 1) * 1e9),
                },
                "frame_id": "base_link",
            },
            "twist": {
                "linear": { 'x': self._current_linear_x, 'y': 0.0, 'z': 0.0},
                "angular": {'x': 0.0, 'y': 0.0, "z": self._current_angular_z}
            },
        })
        self.cmd_vel_topic.publish(msg)
