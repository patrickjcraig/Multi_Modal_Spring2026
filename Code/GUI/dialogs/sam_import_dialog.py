import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox

from makeGeometry import inspect_png_stack

from .ui_sam_import_dialog import Ui_SAMImportDialog
from .xray_import_types import SAMImportParams


class SAMImportDialog(QDialog, Ui_SAMImportDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        self.line_path.setClearButtonEnabled(True)
        self.line_voxel_size.setClearButtonEnabled(True)
        self.line_voxel_size.setAlignment(Qt.AlignRight)
        self.line_voxel_size.setText("0.006937965888099794")
        self.line_voxel_size.setPlaceholderText("Voxel size in mm")
        self.line_voxel_size.setToolTip("Voxel size in millimeters (example: 0.0004631795)")

        validator = QDoubleValidator(0.0, 1.0, 18, self)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.line_voxel_size.setValidator(validator)
        self.spin_marching_cubes.setValue(128)
        self.spin_marching_cubes.setToolTip("For 8-bit SAM PNG data, a typical surface level is in the 1-255 range.")

    def _setup_connections(self):
        self.btn_browse.clicked.connect(self.browse_path)
        self.line_path.textChanged.connect(self._refresh_detected_info)
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)

    def browse_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Select SAM PNG Stack Folder")
        if folder:
            self.line_path.setText(folder)

    def _refresh_detected_info(self):
        folder_path = self.line_path.text().strip()
        if not folder_path or not os.path.isdir(folder_path):
            self.label_detected.setText("")
            return

        try:
            info = inspect_png_stack(folder_path)
        except Exception as exc:
            self.label_detected.setText(str(exc))
            return

        shape_zyx = tuple(int(v) for v in info["shape_zyx"])
        shape_xyz = (shape_zyx[2], shape_zyx[1], shape_zyx[0])
        self.label_detected.setText(
            f"shape XYZ {shape_xyz} | dtype {info['dtype']} | slices {info['slice_count']}"
        )

    def validate_and_accept(self):
        folder_path = self.line_path.text().strip()
        if not folder_path:
            QMessageBox.warning(self, "Missing Folder", "Please select a SAM PNG stack folder.")
            return

        if not os.path.isdir(folder_path):
            QMessageBox.warning(self, "Invalid Folder", "The selected SAM folder does not exist.")
            return

        try:
            inspect_png_stack(folder_path)
        except Exception as exc:
            QMessageBox.warning(self, "Invalid SAM Stack", str(exc))
            return

        voxel_text = self.line_voxel_size.text().strip()
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

        self.accept()

    def get_import_params(self) -> SAMImportParams:
        return SAMImportParams(
            import_type="png stack folder",
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
            dataset_path=None,
        )
