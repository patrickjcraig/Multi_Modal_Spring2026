from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from Widgets.volume_widget import VolumeRenderWidget

class PointCloudViewerWindow(QMainWindow):
    """
    Standalone window for viewing point clouds and meshes with pyqtgraph.
    Can toggle between point cloud and mesh views using Ctrl+T.
    Both geometries are rendered in the same unified viewer backend.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Point Cloud & Mesh Viewer")
        self.setGeometry(100, 100, 1000, 800)
        
        # Create unified viewer that supports both point clouds and meshes
        self.viewer = VolumeRenderWidget()
        self.setCentralWidget(self.viewer)
        
        # Create status bar with controls info
        status_msg = "Left Mouse: Rotate | Right Mouse: Pan | Scroll: Zoom | Ctrl+T: Toggle View"
        self.statusBar().showMessage(status_msg)
        
        # Enable keyboard focus
        self.setFocusPolicy(Qt.StrongFocus)
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard events."""
        if event.key() == Qt.Key_T and event.modifiers() == Qt.ControlModifier:
            self.viewer.toggle_pointcloud_mesh_view()
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def add_point_cloud(self, name, pcd, color=None):
        """Add a point cloud to the viewer."""
        self.viewer.add_point_cloud(name, pcd, color)
        self.viewer.update()
    
    def add_mesh(self, name, mesh, color=None):
        """Add a mesh to the viewer."""
        self.viewer.add_mesh(name, mesh, color)
        self.viewer.update()
    
    def clear(self):
        """Clear all point clouds and meshes."""
        self.viewer.clear_point_clouds()
        self.viewer.clear_meshes()
        self.viewer.update()