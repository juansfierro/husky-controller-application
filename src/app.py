import sys
from PyQt6.QtCore import (
    pyqtSlot
)
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QStatusBar
)

from RosBridgeConnection import RosBridgeConnection
from widgets.ConnectionWidget import ConnectionWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Husky A200 Controller")
        self.setMinimumSize(420, 540)

        self.ros = RosBridgeConnection()

        central = QWidget()
        layout = QVBoxLayout()

        self.connection_widget = ConnectionWidget()

        layout.addWidget(self.connection_widget)

        central.setLayout(layout)
        self.setCentralWidget(central)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Disconnected")

        self._wire_signals()

    def _wire_signals(self):
        self.connection_widget.connect_requested.connect(self.ros.connect_to_bridge)
        self.connection_widget.disconnect_requested.connect(self.ros.disconnect_from_bridge)

        self.ros.connected.connect(self._on_ros_connected)
        self.ros.disconnected.connect(self._on_ros_disconnected)
        self.ros.connection_error.connect(self._on_ros_error)

    @pyqtSlot()
    def _on_ros_connected(self):
        """
        Called when succesfully connected to RosBridge WebSocket
        """
        self.connection_widget.set_connected_state(True)
        self.status_bar.showMessage("Connected to RosBridge")

    @pyqtSlot()
    def _on_ros_disconnected(self):
        """
        Called when disconnected from RosBridge WebSocket
        """
        self.connection_widget.set_connected_state(False)
        self.status_bar.showMessage("Disconnected")

    @pyqtSlot(str)
    def _on_ros_error(self, error:str ):
        self.status_bar.showMessage(f"Connection error: {error}")

    def closeEvent(self, event):
        self.ros.publish_velocity(0.0, 0.0)
        self.ros.disconnect_from_bridge()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
