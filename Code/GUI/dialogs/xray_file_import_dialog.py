import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import QDialog, QMessageBox

from makeGeometry import inspect_array_volume, list_h5_volume_datasets

from .ui_xray_file_import_dialog import Ui_XRayFileImportDialog
from .xray_import_types import XRayImportParams


class XRayFileImportDialog(QDialog, Ui_XRayFileImportDialog):
    def __init__(self, import_type: str, file_path: str, defaults: XRayImportParams, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.import_type = import_type.strip().lower()
        self.file_path = file_path
        self.defaults = defaults
        self._selected_dataset_path = defaults.dataset_path

        self.setWindowTitle(f"X-Ray {self.import_type.upper()} Import")
        self.setModal(True)

        self._setup_ui()
        self._populate_defaults()
        self._setup_connections()
        self._load_file_metadata()

    def _setup_ui(self):
        self.line_path.setClearButtonEnabled(False)
        self.line_path.setReadOnly(True)

        self.line_voxel_size.setAlignment(Qt.AlignRight)
        self.line_voxel_size.setClearButtonEnabled(True)
        validator = QDoubleValidator(0.0, 1.0, 18, self)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.line_voxel_size.setValidator(validator)
        self.spin_marching_cubes.setMinimum(0)
        self.spin_marching_cubes.setToolTip("Use 0 for Auto level detection.")

    def _setup_connections(self):
        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)
        self.combo_dataset.currentIndexChanged.connect(self._refresh_detected_info)

    def _populate_defaults(self):
        self.line_path.setText(self.file_path)
        self.line_voxel_size.setText(f"{self.defaults.voxel_size_mm}")
        self.spin_roi_x.setValue(self.defaults.roi_xyz[0])
        self.spin_roi_y.setValue(self.defaults.roi_xyz[1])
        self.spin_roi_z.setValue(self.defaults.roi_xyz[2])
        self.spin_downsampling.setValue(self.defaults.downsampling)
        self.spin_pcd_pts.setValue(self.defaults.pcd_points)
        self.spin_marching_cubes.setValue(self.defaults.level)

        is_h5 = self.import_type == "h5"
        self.label_dataset.setVisible(is_h5)
        self.combo_dataset.setVisible(is_h5)

    def _load_file_metadata(self):
        if self.import_type == "h5":
            datasets = list_h5_volume_datasets(self.file_path)
            if not datasets:
                raise ValueError("No 3D numeric datasets were found in the selected H5 file.")

            self.combo_dataset.blockSignals(True)
            self.combo_dataset.clear()
            for entry in datasets:
                label = f"{entry['path']}  {entry['shape_zyx']}  {entry['dtype']}"
                self.combo_dataset.addItem(label, entry)

            target_path = self._selected_dataset_path
            if target_path:
                for index in range(self.combo_dataset.count()):
                    entry = self.combo_dataset.itemData(index)
                    if entry["path"] == target_path:
                        self.combo_dataset.setCurrentIndex(index)
                        break
            self.combo_dataset.blockSignals(False)
            self._refresh_detected_info()
        else:
            info = inspect_array_volume(self.file_path, self.import_type)
            self.label_volume_info.setText(
                f"shape ZYX {info['shape_zyx']} | dtype {info['dtype']}"
            )

    def _refresh_detected_info(self):
        if self.import_type != "h5" or self.combo_dataset.count() == 0:
            return

        entry = self.combo_dataset.currentData()
        if entry is None:
            return

        text = f"shape ZYX {entry['shape_zyx']} | dtype {entry['dtype']}"
        spacing = entry.get("spacing_zyx_mm")
        if spacing:
            text += f" | spacing_zyx_mm {spacing}"
        self.label_volume_info.setText(text)

    def validate_and_accept(self):
        if not os.path.isfile(self.file_path):
            QMessageBox.warning(self, "Invalid File", "The selected file does not exist.")
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

        if self.import_type == "h5" and self.combo_dataset.currentData() is None:
            QMessageBox.warning(self, "Missing Dataset", "Please choose an H5 dataset to import.")
            return

        self.accept()

    def get_import_params(self):
        dataset_path = None
        if self.import_type == "h5" and self.combo_dataset.currentData() is not None:
            dataset_path = self.combo_dataset.currentData()["path"]

        return XRayImportParams(
            import_type=self.import_type,
            path=self.file_path,
            voxel_size_mm=float(self.line_voxel_size.text().strip()),
            roi_xyz=(
                self.spin_roi_x.value(),
                self.spin_roi_y.value(),
                self.spin_roi_z.value(),
            ),
            downsampling=self.spin_downsampling.value(),
            pcd_points=self.spin_pcd_pts.value(),
            level=self.spin_marching_cubes.value(),
            dataset_path=dataset_path,
        )
