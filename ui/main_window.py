import os
import subprocess
import time
from datetime import datetime

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QListWidget,
    QListWidgetItem,
    QSlider,
)

import camera
import config
import playback
from drivemanager import DriveManager
from recorder import Recorder
from status import Status


# Preview quality doesn't matter (combing/low-res is fine, only the
# recorded file needs to be clean) so this path skips yadif and runs at
# a much smaller size than the recording - keeps CPU low enough to leave
# the Pi headroom, and it's not competing with the recorder since only
# one of them ever reads the camera at a time.
PREVIEW_WIDTH = 480
PREVIEW_HEIGHT = 270
PREVIEW_FRAME_SIZE = PREVIEW_WIDTH * PREVIEW_HEIGHT * 3

STORAGE_WATCHDOG_MS = 1000

# The USB capture device occasionally hands a fresh opener corrupted
# buffers right after the previous process (preview or recorder) releases
# it - ffmpeg then stalls forever at frame 0, producing zero output with
# no visible error. This checks that a recording is actually producing
# data shortly after starting, and self-heals with one retry if not.
RECORDING_HEALTH_CHECK_MS = 2000

BUTTON_STYLE = "font-size: 28px; font-weight: bold; color: white;"
RECORD_COLOR = "background-color: #c0392b;"
NEUTRAL_COLOR = "background-color: #444444;"


class PreviewWorker(QThread):

    frame_ready = pyqtSignal(QImage)

    def __init__(self, camera_device):
        super().__init__()
        self.camera_device = camera_device
        self.process = None
        self._running = False

    def run(self):

        command = [
            "ffmpeg",
            "-f", "v4l2",
            "-thread_queue_size", "512",
            "-framerate", str(config.FRAME_RATE),
            "-video_size", f"{config.VIDEO_WIDTH}x{config.VIDEO_HEIGHT}",
            "-i", self.camera_device,
            "-vf", f"scale={PREVIEW_WIDTH}:{PREVIEW_HEIGHT}:flags=fast_bilinear",
            "-pix_fmt", "rgb24",
            "-f", "rawvideo",
            "-"
        ]

        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )

        self._running = True

        while True:

            data = self.process.stdout.read(PREVIEW_FRAME_SIZE)

            if len(data) < PREVIEW_FRAME_SIZE:
                break

            if not self._running:
                # stop() was called - keep draining so ffmpeg's writes
                # don't block (which leaves it holding v4l2 buffers when
                # it eventually gets killed, corrupting the device for
                # whoever opens it next), but stop pushing frames to the UI.
                continue

            image = QImage(
                data,
                PREVIEW_WIDTH,
                PREVIEW_HEIGHT,
                PREVIEW_WIDTH * 3,
                QImage.Format_RGB888
            )

            self.frame_ready.emit(image.copy())

    def stop(self):

        self._running = False

        if self.process and self.process.poll() is None:
            self.process.terminate()

        # Let run() keep draining the pipe until ffmpeg actually exits
        # (it needs a live reader to shut down cleanly and release its
        # v4l2 buffers) instead of racing it with a fixed-timeout kill.
        if not self.wait(5000):
            if self.process and self.process.poll() is None:
                self.process.kill()
            self.wait(3000)


class StopWorker(QThread):
    """Runs Recorder.stop() off the GUI thread - ffmpeg's shutdown drain
    can take several seconds (up to config.STOP_TIMEOUT_SECONDS), and
    doing that on the GUI thread freezes the touch UI for the duration."""

    finished_stopping = pyqtSignal()

    def __init__(self, recorder):
        super().__init__()
        self.recorder = recorder

    def run(self):
        self.recorder.stop()
        self.finished_stopping.emit()


def make_button(text, color_style):
    button = QPushButton(text)
    button.setMinimumHeight(90)
    button.setStyleSheet(BUTTON_STYLE + color_style)
    return button


class MainWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.drive = DriveManager()
        self.recorder = Recorder()
        self.status = Status()
        self.camera_device = None
        self.recording = False
        self.stopping = False
        self.recording_retried = False
        self.preview = None

        self.playback_worker = None
        self.playback_path = None
        self.playback_duration = 0.0
        self.playback_paused = False
        self.seek_pending = False

        self._build_ui()

        self.watchdog_timer = QTimer(self)
        self.watchdog_timer.timeout.connect(self._watchdog_tick)
        self.watchdog_timer.start(STORAGE_WATCHDOG_MS)

        self._startup()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_camera_page())
        self.stack.addWidget(self._build_review_page())
        self.stack.addWidget(self._build_playback_page())

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stack)

        self.setLayout(layout)
        self.setStyleSheet("background-color: #111111;")

    def _build_camera_page(self):

        page = QWidget()

        self.video_label = QLabel("Starting camera...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet(
            "background-color: black; color: white; font-size: 24px;"
        )
        self.video_label.setMinimumSize(320, 180)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: white; font-size: 18px;")

        self.record_button = make_button("RECORD", RECORD_COLOR)
        self.record_button.clicked.connect(self._on_record_button)

        self.review_button = make_button("REVIEW", NEUTRAL_COLOR)
        self.review_button.clicked.connect(self._open_review)

        controls = QHBoxLayout()
        controls.addWidget(self.status_label, stretch=1)
        controls.addWidget(self.review_button, stretch=0)
        controls.addWidget(self.record_button, stretch=0)

        layout = QVBoxLayout()
        layout.addWidget(self.video_label, stretch=1)
        layout.addLayout(controls)
        page.setLayout(layout)

        return page

    def _build_review_page(self):

        page = QWidget()

        self.recording_list = QListWidget()
        self.recording_list.setStyleSheet(
            "font-size: 22px; color: white; background-color: #1a1a1a;"
        )
        self.recording_list.itemClicked.connect(self._on_recording_selected)

        back_button = make_button("BACK", NEUTRAL_COLOR)
        back_button.clicked.connect(self._back_to_camera)

        layout = QVBoxLayout()
        layout.addWidget(make_title_label("Recordings"))
        layout.addWidget(self.recording_list, stretch=1)
        layout.addWidget(back_button)
        page.setLayout(layout)

        return page

    def _build_playback_page(self):

        page = QWidget()

        self.playback_label = QLabel("")
        self.playback_label.setAlignment(Qt.AlignCenter)
        self.playback_label.setStyleSheet("background-color: black;")
        self.playback_label.setMinimumSize(320, 180)

        self.playback_time_label = QLabel("00:00 / 00:00")
        self.playback_time_label.setStyleSheet("color: white; font-size: 18px;")

        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 0)
        self.seek_slider.sliderPressed.connect(self._on_seek_pressed)
        self.seek_slider.sliderReleased.connect(self._on_seek_released)

        self.play_pause_button = make_button("PAUSE", NEUTRAL_COLOR)
        self.play_pause_button.clicked.connect(self._on_play_pause)

        back_button = make_button("BACK", NEUTRAL_COLOR)
        back_button.clicked.connect(self._back_to_review)

        seek_row = QHBoxLayout()
        seek_row.addWidget(self.playback_time_label)
        seek_row.addWidget(self.seek_slider, stretch=1)

        controls = QHBoxLayout()
        controls.addWidget(back_button)
        controls.addStretch(1)
        controls.addWidget(self.play_pause_button)

        layout = QVBoxLayout()
        layout.addWidget(self.playback_label, stretch=1)
        layout.addLayout(seek_row)
        layout.addLayout(controls)
        page.setLayout(layout)

        return page

    # ------------------------------------------------------------------
    # Startup / camera preview (unchanged behavior from before review)
    # ------------------------------------------------------------------

    def _startup(self):

        print("Checking storage...")
        storage_ready = self.drive.mount_drive()

        if storage_ready:
            storage_ready = self.drive.initialize()

        self.status.storage_available = storage_ready

        if storage_ready:
            self.status.free_space = self.drive.get_free_space()

        print("Checking camera...")
        self.camera_device = camera.get_camera_device()
        self.status.camera_connected = self.camera_device is not None

        if self.camera_device:
            self._start_preview()
        else:
            self.video_label.setText("No camera detected")

        self._refresh_status_label()

    def _start_preview(self):

        if self.preview is not None:
            return

        self.preview = PreviewWorker(self.camera_device)
        self.preview.frame_ready.connect(self._on_frame)
        self.preview.start()

    def _stop_preview(self):

        if self.preview is None:
            return

        self.preview.frame_ready.disconnect(self._on_frame)
        self.preview.stop()
        self.preview = None

    def _on_frame(self, image):
        pixmap = QPixmap.fromImage(image).scaled(
            self.video_label.width(),
            self.video_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.video_label.setPixmap(pixmap)

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def _on_record_button(self):

        if self.recording:
            self._begin_stop()
        else:
            self._start_recording()

    def _start_recording(self):

        if not self.camera_device:
            print("Camera not ready")
            return

        if not self.status.storage_available:
            print("Storage not ready")
            return

        # Camera can only have one reader at a time - preview has to
        # step aside before the recorder opens the device.
        self._stop_preview()
        self.video_label.setText("RECORDING")

        filename = self.drive.get_next_filename()

        self.recorder.start(
            self.camera_device,
            filename,
            self.drive.get_log_file()
        )

        self.recording = True
        self.recording_retried = False
        self.status.recording = True
        self.status.current_file = filename
        self.status.recording_start = time.time()

        self.record_button.setText("STOP")
        self.record_button.setStyleSheet(BUTTON_STYLE + NEUTRAL_COLOR)
        self.review_button.setEnabled(False)

        self._refresh_status_label()

        QTimer.singleShot(RECORDING_HEALTH_CHECK_MS, self._check_recording_health)

    def _check_recording_health(self):

        if not self.recording or self.stopping:
            return

        temp_file = self.recorder.temp_file

        if temp_file and os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
            return

        print("Recording produced no data (stalled device handoff)")
        self.recorder.kill_without_finalize()

        if self.recording_retried:
            print("Recording failed to start after retry, giving up")
            self._enter_idle_state()
            return

        print("Retrying recording start...")
        self.recording_retried = True

        filename = self.drive.get_next_filename()

        self.recorder.start(
            self.camera_device,
            filename,
            self.drive.get_log_file()
        )

        self.status.current_file = filename
        self.status.recording_start = time.time()

        QTimer.singleShot(RECORDING_HEALTH_CHECK_MS, self._check_recording_health)

    def _begin_stop(self):

        if not self.recording or self.stopping:
            return

        self.stopping = True

        # ffmpeg's shutdown drain can take several seconds (up to
        # config.STOP_TIMEOUT_SECONDS) - run it off the GUI thread so
        # the touch UI stays responsive instead of freezing on STOP.
        self.record_button.setEnabled(False)
        self.record_button.setText("STOPPING...")

        self._stop_worker = StopWorker(self.recorder)
        self._stop_worker.finished_stopping.connect(self._on_stop_finished)
        self._stop_worker.start()

    def _on_stop_finished(self):

        self.stopping = False
        self.record_button.setEnabled(True)
        self._enter_idle_state()

    def _enter_idle_state(self):

        self.recording = False
        self.status.recording = False
        self.status.current_file = None
        self.status.recording_start = None

        self.record_button.setText("RECORD")
        self.record_button.setStyleSheet(BUTTON_STYLE + RECORD_COLOR)
        self.review_button.setEnabled(True)

        self._refresh_status_label()

        if self.camera_device:
            self._start_preview()

    def _watchdog_tick(self):

        # Storage/recorder health only matters while we're on the camera
        # page - the review/playback screens don't touch the recorder.
        if self.stack.currentIndex() != 0:
            return

        if not self.drive.storage_is_writable():

            self.status.storage_available = False

            if self.recording:
                print("Storage lost! Stopping recording...")
                self._begin_stop()

            if self.drive.mount_drive():
                self.drive.initialize()
                self.status.storage_available = True

        else:
            self.status.storage_available = True
            self.status.free_space = self.drive.get_free_space()

        if self.recording and not self.stopping and not self.recorder.is_recording():
            print("Recorder stopped unexpectedly!")
            self._enter_idle_state()

        self._refresh_status_label()

    def _refresh_status_label(self):

        parts = [
            f"Cam: {'OK' if self.status.camera_connected else 'ERROR'}",
            f"Storage: {'OK' if self.status.storage_available else 'ERROR'}",
            f"Free: {self.status.free_space} GB",
        ]

        if self.recording:
            parts.append(f"REC {self.status.get_recording_time()}")

        self.status_label.setText("   ".join(parts))

    # ------------------------------------------------------------------
    # Review list
    # ------------------------------------------------------------------

    def _open_review(self):

        if self.recording:
            return

        self._stop_preview()

        self.recording_list.clear()

        for path, mtime, size_bytes in playback.list_recordings(self.drive.CAMERA_FOLDER):

            name = path.rsplit("/", 1)[-1]
            when = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            size_mb = size_bytes / (1024 * 1024)

            item = QListWidgetItem(f"{name}    {when}    {size_mb:.0f} MB")
            item.setData(Qt.UserRole, path)
            self.recording_list.addItem(item)

        if self.recording_list.count() == 0:
            self.recording_list.addItem("No recordings yet")

        self.stack.setCurrentIndex(1)

    def _back_to_camera(self):

        self.stack.setCurrentIndex(0)

        if self.camera_device:
            self._start_preview()

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    def _on_recording_selected(self, item):

        path = item.data(Qt.UserRole)

        if not path:
            return

        info = playback.get_video_info(path)

        if info is None:
            print(f"Could not read video info for {path}")
            return

        duration, fps = info

        self.playback_path = path
        self.playback_duration = duration
        self.playback_fps = fps

        self.seek_slider.setRange(0, int(duration))
        self._start_playback(start_seconds=0.0)

        self.stack.setCurrentIndex(2)

    def _start_playback(self, start_seconds):

        if self.playback_worker is not None:
            self.playback_worker.frame_ready.disconnect(self._on_playback_frame)
            self.playback_worker.position_changed.disconnect(self._on_playback_position)
            self.playback_worker.finished_playback.disconnect(self._on_playback_finished)
            self.playback_worker.stop()

        self.playback_worker = playback.PlaybackWorker(
            self.playback_path,
            self.playback_fps,
            start_seconds=start_seconds
        )
        self.playback_worker.frame_ready.connect(self._on_playback_frame)
        self.playback_worker.position_changed.connect(self._on_playback_position)
        self.playback_worker.finished_playback.connect(self._on_playback_finished)
        self.playback_worker.start()

        self.playback_paused = False
        self.play_pause_button.setText("PAUSE")

    def _on_playback_frame(self, image):
        pixmap = QPixmap.fromImage(image).scaled(
            self.playback_label.width(),
            self.playback_label.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.playback_label.setPixmap(pixmap)

    def _on_playback_position(self, seconds):

        if self.seek_pending:
            return

        self.seek_slider.blockSignals(True)
        self.seek_slider.setValue(min(int(seconds), self.seek_slider.maximum()))
        self.seek_slider.blockSignals(False)

        self.playback_time_label.setText(
            f"{_format_time(seconds)} / {_format_time(self.playback_duration)}"
        )

    def _on_playback_finished(self):
        self.playback_paused = True
        self.play_pause_button.setText("REPLAY")

    def _on_play_pause(self):

        if self.playback_worker is None or not self.playback_worker.isRunning():
            self._start_playback(start_seconds=0.0)
            return

        if self.playback_paused:
            self.playback_worker.resume()
            self.playback_paused = False
            self.play_pause_button.setText("PAUSE")
        else:
            self.playback_worker.pause()
            self.playback_paused = True
            self.play_pause_button.setText("PLAY")

    def _on_seek_pressed(self):
        self.seek_pending = True

    def _on_seek_released(self):
        self.seek_pending = False
        self._start_playback(start_seconds=float(self.seek_slider.value()))

    def _back_to_review(self):

        if self.playback_worker is not None:
            self.playback_worker.frame_ready.disconnect(self._on_playback_frame)
            self.playback_worker.position_changed.disconnect(self._on_playback_position)
            self.playback_worker.finished_playback.disconnect(self._on_playback_finished)
            self.playback_worker.stop()
            self.playback_worker = None

        self.playback_path = None
        self.playback_label.clear()

        self._open_review()

    # ------------------------------------------------------------------

    def closeEvent(self, event):
        self._stop_preview()
        if self.playback_worker is not None:
            self.playback_worker.stop()
        if self.recording:
            self.recorder.stop()
        event.accept()


def make_title_label(text):
    label = QLabel(text)
    label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
    return label


def _format_time(seconds):
    seconds = max(0, int(seconds))
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02}:{seconds:02}"
