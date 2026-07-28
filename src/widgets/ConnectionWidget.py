from PyQt6.QtCore import (
    pyqtSignal
)
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel
)

class ConnectionWidget(QGroupBox):
    """
    ### Connection Panel
        Host: IP Address
        Port: 9090 (default)
    """

    connect_requested = pyqtSignal(str, int) #IP, PORT
    disconnect_requested = pyqtSignal()

    def __init__(self):
        super().__init__("Connection Panel")
        layout = QHBoxLayout()

        self.host_input = QLineEdit(None)
        self.host_input.setPlaceholderText("IP Address")

        self.port_input = QLineEdit("9090")
        self.port_input.setFixedWidth(60)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self._on_connect_clicked)

        layout.addWidget(QLabel("Host:"))
        layout.addWidget(self.host_input)
        layout.addWidget(QLabel("Port:"))
        layout.addWidget(self.port_input)
        layout.addWidget(self.connect_btn)

        self.setLayout(layout)
        self._connected = False

    def _on_connect_clicked(self):
        if self._connected:
            self.disconnect_requested.emit()
        else:
            host = self.host_input.text().strip()
            try:
                port = int(self.port_input.text().strip())
            except ValueError:
                port = 9090
            self.connect_requested.emit(host, port)

    def set_connected_state(self, connected: bool):
        self._connected = connected
        self.connect_btn.setText("Disconnect" if connected else "Connect")
        self.host_input.setEnabled(not connected)
        self.port_input.setEnabled(not connected)
