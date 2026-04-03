from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent

from Widgets.pointcloud_widget import PointCloudWidget


class ScanViewerTab(QWidget):
    """Small container for one scan/result viewer with point cloud and mesh display.
    
    Supports toggling between point cloud and mesh views using Ctrl+T.
    Both geometries are rendered in the same OpenGL context with opacity control.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.info_label = QLabel("No scan loaded")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # Create unified viewer that supports both point clouds and meshes
        self.viewer = PointCloudWidget(self)
        layout.addWidget(self.viewer, 1)
        
        # Enable focus for keyboard events
        self.setFocusPolicy(Qt.StrongFocus)

    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard events for toggling views."""
        if event.key() == Qt.Key_T and event.modifiers() == Qt.ControlModifier:
            self.viewer.toggle_pointcloud_mesh_view()
            event.accept()
        else:
            super().keyPressEvent(event)

    def set_info_text(self, text):
        self.info_label.setText(text)

    def set_point_clouds(self, clouds):
        """Replace the displayed point clouds with ``clouds``.

        ``clouds`` is an iterable of ``(name, pcd, color)`` tuples.
        """
        self.viewer.clear_point_clouds()
        for name, pcd, color in clouds:
            self.viewer.add_point_cloud(name, pcd, color=color)
        self.viewer.update()
    
    def set_mesh(self, name, mesh, color=None):
        """Add a mesh to the viewer.
        
        Args:
            name: Identifier for the mesh
            mesh: open3d.geometry.TriangleMesh
            color: Optional RGB color tuple (0-1 range)
        """
        self.viewer.add_mesh(name, mesh, color)
        self.viewer.update()

    def set_meshes(self, meshes):
        """Replace displayed meshes with ``meshes``.

        ``meshes`` is an iterable of ``(name, mesh, color)`` tuples.
        """
        self.viewer.clear_meshes()
        for name, mesh, color in meshes:
            self.viewer.add_mesh(name, mesh, color=color)
        self.viewer.update()
    
    def clear_meshes(self):
        """Clear all meshes from the viewer."""
        self.viewer.clear_meshes()
        self.viewer.update()
