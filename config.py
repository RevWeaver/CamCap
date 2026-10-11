# CamCap Configuration

# Storage
MEDIA_PATH = "/media/CAMCAP"
CAMERA_FOLDER = "DCIM/100CAMCAP"
LOG_FOLDER = "LOGS"

# Video settings
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FRAME_RATE = 30
VIDEO_BITRATE = "8M"

# Encoder
# Pi 4 hardware H.264 encoder. Software libx264 can't keep up with real
# camera footage here: hardware-tested 2026-09-25 on a detailed scene,
# "veryfast" managed ~11fps and even "ultrafast" only ~24fps (all four
# cores pegged), so recordings dropped most frames and stalled long enough
# to trip the start-up health check. h264_v4l2m2m held ~29fps over a
# 3-minute recording, ~250% CPU (mostly yadif), stopped cleanly in ~3s,
# with no kernel errors - including repeated start/stop cycles. (An older
# bcm2835_codec kernel Oops is why this was previously avoided; it did not
# reproduce. If it ever does, dmesg will show bcm2835_codec/mmal errors.)
VIDEO_CODEC = "h264_v4l2m2m"
# Keyframe every 2s (YouTube's recommendation). The hardware encoder's
# default is every 12 frames, which wastes bitrate on keyframes.
KEYFRAME_INTERVAL = 60

# Audio (DJI Mic Mini receiver over USB)
# The receiver only offers 48kHz, stereo, packed 24-bit (S24_3LE) - ffmpeg's
# ALSA input defaults to 16-bit and fails to open it ("cannot set sample
# format"), so the input codec has to be given explicitly. In mono mode
# with one transmitter, both channels carry the same signal.
MIC_SAMPLE_RATE = 48000
MIC_CHANNELS = 2
MIC_INPUT_CODEC = "pcm_s24le"
AUDIO_CODEC = "aac"
AUDIO_BITRATE = "256k"

# Recording
VIDEO_EXTENSION = ".MKV"

# How long to wait for ffmpeg to shut down cleanly (flush its encoder
# backlog and finalize the file) before force-killing it. Software H.264
# encoding at this resolution/framerate runs close to the Pi's real-time
# limit, so a clean shutdown can take longer than a few seconds.
STOP_TIMEOUT_SECONDS = 30
