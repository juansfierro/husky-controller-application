import sys
import argparse
import os
# Suppress FFmpeg output
os.environ["OPENCV_FFMPEG_LOGLEVEL"] = "-8"
os.environ["OPENCV_LOG_LEVEL"] = "SILENT"

import cv2
import numpy as np
from PyQt6.QtCore import (
    QThread,
    pyqtSignal,
    pyqtSlot,
    Qt
)
from PyQt6.QtGui import (
    QImage,
    QPixmap,
    QAction,
    QKeySequence
)
from PyQt6.QtWidgets import (
    QApplication,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton
)

parser = argparse.ArgumentParser()

parser.add_argument('-t', action="store_true", dest="test_cam", help="Receive video stream from local camera and not from network.")
results = parser.parse_args()

class VideoCaptureThread(QThread):
    """
    [Add Comment]
    """

    frame_ready = pyqtSignal(np.ndarray)
    connection_failed = pyqtSignal(str)

    def __init__(self, port: int = 5000, parent=None):
        super().__init__(parent)
        self._port = port
        self._running = False

    def run(self):
        if results.test_cam:
            cap = cv2.VideoCapture(0)
        else:
            stream_url = f"udp://0.0.0.0:{self._port}"
            cap = cv2.VideoCapture(stream_url, cv2.CAP_FFMPEG)

        if not cap.isOpened():
            self.connection_failed.emit(
                f"Could not open UDP stream on port {self._port}."
            )
            return

        self._running = True
        while self._running:
            ret, frame = cap.read()
            if not ret:
                continue
            self.frame_ready.emit(frame)
        cap.release()

    def stop(self):
        self._running = False
        self.wait(2000)

class VideoStreamWidget(QGroupBox):
    """
    Displays the live feed from the camera.
    """

    def __init__(self, port: int = 5000, parent=None):
        super().__init__("Camera", parent)
        self._capture_thread: VideoCaptureThread | None = None
        self._port = port
        self._video_label = QLabel("No Video")
        self._video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._video_label.setMinimumSize(320, 240)
        self._video_label.setStyleSheet(
            "background-color: black;" \
            "color: white;"
        )

        layout = QVBoxLayout()
        stream_toolbar = QHBoxLayout()

        stop_video_btn = QPushButton("Stop")
        stop_video_btn.clicked.connect(self.stop)
        stop_video_btn.setShortcut(QKeySequence("End"))
        stream_toolbar.addWidget(stop_video_btn)

        restart_video_btn = QPushButton("Restart")
        restart_video_btn.clicked.connect(self.restart)
        restart_video_btn.setShortcut(QKeySequence("Ctrl+R"))
        stream_toolbar.addWidget(restart_video_btn)

        layout.addLayout(stream_toolbar)
        layout.addWidget(self._video_label)
        self.setLayout(layout)

    def start(self):
        """
        Begin stream reception.
        """
        if self._capture_thread is not None:
            return

        self._capture_thread = VideoCaptureThread(self._port)
        self._capture_thread.frame_ready.connect(self._on_frame_ready)
        self._capture_thread.connection_failed.connect(self._on_connection_failed)
        self._capture_thread.start()

    def stop(self):
        """
        Stop reception.
        """
        if self._capture_thread is not None:
            try:
                self._capture_thread.frame_ready.disconnect(self._on_frame_ready)
                self._capture_thread.connection_failed.disconnect(self._on_connection_failed)
            except:
                pass

            self._capture_thread.stop()
            self._capture_thread = None
            
        self._video_label.setText("No Video")

    def restart(self):
        """
        Restart video reception
        """
        self.stop()
        self.start()

    @pyqtSlot(np.ndarray)
    def _on_frame_ready(self, frame: np.ndarray):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, channels = rgb_frame.shape
        bytes_per_line = channels * w

        qt_image = QImage(
            rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888
        )
        pixmap = QPixmap.fromImage(qt_image)

        scaled = pixmap.scaled(
            self._video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self._video_label.setPixmap(scaled)

    @pyqtSlot(str)
    def _on_connection_failed(self, message: str):
        self._video_label.setText(message)



if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = VideoStreamWidget(port=5000)
    window.resize(680, 520)
    window.show()
    window.start()

    exit_code = app.exec()
    window.stop()
    sys.exit(exit_code)