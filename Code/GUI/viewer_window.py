from PySide6.QtWidgets import QMainWindow
from Widgets.pointcloud_widget import PointCloudWidget

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
        self.statusBar().showMessage("Left Mouse: Rotate | Right Mouse: Move Rotation Origin | Scroll: Zoom")
    
    def add_point_cloud(self, name, pcd, color=None):
        """Add a point cloud to the viewer."""
        self.viewer.add_point_cloud(name, pcd, color)
        # Don't setup geometry here - let it happen during first paint call
        self.viewer.update()
    
    def clear(self):
        """Clear all point clouds."""
        self.viewer.clear_point_clouds()
        self.viewer.update()