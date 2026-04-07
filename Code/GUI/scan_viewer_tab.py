from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtGui import QKeyEvent

from makeGeometry import load_ct_volume_preview
from Widgets.pointcloud_widget import PointCloudWidget
from Widgets.volume_widget import VolumeRenderWidget


class VolumeLoadWorker(QThread):
    finished = Signal(object, dict)
    error = Signal(str)

    def __init__(self, volume_source, downsample_zyx, parent=None):
        super().__init__(parent)
        self.volume_source = volume_source
        self.downsample_zyx = downsample_zyx

    def run(self):
        try:
            volume, metadata = load_ct_volume_preview(
                folder_path=self.volume_source.folder_path,
                downsample_zyx=self.downsample_zyx,
                crop_zyx=self.volume_source.crop_zyx,
                max_preview_voxels=self.volume_source.max_preview_voxels,
            )
            self.finished.emit(volume, metadata)
        except Exception as exc:
            self.error.emit(str(exc))


class ScanViewerTab(QWidget):
    """Small container for one scan/result viewer with point cloud and mesh display.
    
    Supports toggling between geometry and lazy 3D volume views using Ctrl+T.
    Point cloud and mesh views can still be toggled inside geometry mode with Ctrl+M.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.volume_source = None
        self._volume_loaded = False
        self._volume_worker = None
        self._last_volume_shape_xyz = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.info_label = QLabel("No scan loaded")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)

        self.btn_toggle_volume = QPushButton("Show 3D Volume")
        self.btn_toggle_volume.setEnabled(False)
        self.btn_toggle_volume.setToolTip("Toggle point cloud/mesh and lazy 3D volume preview (Ctrl+T)")
        controls.addWidget(self.btn_toggle_volume)

        self.btn_toggle_mesh = QPushButton("Toggle Point Cloud / Mesh")
        self.btn_toggle_mesh.setToolTip("Toggle point cloud and mesh inside the geometry view (Ctrl+M)")
        controls.addWidget(self.btn_toggle_mesh)

        controls.addWidget(QLabel("Volume downsample"))
        self.spin_volume_downsample = QSpinBox()
        self.spin_volume_downsample.setRange(1, 128)
        self.spin_volume_downsample.setValue(4)
        self.spin_volume_downsample.setEnabled(False)
        controls.addWidget(self.spin_volume_downsample)

        self.btn_reload_volume = QPushButton("Reload Volume")
        self.btn_reload_volume.setEnabled(False)
        controls.addWidget(self.btn_reload_volume)

        self.volume_status_label = QLabel("Volume: none")
        self.volume_status_label.setWordWrap(True)
        controls.addWidget(self.volume_status_label, 1)
        layout.addLayout(controls)

        self.view_stack = QStackedWidget()

        # Create unified viewer that supports both point clouds and meshes
        self.viewer = PointCloudWidget(self)
        self.view_stack.addWidget(self.viewer)

        self.volume_viewer = VolumeRenderWidget(self)
        self.view_stack.addWidget(self.volume_viewer)

        layout.addWidget(self.view_stack, 1)

        self.btn_toggle_volume.clicked.connect(self.toggle_volume_view)
        self.btn_toggle_mesh.clicked.connect(self.toggle_pointcloud_mesh_view)
        self.btn_reload_volume.clicked.connect(self.reload_volume)
        self.spin_volume_downsample.valueChanged.connect(self._mark_volume_stale)
        
        # Enable focus for keyboard events
        self.setFocusPolicy(Qt.StrongFocus)

    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard events for toggling views."""
        if event.key() == Qt.Key_T and event.modifiers() == Qt.ControlModifier:
            self.toggle_volume_view()
            event.accept()
        elif event.key() == Qt.Key_M and event.modifiers() == Qt.ControlModifier:
            self.toggle_pointcloud_mesh_view()
            event.accept()
        else:
            super().keyPressEvent(event)

    def set_info_text(self, text):
        self.info_label.setText(text)

    def set_volume_source(self, volume_source):
        self.volume_source = volume_source
        self._volume_loaded = False
        self._last_volume_shape_xyz = None
        has_source = volume_source is not None
        self.btn_toggle_volume.setEnabled(has_source)
        self.spin_volume_downsample.setEnabled(has_source)
        self.btn_reload_volume.setEnabled(has_source)

        if has_source:
            self.spin_volume_downsample.setValue(volume_source.default_downsample_zyx)
            self.volume_status_label.setText("Volume: lazy, not loaded")
        else:
            self.view_stack.setCurrentWidget(self.viewer)
            self.btn_toggle_volume.setText("Show 3D Volume")
            self.volume_status_label.setText("Volume: none")

    def toggle_volume_view(self):
        if self.volume_source is None:
            self.toggle_pointcloud_mesh_view()
            return

        if self.view_stack.currentWidget() is self.volume_viewer:
            self.view_stack.setCurrentWidget(self.viewer)
            self.btn_toggle_volume.setText("Show 3D Volume")
            return

        if self._volume_loaded:
            self._sync_volume_view_from_geometry()
            self.view_stack.setCurrentWidget(self.volume_viewer)
            self.btn_toggle_volume.setText("Show Geometry")
        else:
            self.reload_volume(show_after_load=True)

    def toggle_pointcloud_mesh_view(self):
        self.view_stack.setCurrentWidget(self.viewer)
        self.btn_toggle_volume.setText("Show 3D Volume")
        self.viewer.toggle_pointcloud_mesh_view()

    def _mark_volume_stale(self, _value):
        if self.volume_source is not None and self._volume_loaded:
            self._volume_loaded = False
            self.volume_status_label.setText("Volume: downsample changed, reload needed")

    def reload_volume(self, show_after_load=True):
        if self.volume_source is None:
            return
        if self._volume_worker is not None and self._volume_worker.isRunning():
            return
        if not self.volume_viewer.is_available():
            self.volume_status_label.setText("Volume: install pyqtgraph to enable 3D preview")
            return

        self.btn_toggle_volume.setEnabled(False)
        self.btn_reload_volume.setEnabled(False)
        self.spin_volume_downsample.setEnabled(False)
        self.volume_status_label.setText("Volume: loading preview...")

        self._volume_worker = VolumeLoadWorker(
            self.volume_source,
            self.spin_volume_downsample.value(),
            self,
        )
        self._volume_worker.finished.connect(
            lambda volume, metadata: self._on_volume_loaded(volume, metadata, show_after_load)
        )
        self._volume_worker.error.connect(self._on_volume_error)
        self._volume_worker.start()

    def _on_volume_loaded(self, volume, metadata, show_after_load):
        self.volume_viewer.set_volume(volume)
        self._last_volume_shape_xyz = tuple(int(v) for v in volume.shape)
        self._sync_volume_view_from_geometry(volume_shape_xyz=volume.shape)
        self._volume_loaded = True

        if show_after_load:
            self.view_stack.setCurrentWidget(self.volume_viewer)
            self.btn_toggle_volume.setText("Show Geometry")

        self.btn_toggle_volume.setEnabled(True)
        self.btn_reload_volume.setEnabled(True)
        self.spin_volume_downsample.setEnabled(True)
        self.volume_status_label.setText(
            "Volume: "
            f"{metadata['preview_shape_xyz']} preview, "
            f"downsample {metadata['downsample_zyx']}"
        )
        self._volume_worker = None

    def _sync_volume_view_from_geometry(self, volume_shape_xyz=None):
        """Keep volume preview in the same coordinate frame and view as geometry."""
        if not self.volume_viewer.is_available():
            return

        camera_state = self.viewer.get_camera_state()
        self.volume_viewer.set_camera_from_geometry_state(camera_state)

        bounds = self.viewer.get_scene_bounds()
        if bounds is None:
            return

        if volume_shape_xyz is None:
            if self._last_volume_shape_xyz is None:
                return
            volume_shape_xyz = self._last_volume_shape_xyz

        self.volume_viewer.align_volume_to_world_bounds(
            volume_shape_xyz=volume_shape_xyz,
            bounds_min_xyz=bounds[0],
            bounds_max_xyz=bounds[1],
        )

    def _on_volume_error(self, message):
        self.btn_toggle_volume.setEnabled(self.volume_source is not None)
        self.btn_reload_volume.setEnabled(self.volume_source is not None)
        self.spin_volume_downsample.setEnabled(self.volume_source is not None)
        self.volume_status_label.setText(f"Volume error: {message}")
        self._volume_worker = None

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
