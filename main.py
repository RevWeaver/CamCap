import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "ui"))

from PyQt5.QtWidgets import QApplication
from main_window import MainWindow


app = QApplication(sys.argv)
window = MainWindow()
window.showFullScreen()
app.exec_()
