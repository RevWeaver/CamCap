import glob


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
