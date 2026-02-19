import numpy as np
import sys
from PySide6.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QVBoxLayout, QLabel

# setting up application
class AppTest(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('MultiModal Scanner (Name WIP)')

        self.button = QPushButton('click')
        self.resize(500, 500)

        layout = QVBoxLayout()
        layout.addWidget(self.button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

# setting up window to open
app = QApplication(sys.argv)
window = AppTest()
window.show()

sys.exit(app.exec())