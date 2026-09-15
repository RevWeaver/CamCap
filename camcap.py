import sys
import select
import camera
import time
from status import Status
from recorder import Recorder
from drivemanager import DriveManager


class CamCap:

    def __init__(self):
        self.storage_ready = False
        self.camera_ready = False
        self.camera_device = None

        self.drive = DriveManager()

        self.recorder = Recorder()
        self.recording = False

        self.status = Status()

    def initialize(self):

        print("CamCap starting...")

        print("Checking storage...")

        self.storage_ready = self.drive.mount_drive()

        if self.storage_ready:
            self.storage_ready = self.drive.initialize()

        self.status.storage_available = self.storage_ready

        if self.storage_ready:
            self.status.free_space = self.drive.get_free_space()

        print("Checking camera...")
        self.camera_device = camera.get_camera_device()

        if self.camera_device:
            self.camera_ready = True
            self.status.camera_connected = True
            print(f"Camera detected: {self.camera_device}")
        else:
            print("Camera not detected")

        return self.storage_ready and self.camera_ready

    def run(self):

        if not self.initialize():
            print("Startup failed")
            return

        print("CamCap ready")

        while True:

            # Storage watchdog
            if not self.drive.storage_is_writable():

                self.status.storage_available = False

                if self.recording:
                    print("\nStorage lost! Stopping recording...")
                    self.stop_recording()

                if self.drive.mount_drive():
                    self.drive.initialize()

                self.status.display()
                time.sleep(1)
                continue

            self.status.storage_available = True

            # Recorder watchdog
            if self.recording and not self.recorder.is_recording():

                print("\nRecorder stopped unexpectedly!")

                self.recording = False
                self.status.recording = False
                self.status.recording_start = None
                self.status.current_file = None

            self.status.display()

            print(
                "\nCommand (r=record, s=stop, q=quit): ",
                end="",
                flush=True
            )

            ready, _, _ = select.select(
                [sys.stdin],
                [],
                [],
                1
            )

            if ready:
                command = sys.stdin.readline().strip()

                if command == "r":
                    self.start_recording()

                elif command == "s":
                    self.stop_recording()

                elif command == "q":
                    print("Shutting down CamCap")
                    self.stop_recording()
                    break

                else:
                    print("Unknown command")

            time.sleep(0.1)

    def start_recording(self):

        if not self.camera_ready:
            print("Camera not ready")
            return

        if self.recording:
            print("Already recording")
            return

        filename = self.drive.get_next_filename()

        print("Starting recording:")
        print(filename)

        self.recorder.start(
            self.camera_device,
            filename,
            self.drive.get_log_file()
        )

        self.recording = True
        self.status.recording = True
        self.status.current_file = filename
        self.status.recording_start = time.time()

    def stop_recording(self):

        if not self.recording:
            print("Not recording")
            return

        self.recorder.stop()

        self.recording = False
        self.status.recording = False
        self.status.current_file = None
        self.status.recording_start = None
