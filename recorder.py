import subprocess
import signal
import config
import os


class Recorder:

    def __init__(self):
        self.process = None
        self.current_file = None
        self.log = None

    def start(self, camera_device, output_file):

        if self.process:
            print("Already recording")
            return

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
            "-pix_fmt",
            "yuv420p",
            "-c:v",
            config.VIDEO_CODEC,
            "-b:v",
            config.VIDEO_BITRATE,
            output_file
        ]

        self.current_file = output_file

        log_file = os.path.join(
            config.MEDIA_PATH,
            "LOGS",
            "ffmpeg.log"
        )

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
        self.process.wait()

        self.process = None

        if self.log:
            self.log.close()
            self.log = None

        print("Recording stopped")

    def is_recording(self):

        return self.process is not None
