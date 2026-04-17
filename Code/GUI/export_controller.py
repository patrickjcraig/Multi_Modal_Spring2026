import os
from datetime import datetime

import numpy as np
import tifffile as tiff
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox

from makeGeometry import VolumeSource, load_ct_volume_preview
from Utils.image_enhancement import apply_gamma_contrast_uint8


class ExportController:
    """Handle export actions for generated registration reconstructions."""

    def __init__(self, main_window):
        self.main = main_window
        # Keep export loads bounded to avoid OOM crashes on large volumes.
        self.max_export_preview_voxels = 80_000_000

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

        predicted_path = getattr(volume_source, "path", "")
        if not predicted_path or not os.path.exists(predicted_path):
            QMessageBox.warning(
                self.main,
                "Export",
                "The reconstruction file could not be found on disk.",
            )
            self.main.statusbar.showMessage("Export failed: reconstruction file is missing.")
            return

        source_volume_source, source_preview_downsample = self._resolve_role_export_spec(record, role="source")
        target_volume_source, target_preview_downsample = self._resolve_role_export_spec(record, role="target")
        if source_volume_source is None or target_volume_source is None:
            QMessageBox.warning(
                self.main,
                "Export",
                "Source/Target reconstruction references are missing on this registration result.",
            )
            self.main.statusbar.showMessage("Export failed: source/target reconstruction is unavailable.")
            return

        base_dir = QFileDialog.getExistingDirectory(
            self.main,
            "Select Export Directory",
            os.path.dirname(predicted_path),
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
            "Select isotropic downsampling factor for Predicted_Fusion (Source/Target use slice-view preview scale):",
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

        gamma, contrast = self._current_slice_enhancement(record)

        roles = [
            ("Source", source_volume_source, int(max(1, source_preview_downsample))),
            ("Target", target_volume_source, int(max(1, target_preview_downsample))),
            ("Predicted_Fusion", volume_source, int(max(1, downsample))),
        ]
        role_exports = []
        for role_name, role_volume_source, role_downsample in roles:
            try:
                volume_zyx, source_shape_zyx = self._load_volume_zyx_for_export(
                    role_volume_source,
                    downsample=role_downsample,
                )
                volume_zyx = apply_gamma_contrast_uint8(volume_zyx, gamma=gamma, contrast=contrast)
                volume_zyx = self._prepare_tiff_dtype(volume_zyx)

                role_dir = os.path.join(output_dir, role_name)
                os.makedirs(role_dir, exist_ok=True)
                z_slices = self._write_tiff_stack(role_dir, volume_zyx)
                role_exports.append(
                    {
                        "name": role_name,
                        "path": role_dir,
                        "source_path": getattr(role_volume_source, "path", ""),
                        "source_shape_zyx": source_shape_zyx,
                        "preview_downsample": int(role_downsample),
                        "export_shape_zyx": tuple(int(v) for v in volume_zyx.shape),
                        "z_slices": z_slices,
                        "dtype": str(volume_zyx.dtype),
                    }
                )
            except Exception as exc:
                QMessageBox.critical(
                    self.main,
                    "Export Error",
                    f"Failed while exporting '{role_name}' stack:\n{exc}",
                )
                self.main.statusbar.showMessage(f"Export failed while processing '{role_name}'.")
                return

        info_path = os.path.join(output_dir, "export_info.txt")
        with open(info_path, "w", encoding="utf-8") as handle:
            handle.write("Registration reconstruction TIFF export (multi-folder)\n")
            handle.write(f"Exported: {datetime.now().isoformat(timespec='seconds')}\n")
            handle.write(f"Predicted_Fusion downsample factor: {downsample}\n")
            handle.write(f"Gamma: {gamma:.3f}\n")
            handle.write(f"Contrast: {contrast:.3f}\n")
            handle.write("\n")
            for role in role_exports:
                handle.write(f"[{role['name']}]\n")
                handle.write(f"Source volume: {role['source_path']}\n")
                handle.write(f"Source shape ZYX: {role['source_shape_zyx']}\n")
                handle.write(f"Preview downsample ZYX: {role['preview_downsample']}\n")
                handle.write(f"Export shape ZYX: {role['export_shape_zyx']}\n")
                handle.write(f"Data type: {role['dtype']}\n")
                handle.write(f"TIFF slices: {role['z_slices']}\n")
                handle.write(f"Folder: {role['path']}\n")
                handle.write("\n")

        total_slices = sum(int(role["z_slices"]) for role in role_exports)

        self.main.statusbar.showMessage(
            f"Exported Source/Target/Predicted_Fusion TIFF stacks to '{output_dir}' (downsample {downsample}x)."
        )
        QMessageBox.information(
            self.main,
            "Export Complete",
            f"Export complete.\n\n"
            f"Source: {role_exports[0]['z_slices']} slices\n"
            f"Target: {role_exports[1]['z_slices']} slices\n"
            f"Predicted_Fusion: {role_exports[2]['z_slices']} slices\n"
            f"Total slices: {total_slices}\n\n"
            f"Root folder:\n{output_dir}",
        )

    def _resolve_role_export_spec(self, result_record, role):
        metadata = getattr(result_record, "metadata", {}) or {}
        key = f"{role}_volume_source"
        from_metadata = self._deserialize_volume_source(metadata.get(key))
        role_scan = None

        scan_id_key = f"{role}_scan_id"
        scan_id = metadata.get(scan_id_key)
        if scan_id:
            role_scan = self.main.scans.get(scan_id)

        if from_metadata is not None:
            downsample = self._slice_preview_downsample_for_scan(role_scan, from_metadata)
            return from_metadata, downsample

        if role_scan is not None:
            volume_source = getattr(role_scan, "volume_source", None)
            downsample = self._slice_preview_downsample_for_scan(role_scan, volume_source)
            return volume_source, downsample

        return None, 1

    @staticmethod
    def _slice_preview_downsample_for_scan(scan, fallback_volume_source):
        if scan is not None:
            tab = getattr(scan, "tab", None)
            if tab is not None:
                spin = getattr(tab, "spin_volume_downsample", None)
                if spin is not None:
                    try:
                        return max(1, int(spin.value()))
                    except Exception:
                        pass

            volume_source = getattr(scan, "volume_source", None)
            if volume_source is not None:
                return max(1, int(getattr(volume_source, "default_downsample_zyx", 1)))

        if fallback_volume_source is not None:
            return max(1, int(getattr(fallback_volume_source, "default_downsample_zyx", 1)))

        return 1

    @staticmethod
    def _deserialize_volume_source(data):
        if not isinstance(data, dict):
            return None

        path = str(data.get("path", "") or "")
        source_type = str(data.get("source_type", "") or "")
        if not path or not source_type:
            return None

        return VolumeSource(
            path=path,
            source_type=source_type,
            voxel_size_mm=data.get("voxel_size_mm", None),
            crop_zyx=data.get("crop_zyx", None),
            default_downsample_zyx=max(1, int(data.get("default_downsample_zyx", 1) or 1)),
            dataset_path=data.get("dataset_path", None),
        )

    @staticmethod
    def _write_tiff_stack(output_dir, volume_zyx):
        z_slices = int(volume_zyx.shape[0])
        for z in range(z_slices):
            out_path = os.path.join(output_dir, f"slice_{z:05d}.tif")
            tiff.imwrite(out_path, volume_zyx[z], compression="zlib")
        return z_slices

    def _load_volume_zyx_for_export(self, volume_source, downsample):
        preview_xyz, metadata = load_ct_volume_preview(
            volume_source=volume_source,
            downsample_zyx=max(1, int(downsample)),
            crop_zyx=getattr(volume_source, "crop_zyx", None),
            max_preview_voxels=int(self.max_export_preview_voxels),
        )
        preview_zyx = np.ascontiguousarray(np.transpose(preview_xyz, (2, 1, 0)))
        return preview_zyx, tuple(int(v) for v in metadata.get("shape_zyx", preview_zyx.shape))

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
