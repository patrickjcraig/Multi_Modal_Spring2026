import sys, os, math
import pandas as pd # will be saving data as Pandas dataframes
from PySide6.QtWidgets import QApplication, QMainWindow
#from PySide6.QtUiTools import QUiLoader
#from PySide6.QtCore import QFile
from ui_mainwindow import Ui_MainWindow

class AppTest(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle('MultiModal Scanner (Name WIP)')
        #self.setup_connections() # this function will be used to assign values to the widgets

        # old code from using QUiLoader, switching to using pyside6-uic since this makes the widgets work 
        # all of a sudden for some reason

        #base_dir = os.path.dirname(__file__)
        #ui_path = os.path.join(base_dir, "UI_V1.ui") # setting correct filepath
        #ui_file = QFile(ui_path)
        #ui_file.open(QFile.ReadOnly)

        #loader = QUiLoader()
        #loader.load(ui_file, self)
        #print(self.findChildren(object))
        #ui_file.close()

        #self.setCentralWidget(self.ui)
        #self.setup_connections()

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