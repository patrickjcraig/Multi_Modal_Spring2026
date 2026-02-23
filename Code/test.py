import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
import os

class AppTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('MultiModal Scanner (Name WIP)')

        #ui_path = os.path.join(os.path.dirname(__file__), "..", "UI_RoughDraft", "UI_V1.ui") # Path to GUI file .ui
        ui_path = "UI_V1.ui"
        ui_file = QFile(ui_path)
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.ui = loader.load(ui_file, self)
        ui_file.close()

        self.setCentralWidget(self.ui)

app = QApplication(sys.argv)
window = AppTest()
window.show()
sys.exit(app.exec())
