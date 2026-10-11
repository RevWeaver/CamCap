import glob
import os


def get_mic_device():
    # ALSA card numbers (hw:4 etc.) depend on enumeration order, like
    # /dev/videoN, so look the receiver up by its stable by-id symlink and
    # address it by card ID instead. Returns e.g. "hw:CARD=Rx,DEV=0", or
    # None if the DJI receiver isn't plugged in.
    matches = glob.glob("/dev/snd/by-id/*Wireless_Mic_Rx*")
    if not matches:
        return None

    # by-id/... -> ../controlC4
    control = os.path.basename(os.path.realpath(matches[0]))
    card_number = control.removeprefix("controlC")

    try:
        with open(f"/proc/asound/card{card_number}/id") as f:
            card_id = f.read().strip()
    except OSError:
        return None

    return f"hw:CARD={card_id},DEV=0"


def mic_connected():
    return get_mic_device() is not None
