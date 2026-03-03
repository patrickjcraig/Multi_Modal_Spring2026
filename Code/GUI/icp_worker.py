from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QMainWindow
from open3d_ICP import run_full_registration
from Widgets.pointcloud_widget import PointCloudWidget

class ICPWorkerThread(QThread):
    """
    Worker thread for running ICP registration without blocking the UI.
    """
    finished = Signal(dict)  # Signal emitted when registration is complete
    error = Signal(str)       # Signal emitted if an error occurs
    
    def __init__(self, voxel_size=2.0, ransac_dist_mult=1.5, ransac_max_iter=100000,
                 ransac_validation=1000, icp_dist_mult=0.4):
        super().__init__()
        self.voxel_size = voxel_size
        self.ransac_dist_mult = ransac_dist_mult
        self.ransac_max_iter = ransac_max_iter
        self.ransac_validation = ransac_validation
        self.icp_dist_mult = icp_dist_mult
    
    def run(self):
        """Run the ICP registration in a background thread."""
        try:
            results = run_full_registration(
                voxel_size=self.voxel_size,
                ransac_dist_multiplier=self.ransac_dist_mult,
                ransac_max_iter=self.ransac_max_iter,
                ransac_validation=self.ransac_validation,
                icp_dist_multiplier=self.icp_dist_mult
            )
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class PointCloudViewerWindow(QMainWindow):
    """
    Standalone window for viewing point clouds with OpenGL.
    Can be used independently or integrated into the main GUI.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Point Cloud Viewer - OpenGL")
        self.setGeometry(100, 100, 1000, 800)
        
        # Create the OpenGL widget
        self.viewer = PointCloudWidget()
        self.setCentralWidget(self.viewer)
        
        # Create status bar with controls info
        self.statusBar().showMessage("Left Mouse: Rotate | Right Mouse: Pan | Scroll: Zoom")
    
    def add_point_cloud(self, name, pcd, color=None):
        """Add a point cloud to the viewer."""
        self.viewer.add_point_cloud(name, pcd, color)
        # Don't setup geometry here - let it happen during first paint call
        self.viewer.update()
    
    def clear(self):
        """Clear all point clouds."""
        self.viewer.clear_point_clouds()
        self.viewer.update()