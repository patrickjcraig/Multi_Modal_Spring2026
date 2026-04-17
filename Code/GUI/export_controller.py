import os
from datetime import datetime

import numpy as np
import tifffile as tiff
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox

from Utils.image_enhancement import apply_gamma_contrast_uint8


class ExportController:
    """Handle export actions for generated registration reconstructions."""

    def __init__(self, main_window):
        self.main = main_window

    def export_current_registration_tiff_stack(self):
        record = self.main.current_scan()
        if record is None:
            self.main.statusbar.showMessage("Select a registration result tab before exporting.")
            return

        if not record.is_result or record.modality != "registration-result":
            QMessageBox.information(
                self.main,
                "Export",
                "Export is only available for finished registration result tabs.",
            )
            self.main.statusbar.showMessage("Export is only available for registration results.")
            return

        volume_source = record.volume_source
        if volume_source is None:
            QMessageBox.warning(
                self.main,
                "Export",
                "This registration result does not have a fused reconstruction volume yet.",
            )
            self.main.statusbar.showMessage("No reconstruction volume is available for export.")
            return

        if getattr(volume_source, "source_type", "") != "npy":
            QMessageBox.warning(
                self.main,
                "Export",
                "Only generated NPY reconstruction volumes are currently supported for TIFF export.",
            )
            self.main.statusbar.showMessage("Export skipped: unsupported reconstruction volume type.")
            return

        npy_path = getattr(volume_source, "path", "")
        if not npy_path or not os.path.isfile(npy_path):
            QMessageBox.warning(
                self.main,
                "Export",
                "The reconstruction file could not be found on disk.",
            )
            self.main.statusbar.showMessage("Export failed: reconstruction file is missing.")
            return

        base_dir = QFileDialog.getExistingDirectory(
            self.main,
            "Select Export Directory",
            os.path.dirname(npy_path),
        )
        if not base_dir:
            return

        default_folder = f"{self._sanitize_folder_name(record.name)}_tiff"
        folder_name, ok = QInputDialog.getText(
            self.main,
            "Export Folder Name",
            "Folder name for exported TIFF slices:",
            text=default_folder,
        )
        if not ok:
            return

        folder_name = self._sanitize_folder_name(folder_name)
        if not folder_name:
            QMessageBox.warning(self.main, "Export", "Folder name cannot be empty.")
            return

        downsample_text, ok = QInputDialog.getItem(
            self.main,
            "Downsampling",
            "Select isotropic downsampling factor (applied to Z, Y, X):",
            ["1", "2", "4", "8", "16"],
            current=1,
            editable=False,
        )
        if not ok:
            return
        downsample = int(downsample_text)

        output_dir = os.path.join(base_dir, folder_name)
        if os.path.exists(output_dir):
            existing = os.listdir(output_dir)
            if existing:
                overwrite = QMessageBox.question(
                    self.main,
                    "Export",
                    "The selected folder already exists and is not empty. Overwrite TIFF files with the same names?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if overwrite != QMessageBox.Yes:
                    self.main.statusbar.showMessage("Export cancelled.")
                    return
        else:
            os.makedirs(output_dir, exist_ok=True)

        try:
            volume_zyx = np.load(npy_path, allow_pickle=False)
        except Exception as exc:
            QMessageBox.critical(self.main, "Export Error", f"Failed to load reconstruction: {exc}")
            return

        if volume_zyx.ndim != 3:
            QMessageBox.critical(
                self.main,
                "Export Error",
                f"Expected a 3D reconstruction array, got shape {tuple(int(v) for v in volume_zyx.shape)}.",
            )
            return

        export_zyx = np.ascontiguousarray(volume_zyx[::downsample, ::downsample, ::downsample])

        gamma, contrast = self._current_slice_enhancement(record)
        export_zyx = apply_gamma_contrast_uint8(export_zyx, gamma=gamma, contrast=contrast)
        export_zyx = self._prepare_tiff_dtype(export_zyx)

        z_slices = int(export_zyx.shape[0])
        for z in range(z_slices):
            out_path = os.path.join(output_dir, f"slice_{z:05d}.tif")
            tiff.imwrite(out_path, export_zyx[z], compression="zlib")

        info_path = os.path.join(output_dir, "export_info.txt")
        with open(info_path, "w", encoding="utf-8") as handle:
            handle.write("Registration reconstruction TIFF export\n")
            handle.write(f"Exported: {datetime.now().isoformat(timespec='seconds')}\n")
            handle.write(f"Source volume: {npy_path}\n")
            handle.write(f"Original shape ZYX: {tuple(int(v) for v in volume_zyx.shape)}\n")
            handle.write(f"Export shape ZYX: {tuple(int(v) for v in export_zyx.shape)}\n")
            handle.write(f"Downsample factor: {downsample}\n")
            handle.write(f"Gamma: {gamma:.3f}\n")
            handle.write(f"Contrast: {contrast:.3f}\n")
            handle.write(f"Data type: {export_zyx.dtype}\n")

        self.main.statusbar.showMessage(
            f"Exported {z_slices} TIFF slices to '{output_dir}' (downsample {downsample}x)."
        )
        QMessageBox.information(
            self.main,
            "Export Complete",
            f"Exported {z_slices} TIFF slices to:\n{output_dir}",
        )

    @staticmethod
    def _current_slice_enhancement(record):
        gamma = 1.0
        contrast = 1.0
        tab = getattr(record, "tab", None)
        if tab is None:
            return gamma, contrast

        slice_viewer = getattr(tab, "slice_viewer", None)
        if slice_viewer is None:
            return gamma, contrast

        getter = getattr(slice_viewer, "get_enhancement_settings", None)
        if getter is None:
            return gamma, contrast

        try:
            values = getter()
            gamma = float(values.get("gamma", gamma))
            contrast = float(values.get("contrast", contrast))
        except Exception:
            gamma = 1.0
            contrast = 1.0
        return gamma, contrast

    @staticmethod
    def _sanitize_folder_name(name):
        name = str(name).strip().replace("\\", "_").replace("/", "_")
        if not name:
            return "registration_export"
        allowed = []
        for ch in name:
            if ch.isalnum() or ch in {"-", "_", "."}:
                allowed.append(ch)
            else:
                allowed.append("_")
        cleaned = "".join(allowed).strip("._")
        return cleaned or "registration_export"

    @staticmethod
    def _prepare_tiff_dtype(volume_zyx):
        if volume_zyx.dtype == np.uint8:
            return volume_zyx

        if volume_zyx.dtype == np.uint16:
            return volume_zyx

        if volume_zyx.dtype == np.bool_:
            return (volume_zyx.astype(np.uint8) * 255)

        if np.issubdtype(volume_zyx.dtype, np.floating):
            finite = volume_zyx[np.isfinite(volume_zyx)]
            if finite.size == 0:
                return np.zeros(volume_zyx.shape, dtype=np.uint8)
            vmin = float(np.min(finite))
            vmax = float(np.max(finite))
            if vmax <= vmin:
                return np.zeros(volume_zyx.shape, dtype=np.uint8)
            scaled = (volume_zyx.astype(np.float32, copy=False) - vmin) * (65535.0 / (vmax - vmin))
            np.clip(scaled, 0.0, 65535.0, out=scaled)
            return scaled.astype(np.uint16)

        if np.issubdtype(volume_zyx.dtype, np.integer):
            vmax = int(np.max(volume_zyx))
            if vmax <= 255:
                return volume_zyx.astype(np.uint8, copy=False)
            clipped = np.clip(volume_zyx, 0, 65535)
            return clipped.astype(np.uint16, copy=False)

        return volume_zyx.astype(np.uint8, copy=False)
