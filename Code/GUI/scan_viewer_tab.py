from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QThread, Qt, Signal, QTimer
from PySide6.QtGui import QKeyEvent, QKeySequence, QShortcut

from makeGeometry import load_ct_volume_preview
from GUI.slice_viewer_tab import SliceViewerTab
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
                volume_source=self.volume_source,
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
        self._showing_volume_mode = False
        self._volume_xyz = None
        self._volume_metadata = None
        self._slice_viewer_enabled = False

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

        self.viewer_tabs = QTabWidget(self)
        self.viewer_tabs.setTabPosition(QTabWidget.North)
        layout.addWidget(self.viewer_tabs, 1)

        # 3D view page
        self.page_3d_view = QWidget(self.viewer_tabs)
        page_3d_layout = QVBoxLayout(self.page_3d_view)
        page_3d_layout.setContentsMargins(0, 0, 0, 0)
        page_3d_layout.setSpacing(6)

        # Single pyqtgraph renderer for both geometry and volume
        self.viewer = VolumeRenderWidget(self.page_3d_view)
        self.volume_viewer = self.viewer
        page_3d_layout.addWidget(self.viewer, 1)

        self.slice_viewer = SliceViewerTab(self.viewer_tabs, on_slice_changed=self._on_slice_changed)
        page_3d_layout.addWidget(self.slice_viewer.controls_frame)
        self.slice_viewer.page.layout().insertWidget(0, self.slice_viewer.enhancement_controls_frame)

        self.viewer_tabs.addTab(self.page_3d_view, "3D View")

        self.viewer_tabs.addTab(self.slice_viewer.page, "2D Slice")
        self.viewer_tabs.setTabEnabled(1, False)
        self.viewer_tabs.currentChanged.connect(self._on_viewer_tab_changed)

        self.btn_toggle_volume.clicked.connect(self.toggle_volume_view)
        self.btn_toggle_mesh.clicked.connect(self.toggle_pointcloud_mesh_view)
        self.btn_reload_volume.clicked.connect(self.reload_volume)
        self.spin_volume_downsample.valueChanged.connect(self._mark_volume_stale)

        # Keep shortcuts working even when child widgets (like GLViewWidget) have focus.
        self.shortcut_toggle_volume = QShortcut(QKeySequence("Ctrl+T"), self)
        self.shortcut_toggle_volume.setContext(Qt.WidgetWithChildrenShortcut)
        self.shortcut_toggle_volume.activated.connect(self.toggle_volume_view)

        self.shortcut_toggle_mesh = QShortcut(QKeySequence("Ctrl+M"), self)
        self.shortcut_toggle_mesh.setContext(Qt.WidgetWithChildrenShortcut)
        self.shortcut_toggle_mesh.activated.connect(self.toggle_pointcloud_mesh_view)

        self.shortcut_slice_up = QShortcut(QKeySequence(Qt.Key_Up), self)
        self.shortcut_slice_up.setContext(Qt.WidgetWithChildrenShortcut)
        self.shortcut_slice_up.activated.connect(lambda: self.slice_viewer.step_slice(+1))

        self.shortcut_slice_down = QShortcut(QKeySequence(Qt.Key_Down), self)
        self.shortcut_slice_down.setContext(Qt.WidgetWithChildrenShortcut)
        self.shortcut_slice_down.activated.connect(lambda: self.slice_viewer.step_slice(-1))
        
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
        elif event.key() == Qt.Key_Up and event.modifiers() == Qt.NoModifier:
            self.slice_viewer.step_slice(+1)
            event.accept()
        elif event.key() == Qt.Key_Down and event.modifiers() == Qt.NoModifier:
            self.slice_viewer.step_slice(-1)
            event.accept()
        else:
            super().keyPressEvent(event)

    def set_info_text(self, text):
        self.info_label.setText(text)

    def set_volume_source(self, volume_source):
        self.volume_source = volume_source
        self._volume_loaded = False
        self._last_volume_shape_xyz = None
        self._volume_xyz = None
        self._volume_metadata = None
        has_source = volume_source is not None
        self.btn_toggle_volume.setEnabled(has_source)
        self.spin_volume_downsample.setEnabled(has_source)
        self.btn_reload_volume.setEnabled(has_source)

        if has_source:
            self.spin_volume_downsample.setValue(volume_source.default_downsample_zyx)
            self.volume_status_label.setText("Volume: preloading preview...")
            # Preload in the background so the first toggle to volume is immediate.
            self.reload_volume(show_after_load=False)
        else:
            self._showing_volume_mode = False
            self.viewer.set_volume_mode(False)
            self.btn_toggle_volume.setText("Show 3D Volume")
            self.volume_status_label.setText("Volume: none")
            self.slice_viewer.clear_volume()
            self.viewer.clear_slice_indicator()
            self.disable_slice_viewer()

    def toggle_slice_viewer(self):
        if self._slice_viewer_enabled:
            self.disable_slice_viewer()
            return
        self.enable_slice_viewer()

    def is_slice_viewer_enabled(self):
        return self._slice_viewer_enabled

    def enable_slice_viewer(self):
        if self.volume_source is None:
            self.slice_viewer.set_unavailable_message()
            return

        self._slice_viewer_enabled = True
        self.slice_viewer.set_active(True)
        self.viewer_tabs.setTabEnabled(1, True)
        self.viewer.set_slice_indicator_visible(True)

        if self._volume_loaded and self._volume_xyz is not None:
            self.slice_viewer.set_volume(self._volume_xyz)
            self._update_slice_indicator()
        else:
            self.slice_viewer.set_loading_message()
            self.reload_volume(show_after_load=self._showing_volume_mode)

    def disable_slice_viewer(self):
        self._slice_viewer_enabled = False
        self.slice_viewer.set_active(False)
        self.viewer_tabs.setCurrentIndex(0)
        self.viewer_tabs.setTabEnabled(1, False)
        self.viewer.clear_slice_indicator()

    def toggle_volume_view(self):
        if self.volume_source is None:
            self.toggle_pointcloud_mesh_view()
            return

        if self._showing_volume_mode:
            self._showing_volume_mode = False
            self.viewer.set_volume_mode(False)
            self.btn_toggle_volume.setText("Show 3D Volume")
            return

        if self._volume_loaded:
            self._sync_volume_view_from_geometry()
            self._showing_volume_mode = True
            self.viewer.set_volume_mode(True)
            self.btn_toggle_volume.setText("Show Geometry")
        else:
            self.reload_volume(show_after_load=True)

    def toggle_pointcloud_mesh_view(self):
        self._showing_volume_mode = False
        self.viewer.set_volume_mode(False)
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
        self.viewer.set_volume(volume)
        self._volume_xyz = volume
        self._volume_metadata = dict(metadata)
        self._last_volume_shape_xyz = tuple(int(v) for v in volume.shape)
        self._sync_volume_view_from_geometry(volume_shape_xyz=volume.shape)
        self._volume_loaded = True

        if self._slice_viewer_enabled:
            self.slice_viewer.set_volume(volume)
            self._update_slice_indicator()

        if show_after_load:
            self._showing_volume_mode = True
            self.viewer.set_volume_mode(True)
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
        """Align volume scale/placement to geometry bounds inside shared pyqtgraph view."""
        if not self.volume_viewer.is_available():
            return

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
        self._update_slice_indicator()

    def _on_volume_error(self, message):
        self.btn_toggle_volume.setEnabled(self.volume_source is not None)
        self.btn_reload_volume.setEnabled(self.volume_source is not None)
        self.spin_volume_downsample.setEnabled(self.volume_source is not None)
        self.volume_status_label.setText(f"Volume error: {message}")
        self._volume_metadata = None
        if self._slice_viewer_enabled:
            self.slice_viewer.set_error_message(message)
            self.viewer.clear_slice_indicator()
        self._volume_worker = None

    def get_volume_preview_metadata(self):
        if self._volume_metadata is None:
            return None
        return dict(self._volume_metadata)

    def set_point_clouds(self, clouds):
        """Replace the displayed point clouds with ``clouds``.

        ``clouds`` is an iterable of ``(name, pcd, color)`` tuples.
        """
        self.viewer.clear_point_clouds()
        for name, pcd, color in clouds:
            self.viewer.add_point_cloud(name, pcd, color=color)
        if self._volume_loaded:
            self._sync_volume_view_from_geometry()
        self.viewer.update()
    
    def set_mesh(self, name, mesh, color=None):
        """Add a mesh to the viewer.
        
        Args:
            name: Identifier for the mesh
            mesh: open3d.geometry.TriangleMesh
            color: Optional RGB color tuple (0-1 range)
        """
        self.viewer.add_mesh(name, mesh, color)
        if self._volume_loaded:
            self._sync_volume_view_from_geometry()
        self.viewer.update()

    def set_meshes(self, meshes):
        """Replace displayed meshes with ``meshes``.

        ``meshes`` is an iterable of ``(name, mesh, color)`` tuples.
        """
        self.viewer.clear_meshes()
        for name, mesh, color in meshes:
            self.viewer.add_mesh(name, mesh, color=color)
        if self._volume_loaded:
            self._sync_volume_view_from_geometry()
        self.viewer.update()
    
    def clear_meshes(self):
        """Clear all meshes from the viewer."""
        self.viewer.clear_meshes()
        self.viewer.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.slice_viewer.refresh()

    def _on_slice_changed(self, _slice_index, _slice_count, _slice_axis):
        self._update_slice_indicator()

    def _on_viewer_tab_changed(self, index):
        # Re-render once the 2D page is actually visible so scaling uses
        # the final on-screen widget size instead of hidden-tab size hints.
        if int(index) == 1:
            QTimer.singleShot(0, self.slice_viewer.refresh)

    def _update_slice_indicator(self):
        if not self._slice_viewer_enabled:
            return
        if self._volume_xyz is None:
            return
        if hasattr(self.slice_viewer, "get_all_slice_positions") and hasattr(self.viewer, "set_slice_indicators"):
            self.viewer.set_slice_indicators(self.slice_viewer.get_all_slice_positions())
            return

        # Backward compatibility for older single-plane viewer API.
        self.viewer.set_slice_indicator(
            slice_index=self.slice_viewer.get_slice_index(),
            slice_count=self.slice_viewer.get_slice_count(),
            axis=self.slice_viewer.get_slice_axis(),
        )
