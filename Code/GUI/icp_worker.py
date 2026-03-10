from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QMainWindow
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
                step_callback=cb,
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
        # add step label and progress bar as permanent widgets
        from PySide6.QtWidgets import QLabel, QProgressBar
        self.step_label = QLabel("")
        self.progressBar = QProgressBar()
        self.progressBar.setMaximum(100)
        self.progressBar.setValue(0)
        self.statusBar().addPermanentWidget(self.step_label)
        self.statusBar().addPermanentWidget(self.progressBar)
    
    def add_point_cloud(self, name, pcd, color=None):
        """Add a point cloud to the viewer."""
        self.viewer.add_point_cloud(name, pcd, color)
        # Don't setup geometry here - let it happen during first paint call
        self.viewer.update()
    
    def clear(self):
        """Clear all point clouds."""
        self.viewer.clear_point_clouds()
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
            text = f"RANSAC {iteration}/{total}" if total else f"RANSAC {iteration}"
            self.step_label.setText(text)
            if total:
                self.progressBar.setValue(int(iteration / total * 100))
        elif stage == 2:
            text = f"ICP {iteration}/{total}" if total else f"ICP {iteration}"
            self.step_label.setText(text)
            if total:
                self.progressBar.setValue(int(iteration / total * 100))
        # update overlay text on inner widget if supported
        try:
            self.viewer.set_overlay_text(text)
        except Exception:
            pass

