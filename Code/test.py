import sys
from PySide6.QtWidgets import QApplication
from Utils.opengl_format import configure_opengl
from GUI.main_window import AppTest

# start main app
if __name__ == "__main__":
    configure_opengl()
    app = QApplication(sys.argv)
    window = AppTest()
    window.show()
    sys.exit(app.exec())

# Important Note: Every time a change is made to UI_V1.ui, make sure to rerun the following line in the terminal:
#
# pyside6-uic Code/UI_V1.ui -o Code/ui_mainwindow.py
#
# By adding the folder at the beginning, this puts the newly created Python file in the right folder.