from PyQt6.QtCore import (
    Qt,
    pyqtSignal,
)
from PyQt6.QtWidgets import (
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGridLayout,
    QDoubleSpinBox,
    QPushButton,
    QSlider,
    QLabel
)
from PyQt6.QtGui import (
    QFont,
    QKeyEvent
)

def truncate(num: float, places: int):
    num_str = str(num)
    if '.' not in num_str:
        return

    integer_part, decimal_part = num_str.split('.')
    trunc_str = f"{integer_part}.{decimal_part[:places]}"
    return float(trunc_str)


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

    # For compatibility between QSlider and QDoubleSpinBox
    SCALE = 100

    #Linear velocity range
    MAX_LINEAR_VELOCITY = 2.0
    MIN_LINEAR_VELOCITY = 0.1
    STEP_INTERVAL_LINEAR_VELOCITY = 0.1

    MAX_ANGULAR_VELOCITY = 2.0
    MIN_ANGULAR_VELOCITY = 0.1
    STEP_INTERVAL_ANGULAR_VELOCITY = 0.1

    def __init__(self):
        super().__init__("Teleop Control")
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        layout = QVBoxLayout()

        speed_adjust = QVBoxLayout()

        linear_speed_adjust = QHBoxLayout()
        linear_speed_layout = QVBoxLayout()
        linear_step_layout = QVBoxLayout()

        linear_step_label = QLabel("Step:")

        self.linear_step_spin = QDoubleSpinBox()
        self.linear_step_spin.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.linear_step_spin.setRange(0.01, 1.0)
        self.linear_step_spin.setValue(0.1)
        self.linear_step_spin.setSingleStep(0.01)

        self.linear_step_spin.valueChanged.connect(
            lambda val: self._set_linear_step(val)
        )
        linear_label = QLabel("Linear Speed:")

        self.linear_speed_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.linear_speed_slider.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.linear_speed_slider.setTickPosition(self.linear_speed_slider.TickPosition.TicksBelow)
        self.linear_speed_slider.setRange(
            int(self.MIN_LINEAR_VELOCITY * self.SCALE), int(self.MAX_LINEAR_VELOCITY * self.SCALE))
        self.linear_speed_slider.setTickInterval(int(self.STEP_INTERVAL_LINEAR_VELOCITY * self.SCALE))
        self.linear_speed_slider.setValue(30)

        self.linear_speed_spin = QDoubleSpinBox()
        self.linear_speed_spin.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.linear_speed_spin.setRange(self.MIN_LINEAR_VELOCITY, self.MAX_LINEAR_VELOCITY)
        self.linear_speed_spin.setSingleStep(self.STEP_INTERVAL_LINEAR_VELOCITY)
        self.linear_speed_spin.setValue(0.3)
        self.linear_speed_spin.setSuffix(" m/s")

        self.linear_speed_spin.valueChanged.connect(
            lambda val: self.linear_speed_slider.setValue(int(val * self.SCALE))
        )
        self.linear_speed_slider.valueChanged.connect(
            lambda val: self.linear_speed_spin.setValue(val / self.SCALE)
        )

        linear_step_layout.addWidget(linear_step_label)
        linear_step_layout.addWidget(self.linear_step_spin)
        linear_speed_layout.addWidget(linear_label)
        linear_speed_layout.addWidget(self.linear_speed_spin)

        linear_speed_adjust.addLayout(linear_speed_layout)
        linear_speed_adjust.addLayout(linear_step_layout)
        speed_adjust.addLayout(linear_speed_adjust)
        speed_adjust.addWidget(self.linear_speed_slider)

        angular_speed_adjust = QHBoxLayout()
        angular_speed_layout = QVBoxLayout()
        angular_step_layout = QVBoxLayout()

        angular_step_label = QLabel("Step:")

        self.angular_step_spin = QDoubleSpinBox()
        self.angular_step_spin.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.angular_step_spin.setRange(0.01, 1.0)
        self.angular_step_spin.setValue(0.1)
        self.angular_step_spin.setSingleStep(0.01)

        self.angular_step_spin.valueChanged.connect(
            lambda val: self._set_angular_step(val)
        )
        angular_label = QLabel("Angular Speed:")

        self.angular_speed_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.angular_speed_slider.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.angular_speed_slider.setTickPosition(self.angular_speed_slider.TickPosition.TicksBelow)
        self.angular_speed_slider.setRange(
            int(self.MIN_ANGULAR_VELOCITY * self.SCALE), int(self.MAX_ANGULAR_VELOCITY * self.SCALE))
        self.angular_speed_slider.setTickInterval(int(self.STEP_INTERVAL_ANGULAR_VELOCITY * self.SCALE))
        self.angular_speed_slider.setValue(50)

        self.angular_speed_spin = QDoubleSpinBox()
        self.angular_speed_spin.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.angular_speed_spin.setRange(self.MIN_ANGULAR_VELOCITY, self.MAX_ANGULAR_VELOCITY)
        self.angular_speed_spin.setSingleStep(self.STEP_INTERVAL_ANGULAR_VELOCITY)
        self.angular_speed_spin.setValue(0.5)
        self.angular_speed_spin.setSuffix(" rad/s")

        self.angular_speed_spin.valueChanged.connect(
            lambda val: self.angular_speed_slider.setValue(int(val * self.SCALE))
        )
        self.angular_speed_slider.valueChanged.connect(
            lambda val: self.angular_speed_spin.setValue(val / self.SCALE)
        )

        angular_speed_layout.addWidget(angular_label)
        angular_speed_layout.addWidget(self.angular_speed_spin)
        angular_step_layout.addWidget(angular_step_label)
        angular_step_layout.addWidget(self.angular_step_spin)

        angular_speed_adjust.addLayout(angular_speed_layout)
        angular_speed_adjust.addLayout(angular_step_layout)
        speed_adjust.addLayout(angular_speed_adjust)
        speed_adjust.addWidget(self.angular_speed_slider)

        layout.addLayout(speed_adjust)

        grid = QGridLayout()
        btn_font = QFont()
        btn_font.setPointSize(14)

        def make_button(label: str) -> QPushButton:
            btn = QPushButton(label)
            btn.setFont(btn_font)
            btn.setMinimumSize(80, 80)
            return btn

        self.btn_forward = make_button("\u25b2")
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

    def keyPressEvent(self, event: QKeyEvent):
        if event.isAutoRepeat():
            return

        key = event.key()
        if key == Qt.Key.Key_Up:
            self.btn_forward.setDown(True)
            self._send(1, 0)
        elif key == Qt.Key.Key_Down:
            self.btn_backward.setDown(True)
            self._send(-1, 0)
        elif key == Qt.Key.Key_Left:
            self.btn_left.setDown(True)
            self._send(0, 1)
        elif key == Qt.Key.Key_Right:
            self.btn_right.setDown(True)
            self._send(0, -1)
        elif key == Qt.Key.Key_Space:
            self.btn_stop.setDown(True)
        elif key == Qt.Key.Key_W:
            self.linear_speed_spin.setValue(
                self.linear_speed_spin.value() + self.STEP_INTERVAL_LINEAR_VELOCITY
            )
        elif key == Qt.Key.Key_S:
            self.linear_speed_spin.setValue(
                self.linear_speed_spin.value() - self.STEP_INTERVAL_LINEAR_VELOCITY
            )
        elif key == Qt.Key.Key_Q:
            self.angular_speed_spin.setValue(
                self.angular_speed_spin.value() + self.STEP_INTERVAL_ANGULAR_VELOCITY
            )
        elif key == Qt.Key.Key_A:
            self.angular_speed_spin.setValue(
                self.angular_speed_spin.value() - self.STEP_INTERVAL_ANGULAR_VELOCITY
            )
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        if event.isAutoRepeat():
            return

        key = event.key()
        if key == Qt.Key.Key_Up:
            self.btn_forward.setDown(False)
            self._send(0, 0)
        elif key == Qt.Key.Key_Down:
            self.btn_backward.setDown(False)
            self._send(0, 0)
        elif key == Qt.Key.Key_Left:
            self.btn_left.setDown(False)
            self._send(0, 0)
        elif key == Qt.Key.Key_Right:
            self.btn_right.setDown(False)
            self._send(0, 0)
        elif key == Qt.Key.Key_Space:
            self.btn_stop.setDown(False)
        else:
            super().keyReleaseEvent(event)

    def _set_linear_step(self, value):
        self.STEP_INTERVAL_LINEAR_VELOCITY = value

    def _set_angular_step(self, value):
        self.STEP_INTERVAL_ANGULAR_VELOCITY = value