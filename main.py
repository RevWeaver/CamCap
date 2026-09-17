import os
import signal
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "ui"))

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow


app = QApplication(sys.argv)
window = MainWindow()
window.showFullScreen()

# A plain SIGTERM (e.g. `systemctl stop camcap`, `sudo poweroff`/`reboot`)
# would otherwise kill this process outright without ever running
# closeEvent, leaving an active recording's .tmp file un-finalized on
# disk forever even though ffmpeg itself shuts down cleanly. Just setting
# a signal.signal() handler isn't enough on its own - Python only runs it
# once control returns to the interpreter, which doesn't happen while
# blocked inside Qt's C++ event loop - so a short QTimer hands control
# back regularly to notice the flag and trigger a clean window.close().
shutdown_requested = False


def _request_shutdown(signum, frame):
    global shutdown_requested
    shutdown_requested = True


signal.signal(signal.SIGTERM, _request_shutdown)
signal.signal(signal.SIGINT, _request_shutdown)


def _check_shutdown():
    if shutdown_requested:
        shutdown_poll.stop()
        window.close()


shutdown_poll = QTimer()
shutdown_poll.timeout.connect(_check_shutdown)
shutdown_poll.start(200)

app.exec_()
