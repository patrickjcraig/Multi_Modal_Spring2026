import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox

from defaults import DEFAULT_VOXEL_SIZE_MM
from .xray_file_import_dialog import XRayFileImportDialog
from .xray_import_types import XRayImportParams
from .ui_xray_dialog import Ui_XRayDialog


class XRayImportDialog(QDialog, Ui_XRayDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self._file_import_params = None

        self._setup_ui()
        self._setup_connections()

    def _setup_ui(self):
        # Keep line edits friendly for manual input / copy-paste
        self.line_path.setClearButtonEnabled(True)
        self.line_voxel_size.setClearButtonEnabled(True)
        self.line_voxel_size.setAlignment(Qt.AlignRight)
        self.line_voxel_size.setText(f"{DEFAULT_VOXEL_SIZE_MM}")

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
        self.spin_pcd_pts.setValue(30000)
        self.spin_pcd_pts.setToolTip("Higher point counts capture small internal features better.")
        self.spin_marching_cubes.setMinimum(0)
        self.spin_marching_cubes.setValue(0)
        self.spin_marching_cubes.setToolTip("Use 0 for Auto level detection. Higher values isolate only brighter materials.")
        self._configure_arrow_spinbox(self.spin_downsampling)

    @staticmethod
    def _configure_arrow_spinbox(spinbox):
        # Windows styles can clip the upper arrow when the control is compact.
        spinbox.setMinimumWidth(max(spinbox.minimumWidth(), 150))
        spinbox.setMinimumHeight(max(spinbox.minimumHeight(), 34))
        spinbox.setStyleSheet(
            "QSpinBox {"
            " background-color: #f0f0f0;"
            " border-radius: 3px;"
            " padding-left: 4px;"
            " padding-right: 22px;"
            "}"
            "QSpinBox::up-button, QSpinBox::down-button {"
            " width: 18px;"
            "}"
        )

    def _setup_connections(self):
        self.btn_browse.clicked.connect(self.browse_path)
        self.combo_import_type.currentTextChanged.connect(self._update_mode_state)
        self.buttonBox.accepted.connect(self.validate_and_accept)
        self.buttonBox.rejected.connect(self.reject)
        self._update_mode_state()

    def _numeric_defaults(self):
        return XRayImportParams(
            import_type=self.combo_import_type.currentText().strip().lower(),
            path=self.line_path.text().strip(),
            voxel_size_mm=float(self.line_voxel_size.text().strip() or DEFAULT_VOXEL_SIZE_MM),
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

    def _update_mode_state(self):
        import_type = self.combo_import_type.currentText().strip().lower()
        is_tiff = import_type == "tiff stack folder"
        self.label_file_folder.setText("Folder" if is_tiff else "File")
        self.label_marching_cubes.setText("Marching Cubes" if is_tiff else "Continue in next dialog")
        for widget in (
            self.line_voxel_size,
            self.spin_roi_x,
            self.spin_roi_y,
            self.spin_roi_z,
            self.spin_downsampling,
            self.spin_pcd_pts,
            self.spin_marching_cubes,
        ):
            widget.setEnabled(is_tiff)
        for label in (
            self.label_voxel_size,
            self.label_roi_xyz,
            self.label_downsampling,
            self.label_point_cloud_points,
        ):
            label.setEnabled(is_tiff)

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
        self._file_import_params = None

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

        if import_type in {"h5", "npy"}:
            try:
                file_dialog = XRayFileImportDialog(
                    import_type=import_type,
                    file_path=path,
                    defaults=self._numeric_defaults(),
                    parent=self,
                )
            except Exception as exc:
                QMessageBox.warning(self, "File Import Error", str(exc))
                return

            if not file_dialog.exec():
                return

            self._file_import_params = file_dialog.get_import_params()
            self.accept()
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
        if self._file_import_params is not None:
            return self._file_import_params

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
            dataset_path=None,
        )
