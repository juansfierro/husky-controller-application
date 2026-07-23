from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import (
    QGroupBox,
    QLabel,
    QFormLayout,
)


class TelemetryWidget(QGroupBox):
    def __init__(self):
        super().__init__("Telemetry")

        form = QFormLayout()

        self.pos_label = QLabel("x: --, y: --")
        self.linear_vel_label = QLabel("--")
        self.angular_vel_label = QLabel("--")
        self.battery_label = QLabel("--")

        form.addRow("Position:", self.pos_label)
        form.addRow("Linear vel:", self.linear_vel_label)
        form.addRow("Angular vel:", self.angular_vel_label)
        form.addRow("Battery:", self.battery_label)

        self.setLayout(form)

    @pyqtSlot(dict)
    def update_odom(self, message: dict):
        pos = message.get("pose", {}).get("pose", {}).get("position", {})
        twist = message.get("twist", {}).get("twist", {})
        linear = twist.get("linear", {})
        angular = twist.get("angular", {})

        x = pos.get("x", 0.0)
        y = pos.get("y", 0.0)
        self.pos_label.setText(f"x: {x:.2f} m, y: {y:.2f} m")
        self.linear_vel_label.setText(f"{linear.get("x", 0.0):.2f} m/s")
        self.angular_vel_label.setTest(f"{angular.get("z", 0.0):.2f} rad/s")

    @pyqtSlot(dict)
    def update_battery(self, message: dict):
        percentage = message.get("percentage")
        voltage = message.get("voltage")
        parts = []
        if voltage is not None:
            parts.append(f"{voltage:.1f} v")
        if percentage is not None:
            parts.append(f"{percentage * 100:.0f}%")
        self.battery_label.setText("  |  ".join(parts) if parts else "--")
