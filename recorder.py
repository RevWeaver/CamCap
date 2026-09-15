import subprocess
import signal
import time
import config
import os


class Recorder:

    def __init__(self):
        self.process = None
        self.current_file = None
        self.log = None
        self.temp_file = None

    def start(self, camera_device, output_file, log_file):

        if self.process and self.process.poll() is None:
            print("Already recording")
            return

        if self.log:
            self.log.close()
            self.log = None

        self.process = None
        self.current_file = output_file

        temp_file = output_file + ".tmp"
        self.temp_file = temp_file

        command = [
            "ffmpeg",
            "-f",
            "v4l2",
            "-thread_queue_size",
            "512",
            "-framerate",
            str(config.FRAME_RATE),
            "-video_size",
            f"{config.VIDEO_WIDTH}x{config.VIDEO_HEIGHT}",
            "-i",
            camera_device,
            "-vf",
            "yadif",
            "-pix_fmt",
            "yuv420p",
            "-c:v",
            config.VIDEO_CODEC,
            "-b:v",
            config.VIDEO_BITRATE,
            "-f",
            "matroska",
            temp_file
        ]

        self.log = open(log_file, "a")

        self.process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=self.log,
            stderr=self.log

        )
        print("Recording started")
        print(output_file)

    def stop(self):

        if not self.process:
            print("Not recording")
            return

        self.process.send_signal(signal.SIGINT)

        stop_started = time.time()

        try:
            self.process.wait(timeout=config.STOP_TIMEOUT_SECONDS)
            print(f"FFmpeg stopped cleanly in {time.time() - stop_started:.1f}s")

        except subprocess.TimeoutExpired:
            print(
                f"Recorder did not stop cleanly within "
                f"{config.STOP_TIMEOUT_SECONDS}s, killing FFmpeg"
            )
            self.process.kill()
            self.process.wait()

        self.process = None

        try:
            if self.temp_file and os.path.exists(self.temp_file):
                os.rename(
                    self.temp_file,
                    self.current_file
                )
                print("Recording stopped")
            else:
                print("Recording stopped (no temp file to finalize)")

        except OSError as error:
            print(f"Could not finalize recording, storage may be gone: {error}")

        self.temp_file = None

        try:
            if self.log:
                self.log.close()

        except OSError as error:
            print(f"Could not close ffmpeg log cleanly: {error}")

        self.log = None

    def is_recording(self):

        if self.process is None:
            return False

        return self.process.poll() is None
