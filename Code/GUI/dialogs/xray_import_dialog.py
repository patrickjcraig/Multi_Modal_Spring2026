from dataclasses import dataclass
import os

from PySide6.QtWidgets import QDialog, QFileDialog, QMessageBox
from .ui_xray_dialog import Ui_XRayDialog


@dataclass
class XRayImportParams:
    import_type: str
    path: str


class XRayImportDialog(QDialog, Ui_XRayDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        # Optional: ensure combo box items exist in case you want to populate in code
        # Comment this out if you already added them in Designer.
        if self.combo_import_type.count() == 0:
            self.combo_import_type.addItems(["H5", "NPY", "TIFF Stack Folder"])

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
        path = self.line_path.text().strip()
        import_type = self.combo_import_type.currentText().strip().lower()

        if not path:
            QMessageBox.warning(self, "Missing Path", "Please select a file or folder.")
            return

        if not os.path.exists(path):
            QMessageBox.warning(self, "Invalid Path", "The selected path does not exist.")
            return

        if import_type == "tiff stack folder" and not os.path.isdir(path):
            QMessageBox.warning(self, "Invalid Selection", "Please select a folder for TIFF Stack import.")
            return

        if import_type in {"h5", "npy"} and not os.path.isfile(path):
            QMessageBox.warning(self, "Invalid Selection", "Please select a file for this import type.")
            return

        self.accept()

    def get_import_params(self) -> XRayImportParams:
        return XRayImportParams(
            import_type=self.combo_import_type.currentText().strip().lower(),
            path=self.line_path.text().strip()
        )