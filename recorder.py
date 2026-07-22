import subprocess
import signal
import config


class Recorder:

    def __init__(self):
        self.process = None
        self.current_file = None

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
            "h264_v4l2m2m",
            "-b:v",
            config.VIDEO_BITRATE,
            output_file
        ]

        self.current_file = output_file

        self.process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
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

        print("Recording stopped")

    def is_recording(self):

        return self.process is not None
