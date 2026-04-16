from __future__ import annotations

from dataclasses import dataclass
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from Utils.thz_import import find_companion_cmt, inspect_thz_scan


@dataclass(frozen=True)
class THzImportParams:
    path: str
    cmt_path: str | None
    target_freq_thz: float
    pseudo_depth_mm: float


class THzImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cmt_user_modified = False
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        self.setWindowTitle("THz Import")
        self.setMinimumWidth(520)
        self.setStyleSheet(
            "background-color: #d3d3d3;"
            "padding: 3px;"
            "border-radius: 3px;"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addLayout(form)

        self.line_path = QLineEdit(self)
        self.line_path.setClearButtonEnabled(True)
        self.line_path.setStyleSheet("background-color: #f0f0f0;")
        self.btn_browse_t2t = QPushButton("...", self)
        self.btn_browse_t2t.setStyleSheet("background-color: #f0f0f0;")
        file_row = QWidget(self)
        file_row_layout = QHBoxLayout(file_row)
        file_row_layout.setContentsMargins(0, 0, 0, 0)
        file_row_layout.setSpacing(6)
        file_row_layout.addWidget(self.line_path, 1)
        file_row_layout.addWidget(self.btn_browse_t2t)
        form.addRow("THz Trace (.t2t)", file_row)

        self.line_cmt_path = QLineEdit(self)
        self.line_cmt_path.setClearButtonEnabled(True)
        self.line_cmt_path.setPlaceholderText("Optional companion .cmt file")
        self.line_cmt_path.setStyleSheet("background-color: #f0f0f0;")
        self.btn_browse_cmt = QPushButton("...", self)
        self.btn_browse_cmt.setStyleSheet("background-color: #f0f0f0;")
        cmt_row = QWidget(self)
        cmt_row_layout = QHBoxLayout(cmt_row)
        cmt_row_layout.setContentsMargins(0, 0, 0, 0)
        cmt_row_layout.setSpacing(6)
        cmt_row_layout.addWidget(self.line_cmt_path, 1)
        cmt_row_layout.addWidget(self.btn_browse_cmt)
        form.addRow("THz Metadata (.cmt)", cmt_row)

        self.line_target_freq = QLineEdit(self)
        self.line_target_freq.setAlignment(Qt.AlignRight)
        self.line_target_freq.setText("0.998")
        self.line_target_freq.setToolTip("Target FFT frequency in THz.")
        self.line_target_freq.setStyleSheet("background-color: #f0f0f0;")
        validator = QDoubleValidator(0.001, 50.0, 6, self)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.line_target_freq.setValidator(validator)
        form.addRow("Target Frequency (THz)", self.line_target_freq)

        self.line_pseudo_depth = QLineEdit(self)
        self.line_pseudo_depth.setAlignment(Qt.AlignRight)
        self.line_pseudo_depth.setText("0.0")
        self.line_pseudo_depth.setToolTip(
            "Pseudo 3D depth in mm. Use 0 for a single 2D slice. "
            "Values above 0 create a height-map volume for registration."
        )
        self.line_pseudo_depth.setStyleSheet("background-color: #f0f0f0;")
        depth_validator = QDoubleValidator(0.0, 100.0, 6, self)
        depth_validator.setNotation(QDoubleValidator.StandardNotation)
        self.line_pseudo_depth.setValidator(depth_validator)
        form.addRow("Pseudo Depth (mm)", self.line_pseudo_depth)

        self.label_detected = QLabel("Select a THz trace file to inspect timing and pixel calibration.")
        self.label_detected.setWordWrap(True)
        self.label_detected.setStyleSheet("background-color: #f0f0f0; padding: 6px;")
        layout.addWidget(self.label_detected)

        self.label_note = QLabel(
            "This imports a single FFT amplitude image as a calibrated one-slice volume. "
            "XY scaling is preserved from the THz metadata. Set a positive pseudo depth to build "
            "a registration-friendly 3D height map."
        )
        self.label_note.setWordWrap(True)
        layout.addWidget(self.label_note)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Horizontal,
            self,
        )
        self.button_box.setStyleSheet("background-color: #f0f0f0;")
        layout.addWidget(self.button_box)

    def _connect_signals(self):
        self.btn_browse_t2t.clicked.connect(self._browse_t2t)
        self.btn_browse_cmt.clicked.connect(self._browse_cmt)
        self.line_path.textChanged.connect(self._on_path_changed)
        self.line_cmt_path.textEdited.connect(self._mark_cmt_user_modified)
        self.line_cmt_path.textChanged.connect(self._refresh_detected_info)
        self.button_box.accepted.connect(self._validate_and_accept)
        self.button_box.rejected.connect(self.reject)

    def _browse_t2t(self):
        file_path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Select THz Trace File",
            "",
            "THz Trace Files (*.t2t)",
        )
        if file_path:
            self.line_path.setText(file_path)

    def _browse_cmt(self):
        file_path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Select THz Metadata File",
            "",
            "THz Metadata Files (*.cmt)",
        )
        if file_path:
            self._cmt_user_modified = True
            self.line_cmt_path.setText(file_path)

    def _mark_cmt_user_modified(self, _text):
        self._cmt_user_modified = True

    def _on_path_changed(self):
        t2t_path = self.line_path.text().strip()
        auto_cmt = find_companion_cmt(t2t_path) if t2t_path else None
        if auto_cmt and (not self._cmt_user_modified or not self.line_cmt_path.text().strip()):
            self.line_cmt_path.setText(auto_cmt)
        elif not auto_cmt and not self._cmt_user_modified:
            self.line_cmt_path.clear()
        self._refresh_detected_info()

    def _refresh_detected_info(self):
        t2t_path = self.line_path.text().strip()
        cmt_text = self.line_cmt_path.text().strip()
        cmt_path = cmt_text or None

        if not t2t_path:
            self.label_detected.setText("Select a THz trace file to inspect timing and pixel calibration.")
            return

        if not os.path.isfile(t2t_path):
            self.label_detected.setText("Selected THz trace file does not exist.")
            return

        try:
            info = inspect_thz_scan(t2t_path, cmt_path)
        except Exception as exc:
            self.label_detected.setText(str(exc))
            return

        details = [
            f"dt {info.dt_ps:.6g} ps",
            f"begin {info.begin_ps:.6g} ps",
        ]
        if info.trace_samples is not None:
            details.append(f"samples {info.trace_samples}")
        if info.resolution_x_mm is not None and info.resolution_y_mm is not None:
            details.append(f"pixel mm ({info.resolution_x_mm:.6g}, {info.resolution_y_mm:.6g})")
        if info.size_x_mm is not None and info.size_y_mm is not None:
            details.append(f"size mm ({info.size_x_mm:.6g}, {info.size_y_mm:.6g})")
        details.append("scaled pixel map ready" if info.resolution_x_mm and info.resolution_y_mm else "pixel size inferred from coordinates at import")

        self.label_detected.setText(" | ".join(details))

    def _validate_and_accept(self):
        t2t_path = self.line_path.text().strip()
        cmt_text = self.line_cmt_path.text().strip()
        freq_text = self.line_target_freq.text().strip()
        depth_text = self.line_pseudo_depth.text().strip()

        if not t2t_path:
            QMessageBox.warning(self, "Missing THz Trace", "Please select a THz .t2t file.")
            return
        if not os.path.isfile(t2t_path):
            QMessageBox.warning(self, "Invalid THz Trace", "The selected THz .t2t file does not exist.")
            return
        if cmt_text and not os.path.isfile(cmt_text):
            QMessageBox.warning(self, "Invalid THz Metadata", "The selected THz .cmt file does not exist.")
            return
        if not freq_text:
            QMessageBox.warning(self, "Missing Frequency", "Please enter a target FFT frequency in THz.")
            return

        try:
            target_freq_thz = float(freq_text)
        except ValueError:
            QMessageBox.warning(self, "Invalid Frequency", "Target frequency must be a valid decimal number.")
            return

        if target_freq_thz <= 0.0:
            QMessageBox.warning(self, "Invalid Frequency", "Target frequency must be greater than 0 THz.")
            return

        if not depth_text:
            QMessageBox.warning(self, "Missing Depth", "Please enter a pseudo depth in mm.")
            return

        try:
            pseudo_depth_mm = float(depth_text)
        except ValueError:
            QMessageBox.warning(self, "Invalid Depth", "Pseudo depth must be a valid decimal number.")
            return

        if pseudo_depth_mm < 0.0:
            QMessageBox.warning(self, "Invalid Depth", "Pseudo depth cannot be negative.")
            return

        self.accept()

    def get_import_params(self) -> THzImportParams:
        cmt_text = self.line_cmt_path.text().strip()
        return THzImportParams(
            path=self.line_path.text().strip(),
            cmt_path=cmt_text or None,
            target_freq_thz=float(self.line_target_freq.text().strip()),
            pseudo_depth_mm=float(self.line_pseudo_depth.text().strip() or "0.0"),
        )
