import config
import os
import shutil

MEDIA_PATH = config.MEDIA_PATH

CAMERA_FOLDER = os.path.join(
    MEDIA_PATH,
    config.CAMERA_FOLDER
)

LOG_FOLDER = os.path.join(
    MEDIA_PATH,
    config.LOG_FOLDER
)

def initialize_storage():

    if not os.path.exists(MEDIA_PATH):
        print("No CAMCAP media detected")
        return False

    print("CAMCAP media detected")

    create_folders()

    return True


def create_folders():
    folders = [
        CAMERA_FOLDER,
        LOG_FOLDER
    ]

    for folder in folders:
        os.makedirs(folder, exist_ok=True)

    print("Camera folders ready")


def get_free_space():
    usage = shutil.disk_usage(MEDIA_PATH)

    free_gb = usage.free / (1024 ** 3)

    return round(free_gb, 1)

def get_next_filename():
    number = 1

    while True:
        filename = f"C{number:04d}{config.VIDEO_EXTENSION}"

        path = os.path.join(
            CAMERA_FOLDER,
            filename
        )

        if not os.path.exists(path):
            return path

        number += 1

def storage_is_writable():

    if not os.path.ismount(MEDIA_PATH):
        return False

    try:
        test_file = os.path.join(MEDIA_PATH, ".camcap_test")

        with open(test_file, "w"):
            pass

        os.remove(test_file)

        return True

    except OSError:
        return False
