import subprocess
import re


def get_camera_device():
    try:
        result = subprocess.run(
            ["v4l2-ctl", "--list-devices"],
            capture_output=True,
            text=True
        )

        lines = result.stdout.splitlines()

        found_camera = False

        for line in lines:
            if "Cam Link" in line:
                found_camera = True

            elif found_camera and "/dev/video" in line:
                return line.strip()

        return None

    except Exception:
        return None


def camera_connected():
    return get_camera_device() is not None
