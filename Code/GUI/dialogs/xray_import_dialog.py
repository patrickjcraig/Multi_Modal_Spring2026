from dataclasses import dataclass
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox

from .ui_xray_dialog import Ui_XRayDialog


@dataclass
class XRayImportParams:
    import_type: str
    path: str
    voxel_size_mm: float
    roi_xyz: tuple[int, int, int]
    downsampling: int
    pcd_points: int
    level: int


class XRayImportDialog(QDialog, Ui_XRayDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        # Keep line edits friendly for manual input / copy-paste
        self.line_path.setClearButtonEnabled(True)
        self.line_voxel_size.setClearButtonEnabled(True)
        self.line_voxel_size.setAlignment(Qt.AlignRight)

        # Validate voxel size as a positive decimal number typed by the user.
        # StandardNotation avoids scientific notation entry like 1e-9.
        validator = QDoubleValidator(0.0, 1.0, 18, self)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.line_voxel_size.setValidator(validator)

        # Reasonable lower bounds for integer inputs
        self.spin_roi_x.setMinimum(1)
        self.spin_roi_y.setMinimum(1)
        self.spin_roi_z.setMinimum(1)
        self.spin_downsampling.setMinimum(1)
        self.spin_pcd_pts.setMinimum(1)
        self.spin_marching_cubes.setMinimum(1)

    def _setup_connections(self):
        self.btn_browse.clicked.connect(self.browse_path)
        self.buttonBox.accepted.connect(self.validate_and_accept)
        self.buttonBox.rejected.connect(self.reject)

    def browse_path(self):
        import_type = self.combo_import_type.currentText().strip().lower()

        if import_type == "tiff stack folder":
            folder = QFileDialog.getExistingDirectory(
                self,
                "Select TIFF Stack Folder"
            )
            if folder:
                self.line_path.setText(folder)

        elif import_type == "h5":
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select H5 File",
                "",
                "H5 Files (*.h5 *.hdf5)"
            )
            if file_path:
                self.line_path.setText(file_path)

        elif import_type == "npy":
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select NPY File",
                "",
                "NumPy Files (*.npy)"
            )
            if file_path:
                self.line_path.setText(file_path)

    def validate_and_accept(self):
        import_type = self.combo_import_type.currentText().strip().lower()
        path = self.line_path.text().strip()
        voxel_text = self.line_voxel_size.text().strip()
        level = self.spin_marching_cubes.value()

        if not path:
            QMessageBox.warning(self, "Missing Path", "Please select a file or folder path.")
            return

        if not os.path.exists(path):
            QMessageBox.warning(self, "Invalid Path", "The selected path does not exist.")
            return

        if import_type == "tiff stack folder" and not os.path.isdir(path):
            QMessageBox.warning(
                self,
                "Invalid Selection",
                "TIFF Stack import requires a folder."
            )
            return

        if import_type in {"h5", "npy"} and not os.path.isfile(path):
            QMessageBox.warning(
                self,
                "Invalid Selection",
                f"{self.combo_import_type.currentText()} import requires a file."
            )
            return

        if not voxel_text:
            QMessageBox.warning(self, "Missing Voxel Size", "Please enter a voxel size in mm.")
            return

        try:
            voxel_size_mm = float(voxel_text)
        except ValueError:
            QMessageBox.warning(self, "Invalid Voxel Size", "Voxel size must be a valid decimal number.")
            return

        if voxel_size_mm <= 0:
            QMessageBox.warning(self, "Invalid Voxel Size", "Voxel size must be greater than 0.")
            return

        roi_xyz = (
            self.spin_roi_x.value(),
            self.spin_roi_y.value(),
            self.spin_roi_z.value(),
        )

        if any(v <= 0 for v in roi_xyz):
            QMessageBox.warning(self, "Invalid ROI", "All ROI values must be greater than 0.")
            return

        if self.spin_downsampling.value() <= 0:
            QMessageBox.warning(self, "Invalid Downsampling", "Downsampling must be greater than 0.")
            return

        if self.spin_pcd_pts.value() <= 0:
            QMessageBox.warning(self, "Invalid Point Count", "Point cloud point count must be greater than 0.")
            return

        self.accept()

    def get_import_params(self) -> XRayImportParams:
        return XRayImportParams(
            import_type=self.combo_import_type.currentText().strip().lower(),
            path=self.line_path.text().strip(),
            voxel_size_mm=float(self.line_voxel_size.text().strip()),
            roi_xyz=(
                self.spin_roi_x.value(),
                self.spin_roi_y.value(),
                self.spin_roi_z.value(),
            ),
            downsampling=self.spin_downsampling.value(),
            pcd_points=self.spin_pcd_pts.value(),
            level=self.spin_marching_cubes.value(),
        )