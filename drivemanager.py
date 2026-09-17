import os
import subprocess
import shutil


class DriveManager:

    MOUNT_POINT = "/media/CAMCAP"
    ROOT_FOLDER = os.path.join(MOUNT_POINT, "CamCap")
    CAMERA_FOLDER = os.path.join(ROOT_FOLDER, "DCIM", "100CAMCAP")
    LOG_FOLDER = os.path.join(ROOT_FOLDER, "LOGS")
    CONFIG_FOLDER = os.path.join(ROOT_FOLDER, "CONFIG")
    MARKER_FILE = os.path.join(ROOT_FOLDER, ".camcap_drive")

    # ffmpeg's own log deliberately does NOT live on the removable drive:
    # a disconnect is exactly the failure this log is most needed to
    # diagnose, and a vanished drive would take the log with it.
    LOCAL_LOG_FOLDER = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "logs"
    )

    def __init__(self):
        self.ready = False

    def is_mounted(self):
        return os.path.ismount(self.MOUNT_POINT)

    def initialize(self):

        if not self.is_mounted():
            print("No recording drive mounted.")
            return False

        try:

            os.makedirs(self.CAMERA_FOLDER, exist_ok=True)
            os.makedirs(self.LOG_FOLDER, exist_ok=True)
            os.makedirs(self.CONFIG_FOLDER, exist_ok=True)

            if not os.path.exists(self.MARKER_FILE):
                with open(self.MARKER_FILE, "w") as marker:
                    marker.write("CamCap Drive\n")

        except OSError as e:
            print(f"Failed to prepare drive: {e}")
            return False

        self.ready = True
        return True

    def get_free_space(self):
        total, used, free = shutil.disk_usage(self.MOUNT_POINT)
        return round(free / (1024 ** 3), 1)

    def storage_is_writable(self):

        if not self.is_mounted():
            return False

        try:
            test_file = os.path.join(self.MOUNT_POINT, ".write_test")

            with open(test_file, "w"):
                pass

            os.remove(test_file)
            return True

        except Exception:
            return False

    def get_next_filename(self):

        number = 1

        while True:

            filename = f"C{number:04d}.MKV"

            path = os.path.join(
                self.CAMERA_FOLDER,
                filename
            )

            if not os.path.exists(path) and not os.path.exists(path + ".tmp"):
                return path

            number += 1

    def get_log_file(self):

        os.makedirs(self.LOCAL_LOG_FOLDER, exist_ok=True)

        return os.path.join(
            self.LOCAL_LOG_FOLDER,
            "ffmpeg.log"
        )

    def detect_drive(self):

        try:

            result = subprocess.run(
                [
                    "lsblk",
                    "-pn",
                    "-o",
                    "NAME,TRAN"
                ],
                capture_output=True,
                text=True,
                check=True
            )

        except subprocess.CalledProcessError:
            return None

        usb_drive = None

        for line in result.stdout.splitlines():

            parts = line.split()

            if len(parts) == 2:

                device, transport = parts

                if transport == "usb":
                    usb_drive = device

        if not usb_drive:
            return None

        try:

            result = subprocess.run(
                [
                    "lsblk",
                    "-pn",
                    "-o",
                    "NAME",
                    usb_drive
                ],
                capture_output=True,
                text=True,
                check=True
            )

        except subprocess.CalledProcessError:
            return None

        for line in result.stdout.splitlines():

            device = line.strip()

            device = device.replace("└─", "")
            device = device.replace("├─", "")

            if device != usb_drive:
                return device

        return None

    def mount_drive(self):

        if self.is_mounted():

            if self.storage_is_writable():
                return True

            # The mount table still shows something at MOUNT_POINT, but it
            # doesn't actually work (e.g. the drive was unplugged without a
            # clean unmount). Clear the stale mount before trying to mount
            # whatever drive is actually connected now.
            print("Existing mount is stale, clearing it...")

            try:

                subprocess.run(
                    [
                        "sudo",
                        "umount",
                        self.MOUNT_POINT
                    ],
                    check=True
                )

            except subprocess.CalledProcessError:
                print("Failed to clear stale mount")
                return False

        device = self.detect_drive()

        if not device:
            print("No USB drive detected")
            return False

        os.makedirs(self.MOUNT_POINT, exist_ok=True)

        try:

            subprocess.run(
                [
                    "sudo",
                    "mount",
                    device,
                    self.MOUNT_POINT
                ],
                check=True
            )

        except subprocess.CalledProcessError:
            print("Failed to mount drive")
            return False

        if self.storage_is_writable():
            return True

        # A drive formatted elsewhere (or freshly mkfs'd) is typically
        # owned by root, unlike an SD card that just works in a camera.
        # Fix ownership once instead of requiring manual setup per drive.
        print("Drive mounted but not writable, fixing ownership...")

        try:

            subprocess.run(
                [
                    "sudo",
                    "chown",
                    f"{os.getuid()}:{os.getgid()}",
                    self.MOUNT_POINT
                ],
                check=True
            )

        except subprocess.CalledProcessError:
            print("Failed to fix drive ownership")
            subprocess.run(["sudo", "umount", self.MOUNT_POINT])
            return False

        if self.storage_is_writable():
            return True

        print("Drive still not writable after fixing ownership")
        subprocess.run(["sudo", "umount", self.MOUNT_POINT])
        return False
