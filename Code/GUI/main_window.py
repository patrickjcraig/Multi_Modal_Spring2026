import os
import copy
import numpy as np
from PySide6.QtWidgets import QMainWindow
from ui_mainwindow import Ui_MainWindow
from Widgets.triangle_widget import TriangleWidget
from Widgets.pointcloud_widget import PointCloudWidget
from GUI.icp_worker import ICPWorkerThread
from Utils.dataframe_utils import pcd_to_df, tf_to_df, reg_to_df
from GUI.workspace_controller import WorkspaceController
from makeGeometry import get_pcd_from_ct_stack

class AppTest(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle('MultiModal Scanner (Name WIP)')
        
        # Initialize worker thread for ICP
        self.icp_thread = None

        # Initialize WorkspaceController to allow for saving and loading workspaces
        self.workspace_controller = WorkspaceController(self)
        
        # Replace the placeholder OpenGL widget with our custom triangle widget
        self._setup_opengl_widget()
        
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

    def _setup_opengl_widget(self):
        """
        Replace the placeholder OpenGL widget with our custom TriangleWidget.
        """
        # Get the geometry of the existing placeholder widget
        geometry = self.openGLWidget.geometry()
        parent = self.openGLWidget.parent()
        
        # Remove the old widget
        self.openGLWidget.setParent(None)
        self.openGLWidget.deleteLater()
        
        # Create and set up the new custom OpenGL widget
        self.openGLWidget = TriangleWidget(parent)
        self.openGLWidget.setGeometry(geometry)
        self.openGLWidget.show()

    def setup_connections(self):
        self.toolButton.clicked.connect(self.run_scan)
        self.toolButton_2.clicked.connect(self.save_df)
        self.toolButton_3.clicked.connect(self.ct_demo)
        self.btn_prev_step.clicked.connect(self._prev_step)
        self.btn_next_step.clicked.connect(self._next_step)
        self.actionSave_Workspace.triggered.connect(self.workspace_controller.save)
        self.actionLoad_Workspace.triggered.connect(self.workspace_controller.load)
        
        # Initialize step tracking
        self.current_step = 0  # 0 = original, 1 = RANSAC, 2 = ICP

    # functions for running registration and saving as df
    def run_scan(self): # function for running 3D scan from open3d_ICP file
        # Disable the button while running
        self.toolButton.setEnabled(False)
        self.progressBar.setValue(0)
        self.statusbar.showMessage('Currently running ICP registration...')
        
        # Clear previous results
        self.label_ransac_fitness.setText("--")
        self.label_ransac_rmse.setText("--")
        self.label_icp_fitness.setText("--")
        self.label_icp_rmse.setText("--")
        
        # Read parameter values from the UI
        voxel_size = self.spinBox_voxel_size.value()
        ransac_dist_mult = self.spinBox_ransac_dist.value()
        ransac_max_iter = self.spinBox_ransac_max_iter.value()
        ransac_validation = self.spinBox_ransac_validation.value()
        icp_dist_mult = self.spinBox_icp_dist.value()
        
        # Create and start the worker thread with parameters
        self.icp_thread = ICPWorkerThread(
            voxel_size=voxel_size,
            ransac_dist_mult=ransac_dist_mult,
            ransac_max_iter=ransac_max_iter,
            ransac_validation=ransac_validation,
            icp_dist_mult=icp_dist_mult
        )
        self.icp_thread.finished.connect(self._on_registration_complete)
        self.icp_thread.error.connect(self._on_registration_error)
        self.icp_thread.start()
    
    def _on_registration_complete(self, results):
        """Called when ICP registration is complete."""
        # Store the results
        self.pcd1 = results['pcd1']
        self.pcd2 = results['pcd2']
        self.ransac_result = results['ransac']
        self.icp_result = results['icp']
        
        # Update the results labels
        self._update_results_display()
        
        # Display the registered point clouds in the OpenGL viewer (start at final ICP result)
        self.current_step = 2
        self._display_registration_results()
        
        # Enable navigation buttons
        self.btn_prev_step.setEnabled(True)
        self.btn_next_step.setEnabled(False)  # Already at last step
        
        # Update UI
        self.progressBar.setValue(100)
        self.statusbar.showMessage('Registration complete! Fitness: {:.6f}, RMSE: {:.6f}'.format(
            self.icp_result.fitness, self.icp_result.inlier_rmse))
        
        # Re-enable the button
        self.toolButton.setEnabled(True)
    
    def _update_results_display(self):
        """Update the results labels with RANSAC and ICP statistics."""
        # Update RANSAC results
        self.label_ransac_fitness.setText(f"{self.ransac_result.fitness:.6f}")
        self.label_ransac_rmse.setText(f"{self.ransac_result.inlier_rmse:.6f}")
        
        # Update ICP results
        self.label_icp_fitness.setText(f"{self.icp_result.fitness:.6f}")
        self.label_icp_rmse.setText(f"{self.icp_result.inlier_rmse:.6f}")
    
    def _on_registration_error(self, error_msg):
        """Called if an error occurs during registration."""
        self.statusbar.showMessage(f'Error during registration: {error_msg}')
        self.toolButton.setEnabled(True)
    
    def _display_registration_results(self):
        """Display the registration results in the OpenGL viewer based on current step."""
        # Replace the triangle widget with a point cloud viewer if needed
        if not isinstance(self.openGLWidget, PointCloudWidget):
            geometry = self.openGLWidget.geometry()
            parent = self.openGLWidget.parent()
            
            # Remove the old widget
            self.openGLWidget.setParent(None)
            self.openGLWidget.deleteLater()
            
            # Create the new point cloud widget
            self.openGLWidget = PointCloudWidget(parent)
            self.openGLWidget.setGeometry(geometry)
            self.openGLWidget.show()
        else:
            # Clear existing point clouds
            self.openGLWidget.point_clouds.clear()
        
        # Prepare point clouds with colors
        import copy
        source_temp = copy.deepcopy(self.pcd1)
        target_temp = copy.deepcopy(self.pcd2)
        
        source_temp.paint_uniform_color([1.0, 0.706, 0.0])  # Orange
        target_temp.paint_uniform_color([0.0, 0.651, 0.929])  # Blue
        
        # Apply transformation based on current step
        if self.current_step == 0:
            # Step 0: Original offset point clouds (no transformation)
            self.label_step_info.setText("Step 1/3: Original Point Clouds")
        elif self.current_step == 1:
            # Step 1: RANSAC alignment
            source_temp.transform(self.ransac_result.transformation)
            self.label_step_info.setText("Step 2/3: RANSAC Alignment")
        elif self.current_step == 2:
            # Step 2: Final ICP alignment
            source_temp.transform(self.icp_result.transformation)
            self.label_step_info.setText("Step 3/3: ICP Refinement")
        
        # Add to the viewer
        self.openGLWidget.add_point_cloud("Source", source_temp)
        self.openGLWidget.add_point_cloud("Target", target_temp)
        self.openGLWidget.update()
    
    def _prev_step(self):
        """Navigate to the previous registration step."""
        if self.current_step > 0:
            self.current_step -= 1
            self._display_registration_results()
            
            # Update button states
            self.btn_next_step.setEnabled(True)
            if self.current_step == 0:
                self.btn_prev_step.setEnabled(False)
    
    def _next_step(self):
        """Navigate to the next registration step."""
        if self.current_step < 2:
            self.current_step += 1
            self._display_registration_results()
            
            # Update button states
            self.btn_prev_step.setEnabled(True)
            if self.current_step == 2:
                self.btn_next_step.setEnabled(False)

    def save_df(self):
        if not hasattr(self, 'pcd1'):
            self.statusbar.showMessage('No valid data is available.')
            return
        
        # saving pcd1, pcd2, ICP and RANSAC results into separate Pandas dfs
        pcd1_df = pcd_to_df(self.pcd1)
        pcd2_df = pcd_to_df(self.pcd2)
        icp_tf_df = tf_to_df(self.icp_result) # transformation matrix of ICP registration
        icp_df = reg_to_df(self.icp_result) # metadata of ICP registration
        ransac_tf_df = tf_to_df(self.ransac_result) # transformation matrix of RANSAC
        ransac_df = reg_to_df(self.ransac_result) # metadata of RANSAC

        code_dir = os.path.dirname(os.path.abspath(__file__)) # finding directory for this file
        ws_dir = os.path.dirname(code_dir) # go into Multi_Modal_Spring2026 folder
        base = os.path.join(ws_dir, 'TestData') # go into TestData folder to save the CSVs
        
        # Create TestData directory if it doesn't exist
        os.makedirs(base, exist_ok=True)
        
        # save CSV files for each df
        pcd1_df.to_csv(os.path.join(base, 'pcd1_raw.csv'), index=False)
        pcd2_df.to_csv(os.path.join(base, 'pcd2_raw.csv'), index=False)
        icp_tf_df.to_csv(os.path.join(base, 'icp_transform.csv'), index=False)
        icp_df.to_csv(os.path.join(base, 'icp_metadata.csv'), index=False)
        ransac_tf_df.to_csv(os.path.join(base, 'ransac_transform.csv'), index=False)
        ransac_df.to_csv(os.path.join(base, 'ransac_metadata.csv'), index=False)
        # right now, this is just the names of the files, we can change this later to have a current date and time if we want to

        self.statusbar.showMessage('The data has been saved successfully.')

    def scan_reset(self): # function that resets scanning data (mainly for when loading a workspace from a .pkl file)
        self.pcd1 = None
        self.pcd2 = None
        self.ransac_result = None
        self.icp_result = None
        self.current_step = 0

        self._setup_opengl_widget()

        self.btn_prev_step.setEnabled(False)
        self.btn_next_step.setEnabled(False)

    def ct_demo(self): # temporary function for a button to show pointcloud in software, will be replaced eventually once file importing is done
        """
        Generates the demo CT point cloud and displays it in the OpenGL viewer.
        """

        try:
            self.statusbar.showMessage("Generating demo CT point cloud...")
            # this is where reconstruction_v1 is located, adjust if needed
            demo_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '120kv_FDK'))

            # Call the main function logic in the module
            pcd, mesh, level = get_pcd_from_ct_stack(
                folder_path=demo_folder,    # None will trigger the default in your function
                downsample_zyx=4,
                crop_zyx=(256, 256, 256),
                level=None,
                n_points=5000,
            )

            print("MC level:", level)
            print("PCD points:", np.asarray(pcd.points).shape[0])
            print("Mesh verts:", np.asarray(mesh.vertices).shape[0])

            # Reset previous scan & OpenGL widget
            self.scan_reset()

            # Store internally if needed
            self.pcd1 = pcd
            self.mesh1 = mesh

            # Replace the TriangleWidget with your point cloud widget
            geometry_widget_geometry = self.openGLWidget.geometry()
            parent = self.openGLWidget.parent()

            self.openGLWidget.setParent(None)
            self.openGLWidget.deleteLater()

            # Use your existing PointCloudWidget
            self.openGLWidget = PointCloudWidget(parent)
            self.openGLWidget.setGeometry(geometry_widget_geometry)
            self.openGLWidget.show()

            # Add the point cloud(s)
            self.openGLWidget.add_point_cloud("Demo CT", pcd)
            self.openGLWidget.update()

            self.statusbar.showMessage("Demo CT point cloud generated and displayed.")

        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", str(e))
            self.statusbar.showMessage("Error generating demo CT point cloud.")