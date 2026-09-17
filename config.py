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
# x264 preset. Hardware-tested 2026-09-17: the default ("medium") pushes
# the Pi 4B into real thermal throttling within ~90s of sustained 1080p30
# recording (measured up to 85C, throttled=0xe0008), and once throttled
# the ffmpeg shutdown drain can exceed STOP_TIMEOUT_SECONDS, forcing a
# SIGKILL that leaves the recording without a finalized duration/trailer.
# "veryfast" held steady at 62-70C over a 3-minute recording (no
# throttling) and stopped cleanly in ~4s instead of being killed.
VIDEO_PRESET = "veryfast"

# Recording
VIDEO_EXTENSION = ".MKV"

# How long to wait for ffmpeg to shut down cleanly (flush its encoder
# backlog and finalize the file) before force-killing it. Software H.264
# encoding at this resolution/framerate runs close to the Pi's real-time
# limit, so a clean shutdown can take longer than a few seconds.
STOP_TIMEOUT_SECONDS = 30
