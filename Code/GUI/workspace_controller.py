# GUI elements for Save Workspace and Load Workspace
from PySide6.QtWidgets import QFileDialog, QMessageBox
from Utils.workspace_manager import save_workspace, load_workspace

class WorkspaceController:
    """
    Handles Save and Load workspace functionality.
    Only saves parameters and UI state.
    Does NOT save Open3D objects.
    """

    def __init__(self, main_window):
        self.main = main_window

    # -------------------------------------------------
    # Save Workspace (Parameters Only)
    # -------------------------------------------------

    def save(self):
        """
        Save only UI parameters and state.
        Avoids pickling Open3D objects.
        """

        filepath, selected_filter = QFileDialog.getSaveFileName(
        self.main,
        "Save Workspace",
        "",
        "Workspace Files (*.pkl)"
        )

        if not filepath:
            return

        # if .pkl is not manually typed for the file name, add the file extension to make it the correct file type
        if selected_filter == 'Workspace Files (*.pkl)' and not filepath.lower().endswith('.pkl'):
            filepath += '.pkl'

        workspace_data = {
            # UI parameters
            "voxel_size": self.main.spinBox_voxel_size.value(),
            "ransac_dist": self.main.spinBox_ransac_dist.value(),
            "ransac_max_iter": self.main.spinBox_ransac_max_iter.value(),
            "ransac_validation": self.main.spinBox_ransac_validation.value(),
            "icp_dist": self.main.spinBox_icp_dist.value(),

            # Application state
            "current_step": self.main.current_step,
        }

        try:
            save_workspace(filepath, workspace_data)
            self.main.statusbar.showMessage("Workspace parameters saved successfully.")
        except Exception as e:
            QMessageBox.critical(self.main, "Save Error", str(e))

    # -------------------------------------------------
    # Load Workspace (Parameters Only)
    # -------------------------------------------------

    def load(self):
        """
        Load previously saved UI parameters and state.
        """

        filepath, _ = QFileDialog.getOpenFileName(
            self.main,
            "Load Workspace",
            "",
            "Workspace Files (*.pkl)"
        )

        if not filepath:
            return

        try:
            workspace_data = load_workspace(filepath)

            # Reset scan (this will NOT save due to pickling limitations)
            self.main.scan_reset()

            # Restore UI parameters
            self.main.spinBox_voxel_size.setValue(workspace_data["voxel_size"])
            self.main.spinBox_ransac_dist.setValue(workspace_data["ransac_dist"])
            self.main.spinBox_ransac_max_iter.setValue(workspace_data["ransac_max_iter"])
            self.main.spinBox_ransac_validation.setValue(workspace_data["ransac_validation"])
            self.main.spinBox_icp_dist.setValue(workspace_data["icp_dist"])

            # Restore application state
            self.main.current_step = workspace_data["current_step"]

            # Update UI elements accordingly
            self.main.btn_prev_step.setEnabled(self.main.current_step > 0)
            self.main.btn_next_step.setEnabled(self.main.current_step < 2)

            self.main.statusbar.showMessage("Workspace parameters loaded successfully.")

        except Exception as e:
            QMessageBox.critical(self.main, "Load Error", str(e))