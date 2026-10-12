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

    def start(self, camera_device, output_file, log_file, mic_device=None):

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
        ]

        # Mic is optional - no receiver plugged in just means a silent
        # (video-only) recording, not a failed one. If the receiver drops
        # out mid-recording, ffmpeg logs "ALSA read error: No such device"
        # and carries on recording video (hardware-tested 2026-10-11);
        # audio does not resume if it's plugged back in.
        if mic_device:
            command += [
                "-f",
                "alsa",
                "-thread_queue_size",
                "1024",
                "-c:a",
                config.MIC_INPUT_CODEC,
                "-channels",
                str(config.MIC_CHANNELS),
                "-sample_rate",
                str(config.MIC_SAMPLE_RATE),
                "-i",
                mic_device,
                "-map",
                "0:v",
                "-map",
                "1:a",
                "-c:a",
                config.AUDIO_CODEC,
                "-b:a",
                config.AUDIO_BITRATE,
            ]

        command += [
            "-vf",
            "yadif",
            "-pix_fmt",
            "yuv420p",
            "-c:v",
            config.VIDEO_CODEC,
            "-g",
            str(config.KEYFRAME_INTERVAL),
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
        print("Recording started" + (f" with mic {mic_device}" if mic_device else " (no mic)"))
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

        saved = False

        # ffmpeg exiting only means the data reached Linux's page cache -
        # the kernel writes it to the SSD over the next ~30s. Unplugging
        # the drive in that window lost the video of a finished take
        # (2026-10-11), so force it onto the disk before calling it saved.
        try:
            if self.temp_file and os.path.exists(self.temp_file):
                flush_start = time.time()
                fsync_path(self.temp_file)
                os.rename(
                    self.temp_file,
                    self.current_file
                )
                fsync_path(os.path.dirname(self.current_file))
                print(f"Recording saved to disk (flush took {time.time() - flush_start:.1f}s)")
                saved = True
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

        return saved

    def is_recording(self):

        if self.process is None:
            return False

        return self.process.poll() is None

    def kill_without_finalize(self):
        """Force-kill without renaming the temp file - for when the
        encoder never produced usable output (e.g. a stalled device
        handoff right after the camera changes hands) and the temp file
        isn't a real recording worth keeping."""

        if self.process and self.process.poll() is None:
            self.process.kill()
            self.process.wait()

        if self.temp_file and os.path.exists(self.temp_file):
            os.remove(self.temp_file)

        self.process = None
        self.temp_file = None
        self.current_file = None

        if self.log:
            self.log.close()
            self.log = None


def fsync_path(path):
    """Block until path's data (or, for a directory, its entries - e.g. a
    rename) is physically on the drive. Raises OSError if the drive is gone."""

    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
