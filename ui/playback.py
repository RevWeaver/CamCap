import os
import subprocess
import signal

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage


# Recordings are full 1920x1080, but this appliance's job here is
# reviewing footage on a small touchscreen, not pixel-peeping - decode
# at a reduced size to keep playback CPU low, same reasoning as the
# live preview path.
PLAYBACK_WIDTH = 960
PLAYBACK_HEIGHT = 540
PLAYBACK_FRAME_SIZE = PLAYBACK_WIDTH * PLAYBACK_HEIGHT * 3


def list_recordings(camera_folder):
    """Recordings in camera_folder as (path, mtime, size_bytes), newest first."""

    if not os.path.isdir(camera_folder):
        return []

    recordings = []

    for name in os.listdir(camera_folder):

        if not name.endswith(".MKV"):
            continue

        path = os.path.join(camera_folder, name)
        stat = os.stat(path)
        recordings.append((path, stat.st_mtime, stat.st_size))

    recordings.sort(key=lambda r: r[1], reverse=True)
    return recordings


def get_video_info(path):
    """Return (duration_seconds, fps) for a recording, or None on failure."""

    try:

        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "format=duration:stream=r_frame_rate",
                "-of", "default=noprint_wrappers=1:nokey=1",
                path
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=True
        )

        lines = result.stdout.strip().splitlines()
        fps_num, fps_den = lines[0].split("/")
        fps = float(fps_num) / float(fps_den)
        duration = float(lines[1])

        return duration, fps

    except (subprocess.SubprocessError, ValueError, IndexError, OSError):
        return None


class PlaybackWorker(QThread):

    frame_ready = pyqtSignal(QImage)
    position_changed = pyqtSignal(float)
    finished_playback = pyqtSignal()

    def __init__(self, path, fps, start_seconds=0.0):
        super().__init__()
        self.path = path
        self.fps = fps
        self.start_seconds = start_seconds
        self.process = None
        self._running = False
        self._paused = False

    def run(self):

        command = [
            "ffmpeg", "-loglevel", "error",
            "-ss", str(self.start_seconds),
            "-re",
            "-i", self.path,
            "-vf", f"scale={PLAYBACK_WIDTH}:{PLAYBACK_HEIGHT}",
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
        frame_index = 0
        ended_naturally = False

        while True:

            data = self.process.stdout.read(PLAYBACK_FRAME_SIZE)

            if len(data) < PLAYBACK_FRAME_SIZE:
                ended_naturally = self._running
                break

            if not self._running:
                # stop() was called - keep draining so ffmpeg isn't left
                # blocked writing into a pipe nobody's reading, which
                # would otherwise force a hard kill instead of a clean exit.
                continue

            image = QImage(
                data,
                PLAYBACK_WIDTH,
                PLAYBACK_HEIGHT,
                PLAYBACK_WIDTH * 3,
                QImage.Format_RGB888
            )
            self.frame_ready.emit(image.copy())

            frame_index += 1
            self.position_changed.emit(
                self.start_seconds + frame_index / self.fps
            )

        if ended_naturally:
            self.finished_playback.emit()

    def pause(self):

        if self.process and self.process.poll() is None and not self._paused:
            self.process.send_signal(signal.SIGSTOP)
            self._paused = True

    def resume(self):

        if self.process and self.process.poll() is None and self._paused:
            self.process.send_signal(signal.SIGCONT)
            self._paused = False

    def stop(self):

        self._running = False

        if self.process and self.process.poll() is None:

            if self._paused:
                self.process.send_signal(signal.SIGCONT)

            self.process.terminate()

        if not self.wait(5000):
            if self.process and self.process.poll() is None:
                self.process.kill()
            self.wait(3000)
