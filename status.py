import time
import os
class Status:

    def __init__(self):
        self.camera_connected = False
        self.storage_available = False
        self.recording = False
        self.free_space = 0
        self.current_file = None
        self.recording_start = None

    def get_recording_time(self):

        if not self.recording or not self.recording_start:
            return "00:00:00"

        elapsed = int(time.time() - self.recording_start)

        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        seconds = elapsed % 60

        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def display(self):

        os.system("clear")

        print("======================")
        print("        CamCap")
        print("======================")

        print(f"Camera:    {'OK' if self.camera_connected else 'ERROR'}")
        print(f"Storage:   {'OK' if self.storage_available else 'ERROR'}")
        print(f"Free:      {self.free_space} GB")

        if self.recording:
            print("State:     RECORDING")
            print(f"Time:      {self.get_recording_time()}")
        else:
            print("State:     READY")

        if self.current_file:
            print(f"File:      {self.current_file}")

        print("======================")
