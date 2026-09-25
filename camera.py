import glob
import os


def get_camera_device():
    # /dev/videoN indices are assigned by enumeration order and can shift
    # across reboots or USB resets (the Pi's own bcm2835 codec nodes and
    # the Cam Link both show up as /dev/videoN). The by-id symlink is
    # stable, so use that instead of trusting whatever index the kernel
    # handed out this time.
    matches = glob.glob("/dev/v4l/by-id/*Cam_Link*video-index0")
    return matches[0] if matches else None


def camera_connected():
    return get_camera_device() is not None


def get_camera_usb_speed():
    # USB link speed in Mbit/s (480 = USB 2, 5000+ = USB 3), or None if the
    # camera isn't connected. Uncompressed 1080p30 from the Cam Link needs
    # ~1000 Mbit/s, so on a USB 2 port/hub the preview still limps along
    # but recordings get corrupted/empty frames and fail - hardware-tested
    # 2026-09-25 through a USB 2.0 hub.
    device = get_camera_device()
    if not device:
        return None

    node = os.path.basename(os.path.realpath(device))
    # .../usbN/<port>/<port>:1.0 - the interface's parent is the USB device.
    speed_file = f"/sys/class/video4linux/{node}/device/../speed"

    try:
        with open(speed_file) as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return None
