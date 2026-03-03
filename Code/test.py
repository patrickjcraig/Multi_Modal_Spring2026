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
# pyside6-uic Code/UI_V1.ui -o ui_mainwindow.py
#
# This is assuming you are working in the directory folder for Multi_Modal_Spring2026. Then afterward, since the 
# file will be made in that directory, move the newly created file into the Code folder so it is in the same
# directory as the main Python file that will run this code.
# Addendum: When replacing the ui_mainwindow.py file, for some reason it adds 'Code.' to the import at the beginning
# of this file. Make sure to fix that back to the way it was before (without Code. at the beginning) for this to run.