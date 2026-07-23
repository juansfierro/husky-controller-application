from PyQt6.QtCore import (
    pyqtSignal,
)
from PyQt6.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QFormLayout,
    QGridLayout,
    QDoubleSpinBox,
    QPushButton
)
from PyQt6.QtGui import QFont


class TeleopWidget(QGroupBox):
    """
    ## Teleoperations Interface
    Press directional buttons to publish movement command once.
    Hold to publish continously.
    On Release publish zero-velocity stop command

    Use boxes to enter or step through values for linear velocity (m/s) or angular velocity (rad/s):
        - Forwards, Backwards (linear.x)
        - Left, Right (angular.z)
    """

    velocity_command = pyqtSignal(float, float)

    def __init__(self):
        super().__init__("Teleop Control")

        layout = QVBoxLayout()

        speed_form = QFormLayout()
        self.linear_speed_spin = QDoubleSpinBox()
        self.linear_speed_spin.setRange(0.1, 2.0)
        self.linear_speed_spin.setSingleStep(0.1)
        self.linear_speed_spin.setValue(0.3)
        self.linear_speed_spin.setSuffix(" m/s")

        self.angular_speed_spin = QDoubleSpinBox()
        self.angular_speed_spin.setRange(0.1, 2.0)
        self.angular_speed_spin.setSingleStep(0.1)
        self.angular_speed_spin.setValue(0.5)
        self.angular_speed_spin.setSuffix(" rad/s")

        speed_form.addRow("Linear speed:", self.linear_speed_spin)
        speed_form.addRow("Angular speed:", self.angular_speed_spin)
        layout.addLayout(speed_form)

        grid = QGridLayout()
        btn_font = QFont()
        btn_font.setPointSize(14)

        def make_button(label: str) -> QPushButton:
            btn = QPushButton(label)
            btn.setFont(btn_font)
            btn.setMinimumSize(80, 80)
            return btn

        self.btn_forward = make_button("\u25b2") # ▲
        self.btn_backward = make_button("\u25bc")
        self.btn_left = make_button("\u25c4")
        self.btn_right = make_button("\u25ba")
        self.btn_stop = make_button("\u25a0")
        self.btn_stop.setStyleSheet(
            "background-color:#c0392b;" \
            "color:white;"
        )

        grid.addWidget(self.btn_forward, 0, 1)
        grid.addWidget(self.btn_left, 1, 0)
        grid.addWidget(self.btn_stop, 1, 1)
        grid.addWidget(self.btn_right, 1, 2)
        grid.addWidget(self.btn_backward, 2, 1)
        layout.addLayout(grid)

        self.setLayout(layout)

        self.btn_forward.pressed.connect(lambda: self._send(1, 0))
        self.btn_forward.released.connect(lambda: self._send(0, 0))

        self.btn_backward.pressed.connect(lambda: self._send(-1, 0))
        self.btn_backward.released.connect(lambda: self._send(0, 0))

        self.btn_left.pressed.connect(lambda: self._send(0, 1))
        self.btn_left.released.connect(lambda: self._send(0, 0))

        self.btn_right.pressed.connect(lambda: self._send(0, -1))
        self.btn_right.released.connect(lambda: self._send(0, 0))

        self.btn_stop.clicked.connect(lambda: self._send(0, 0))

    def _send(self, linear_dir: int, angular_dir: int):
        linear = linear_dir * self.linear_speed_spin.value()
        angular = angular_dir * self.angular_speed_spin.value()
        # print(f"[TeleopWidget.py]: (publish /cmd_vel) Linear.x: {linear} | Angular.z: {angular}")
        self.velocity_command.emit(linear, angular)

    def set_enabled_controls(self, enabled: bool):
        for btn in (self.btn_forward, self.btn_backward, self.btn_left, 
                    self.btn_right, self.btn_stop):
            btn.setEnabled(enabled)