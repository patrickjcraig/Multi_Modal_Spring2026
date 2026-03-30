from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import QMainWindow, QLabel, QProgressBar
from PySide6.QtGui import QKeyEvent
from open3d_ICP import run_full_registration
from Widgets.pointcloud_widget import PointCloudWidget

class ICPWorkerThread(QThread):
    """
    Worker thread for running ICP registration without blocking the UI.

    This thread now emits step-by-step results via the ``step`` signal so that
    the GUI can visualize intermediate states (original clouds, post-ransac
    alignment, and post-ICP refinement) while the registration is executing.
    """
    finished = Signal(dict)  # Signal emitted when registration is complete
    error = Signal(str)       # Signal emitted if an error occurs
    # Emits (stage, iteration, data)
    # stage: 0=raw, 1=ransac, 2=icp
    step = Signal(int, int, dict)  # stage, iter, payload

    def __init__(
        self,
        voxel_size=2.0,
        ransac_dist_mult=1.5,
        ransac_max_iter=100000,
        ransac_validation=1000,
        icp_dist_mult=0.4,
        source_pcd=None,
        target_pcd=None,
        global_transform_model="rigid",
    ):
        super().__init__()
        self.voxel_size = voxel_size
        self.ransac_dist_mult = ransac_dist_mult
        self.ransac_max_iter = ransac_max_iter
        self.ransac_validation = ransac_validation
        self.icp_dist_mult = icp_dist_mult
        self.source_pcd = source_pcd
        self.target_pcd = target_pcd
        self.global_transform_model = global_transform_model
    
    def run(self):
        """Run the ICP registration in a background thread."""
        try:
            # forward the callback to the UI thread via the ``step`` signal
            def cb(stage, it, data):
                # simply forward tuple to GUI thread
                self.step.emit(stage, it, data)

            results = run_full_registration(
                voxel_size=self.voxel_size,
                ransac_dist_multiplier=self.ransac_dist_mult,
                ransac_max_iter=self.ransac_max_iter,
                ransac_validation=self.ransac_validation,
                icp_dist_multiplier=self.icp_dist_mult,
                source_pcd=self.source_pcd,
                target_pcd=self.target_pcd,
                step_callback=cb,
                global_transform_model=self.global_transform_model,
            )
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class PointCloudViewerWindow(QMainWindow):
    """
    Standalone window for viewing point clouds and meshes with OpenGL.
    Can toggle between point cloud and mesh visibility using Ctrl+T.
    Both geometries are rendered in the same OpenGL context with opacity control.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Point Cloud & Mesh Viewer - OpenGL")
        self.setGeometry(100, 100, 1000, 800)
        
        # Create unified viewer that supports both point clouds and meshes
        self.viewer = PointCloudWidget()
        self.setCentralWidget(self.viewer)
        
        # Create status bar with controls info
        status_msg = "Left Mouse: Rotate | Right Mouse: Pan | Scroll: Zoom | Ctrl+T: Toggle View"
        self.statusBar().showMessage(status_msg)
        
        # Add step label and progress bar to status bar
        self.step_label = QLabel("")
        self.progressBar = QProgressBar()
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)
        self.statusBar().addPermanentWidget(self.step_label)
        self.statusBar().addPermanentWidget(self.progressBar)
        
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

    def update_stage(self, stage, iteration, total=None):
        """Update progress bar and step label.

        ``stage`` is 0=raw, 1=ransac, 2=icp; ``total`` is optional total count.
        """
        if stage == 0:
            text = "raw clouds"
            self.step_label.setText(text)
            self.progressBar.setValue(0)
        elif stage == 1:
            text = f"Global RANSAC {iteration}/{total}" if total else f"Global RANSAC {iteration}"
            self.step_label.setText(text)
            if total:
                self.progressBar.setValue(int(iteration / total * 100))
        elif stage == 2:
            text = f"Local ICP {iteration}/{total}" if total else f"Local ICP {iteration}"
            self.step_label.setText(text)
            if total:
                self.progressBar.setValue(int(iteration / total * 100))
        
        # Update overlay text on viewer
        try:
            if hasattr(self.viewer, 'set_overlay_text'):
                self.viewer.set_overlay_text(text)
        except Exception:
            pass

