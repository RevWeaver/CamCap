# CamCap Configuration

# Storage
MEDIA_PATH = "/media/CAMCAP"
CAMERA_FOLDER = "DCIM/100CAMCAP"
LOG_FOLDER = "LOGS"

# Camera
CAMERA_DEVICE = "/dev/v4l/by-id/usb-Elgato_Cam_Link_4K_00016DFB11000-video-index0"

# Video settings
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FRAME_RATE = 30
VIDEO_BITRATE = "8M"

# Encoder
VIDEO_CODEC = "libx264"

# Recording
VIDEO_EXTENSION = ".MKV"

# How long to wait for ffmpeg to shut down cleanly (flush its encoder
# backlog and finalize the file) before force-killing it. Software H.264
# encoding at this resolution/framerate runs close to the Pi's real-time
# limit, so a clean shutdown can take longer than a few seconds.
STOP_TIMEOUT_SECONDS = 30
