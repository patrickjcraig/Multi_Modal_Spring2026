import sys, os, math
import pandas as pd # will be saving data as Pandas dataframes
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog
#from PySide6.QtUiTools import QUiLoader
#from PySide6.QtCore import QFile
from ui_mainwindow import Ui_MainWindow
from open3d_ICP import run_full_registration


class AppTest(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle('MultiModal Scanner (Name WIP)')
        self.setup_connections() # this function will be used to assign values to the widgets

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

    def setup_connections(self):
        self.toolButton.clicked.connect(self.run_scan)
        self.toolButton_2.clicked.connect(self.save_df)

    # functions for running registration and saving as df
    def run_scan(self): # function for running 3D scan from open3d_ICP file
        self.statusbar.showMessage('Currently running ICP...')
        results = run_full_registration()
        self.pcd1 = results['pcd1']
        self.pcd2 = results['pcd2']
        self.icp_result = results['icp']
        
        self.progressBar.setValue(100)
        self.statusbar.showMessage('Finished registration.')

    def save_df(self):
        if not hasattr(self, 'pcd1'):
            self.statusbar.showMessage('No valid data is available.')
            return
        
        # saving pcd1, pcd2, and ICP results into separate Pandas dfs
        pcd1_df = pcd_to_df(self.pcd1)
        pcd2_df = pcd_to_df(self.pcd2)
        icp_tf_df = tf_to_df(self.icp_result) # transformation matrix of registration
        icp_df = reg_to_df(self.icp_result) # metadata of registration

        code_dir = os.path.dirname(os.path.abspath(__file__)) # finding directory for this file
        ws_dir = os.path.dirname(code_dir) # go into Multi_Modal_Spring2026 folder
        base = os.path.join(ws_dir, 'TestData') # go into TestData folder to save the CSVs
        # save CSV files for each df
        pcd1_df.to_csv(os.path.join(base, 'pcd1_raw.csv'), index=False)
        pcd2_df.to_csv(os.path.join(base, 'pcd2_raw.csv'), index=False)
        icp_tf_df.to_csv(os.path.join(base, 'icp_transform.csv'), index=False)
        icp_df.to_csv(os.path.join(base, 'icp_metadata.csv'), index=False)
        # right now, this is just the names of the files, we can change this later to have a current date and time if we want to

        self.statusbar.showMessage('The data has been saved successfully.')

# miscellaneous helper functions to simplify code inside class
def pcd_to_df(pcd): # helper function for converting pcds to df
    points = np.asarray(pcd.points)
    df = pd.DataFrame(points, columns=['X','Y','Z'])
    return df

def tf_to_df(result): # helper function to store the transformation matrix of result data
    return pd.DataFrame(result.transformation, columns=['C1','C2','C3','C4'], index=['R1','R2','R3','R4'])

def reg_to_df(result): # helper function to store the metadata of result data
    return pd.DataFrame({'Fitness':[result.fitness], 'Inlier RMSE':[result.inlier_rmse]})

# start main app
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