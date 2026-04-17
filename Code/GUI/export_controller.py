import os
from datetime import datetime

import numpy as np
import tifffile as tiff
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox
from scipy.ndimage import map_coordinates

from makeGeometry import (
    VolumeSource,
    inspect_volume_source,
    load_ct_volume_preview,
    load_volume_region_zyx,
)
from Utils.image_enhancement import apply_gamma_contrast_uint8
from Utils.image_fusion import compute_similarity_metrics, normalize_image_uint8, pca_fuse_images


class ExportController:
    """Handle export actions for generated registration reconstructions."""

    def __init__(self, main_window):
        self.main = main_window
        # Keep export loads bounded to avoid OOM crashes on large volumes.
        self.max_export_preview_voxels = 80_000_000
        self.max_slice_fusion_region_voxels = 64_000_000
        self.slice_fusion_initial_tile_size = 768
        self.slice_fusion_min_tile_size = 32

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

    def fuse_current_registration_slice_pca(self):
        record = self.main.current_scan()
        if record is None:
            self.main.statusbar.showMessage("Select a registration result tab before creating a PCA fusion slice.")
            return

        if not record.is_result or record.modality != "registration-result":
            QMessageBox.information(
                self.main,
                "PCA Slice Fusion",
                "Select a finished registration result tab before creating a PCA fusion slice.",
            )
            self.main.statusbar.showMessage("PCA slice fusion is only available for registration results.")
            return

        fusion_context = self._resolve_registration_fusion_context(record)
        if fusion_context["error"] is not None:
            QMessageBox.warning(self.main, "PCA Slice Fusion", fusion_context["error"])
            self.main.statusbar.showMessage("PCA slice fusion could not start.")
            return

        try:
            fusion_result = self._build_pca_slice_fusion(record, fusion_context)
        except Exception as exc:
            QMessageBox.critical(self.main, "PCA Slice Fusion Error", str(exc))
            self.main.statusbar.showMessage("PCA slice fusion failed.")
            return

        output_dir = os.path.join(self.main.repo_root, "generated", "registration_fusions")
        os.makedirs(output_dir, exist_ok=True)
        result_token = (record.scan_id or "result").replace("-", "")[:12]
        output_path = os.path.join(
            output_dir,
            f"pca_slice_fusion_{result_token}_z{int(fusion_result['target_native_z']):05d}.npy",
        )
        np.save(output_path, fusion_result["comparison_volume_zyx"], allow_pickle=False)

        volume_source = VolumeSource(
            path=output_path,
            source_type="npy",
            voxel_size_mm=float(fusion_result["target_voxel_size_mm"]),
            crop_zyx=None,
            default_downsample_zyx=1,
        )

        target_metrics = fusion_result["metrics_target_vs_registered"]
        fused_metrics = fusion_result["metrics_target_vs_fused"]
        pca_meta = fusion_result["pca"]
        metadata = {
            "Source registration": record.name,
            "Slice order Z": "0=PCA fused, 1=registered source, 2=target reference",
            "Target native z": int(fusion_result["target_native_z"]),
            "Result preview z": int(fusion_result["result_preview_z"]),
            "Target sample step": int(fusion_result["target_native_step"]),
            "Overlap pixels": int(fusion_result["valid_pixels"]),
            "Overlap fraction": f"{100.0 * fusion_result['valid_fraction']:.2f}%",
            "Fusion tiles": int(fusion_result["tile_stats"]["processed_tiles"]),
            "Max source tile voxels": int(fusion_result["tile_stats"]["max_region_voxels"]),
            "PCA weights (target, source)": f"{pca_meta['weights'][0]:.4f}, {pca_meta['weights'][1]:.4f}",
            "PCA eigenvalues": ", ".join(f"{float(v):.6g}" for v in pca_meta["eigenvalues"]),
            "Target vs registered SSIM": self._format_metric(target_metrics.get("ssim")),
            "Target vs registered Corr": self._format_metric(target_metrics.get("corrcoef")),
            "Target vs registered RMSE": self._format_metric(target_metrics.get("rmse")),
            "Target vs registered PSNR (dB)": self._format_metric(target_metrics.get("psnr_db")),
            "Target vs fused SSIM": self._format_metric(fused_metrics.get("ssim")),
            "Target vs fused Corr": self._format_metric(fused_metrics.get("corrcoef")),
            "Target vs fused RMSE": self._format_metric(fused_metrics.get("rmse")),
            "Target vs fused PSNR (dB)": self._format_metric(fused_metrics.get("psnr_db")),
            "Display gamma/contrast": f"{fusion_result['gamma']:.2f}, {fusion_result['contrast']:.2f}",
        }

        scan_id = self.main.add_scan_tab(
            name=f"PCA Slice Fusion z={int(fusion_result['target_native_z'])}",
            modality="pca-slice-fusion",
            path=output_path,
            voxel_size_mm=float(fusion_result["target_voxel_size_mm"]),
            volume_source=volume_source,
            metadata=metadata,
            make_current=True,
        )
        new_record = self.main.scans.get(scan_id)
        if new_record is not None and new_record.tab is not None:
            new_record.tab.enable_slice_viewer()
            new_record.tab.viewer_tabs.setCurrentIndex(1)

        self.main.statusbar.showMessage(
            "PCA slice fusion created for the current registered Z slice."
        )

    def _build_pca_slice_fusion(self, result_record, fusion_context):
        preview_metadata = self._current_result_preview_metadata(result_record)
        overlay_meta = fusion_context["fusion_volume_metadata"]
        transform = fusion_context["transform"]
        source_volume_source = fusion_context["source_volume_source"]
        target_volume_source = fusion_context["target_volume_source"]
        source_scan = fusion_context["source_scan"]
        target_scan = fusion_context["target_scan"]

        target_grid = self._result_preview_to_target_native_grid(
            result_record=result_record,
            preview_metadata=preview_metadata,
            overlay_meta=overlay_meta,
        )

        target_info = inspect_volume_source(target_volume_source)
        source_info = inspect_volume_source(source_volume_source)
        target_shape_zyx = tuple(int(v) for v in target_info["shape_zyx"])
        source_shape_zyx = tuple(int(v) for v in source_info["shape_zyx"])

        target_native_z = int(target_grid["target_native_z"])
        if target_native_z < 0 or target_native_z >= target_shape_zyx[0]:
            raise ValueError("The selected result slice maps outside the target volume bounds.")

        target_slice = load_volume_region_zyx(
            target_volume_source,
            z_slice=slice(target_native_z, target_native_z + 1),
            y_slice=target_grid["target_y_slice"],
            x_slice=target_grid["target_x_slice"],
        )[0]

        source_voxel_size_mm = self._scan_voxel_size_mm(source_scan, source_volume_source)
        target_voxel_size_mm = self._scan_voxel_size_mm(target_scan, target_volume_source)
        if source_voxel_size_mm <= 0.0 or target_voxel_size_mm <= 0.0:
            raise ValueError("Source/target voxel sizes must be positive for slice fusion.")

        grid_x_native, grid_y_native = np.meshgrid(
            target_grid["target_x_indices"],
            target_grid["target_y_indices"],
            indexing="xy",
        )
        grid_z_native = np.full(grid_x_native.shape, float(target_native_z), dtype=np.float32)
        target_world = np.stack(
            [
                grid_x_native * float(target_voxel_size_mm),
                grid_y_native * float(target_voxel_size_mm),
                grid_z_native * float(target_voxel_size_mm),
            ],
            axis=-1,
        ).reshape(-1, 3)

        inv_transform = np.linalg.inv(transform)
        source_world = target_world @ inv_transform[:3, :3].T + inv_transform[:3, 3]
        source_xyz = source_world / float(source_voxel_size_mm)

        src_x = source_xyz[:, 0].reshape(grid_x_native.shape)
        src_y = source_xyz[:, 1].reshape(grid_y_native.shape)
        src_z = source_xyz[:, 2].reshape(grid_z_native.shape)
        valid_mask = np.logical_and.reduce(
            [
                np.isfinite(src_x),
                np.isfinite(src_y),
                np.isfinite(src_z),
                src_x >= 0.0,
                src_y >= 0.0,
                src_z >= 0.0,
                src_x <= float(source_shape_zyx[2] - 1),
                src_y <= float(source_shape_zyx[1] - 1),
                src_z <= float(source_shape_zyx[0] - 1),
            ]
        )
        valid_pixels = int(np.count_nonzero(valid_mask))
        if valid_pixels < 8:
            raise ValueError("The selected result slice has too little source/target overlap for PCA fusion.")

        sampled_source, tile_stats = self._sample_registered_source_slice_tiled(
            source_volume_source=source_volume_source,
            source_shape_zyx=source_shape_zyx,
            src_x=src_x,
            src_y=src_y,
            src_z=src_z,
            valid_mask=valid_mask,
        )

        target_uint8 = normalize_image_uint8(target_slice)
        source_uint8 = normalize_image_uint8(sampled_source)
        fused_uint8, pca_meta = pca_fuse_images(
            target_uint8,
            source_uint8,
            valid_mask=valid_mask,
        )

        gamma, contrast = self._current_slice_enhancement(result_record)
        display_fused = apply_gamma_contrast_uint8(fused_uint8, gamma=gamma, contrast=contrast)
        display_source = apply_gamma_contrast_uint8(source_uint8, gamma=gamma, contrast=contrast)
        display_target = apply_gamma_contrast_uint8(target_uint8, gamma=gamma, contrast=contrast)
        comparison_volume_zyx = np.stack([display_fused, display_source, display_target], axis=0)

        return {
            "comparison_volume_zyx": comparison_volume_zyx.astype(np.uint8, copy=False),
            "metrics_target_vs_registered": compute_similarity_metrics(
                target_uint8,
                source_uint8,
                valid_mask=valid_mask,
            ),
            "metrics_target_vs_fused": compute_similarity_metrics(
                target_uint8,
                fused_uint8,
                valid_mask=valid_mask,
            ),
            "pca": pca_meta,
            "valid_pixels": valid_pixels,
            "valid_fraction": float(valid_pixels) / float(valid_mask.size),
            "target_native_z": target_native_z,
            "target_native_step": int(target_grid["target_native_step"]),
            "target_voxel_size_mm": float(target_voxel_size_mm),
            "result_preview_z": int(target_grid["result_preview_z"]),
            "gamma": float(gamma),
            "contrast": float(contrast),
            "tile_stats": tile_stats,
        }

    def _sample_registered_source_slice_tiled(
        self,
        source_volume_source,
        source_shape_zyx,
        src_x,
        src_y,
        src_z,
        valid_mask,
    ):
        sampled_source = np.zeros(src_x.shape, dtype=np.float32)
        tile_queue = []
        height, width = src_x.shape
        initial_tile = max(int(self.slice_fusion_min_tile_size), int(self.slice_fusion_initial_tile_size))
        for row0 in range(0, height, initial_tile):
            row1 = min(height, row0 + initial_tile)
            for col0 in range(0, width, initial_tile):
                col1 = min(width, col0 + initial_tile)
                tile_queue.append((row0, row1, col0, col1))

        processed_tiles = 0
        max_region_voxels = 0
        while tile_queue:
            row0, row1, col0, col1 = tile_queue.pop()
            tile_valid = valid_mask[row0:row1, col0:col1]
            if not np.any(tile_valid):
                continue

            bounds = self._source_bounds_for_tile(
                src_x=src_x[row0:row1, col0:col1],
                src_y=src_y[row0:row1, col0:col1],
                src_z=src_z[row0:row1, col0:col1],
                valid_mask=tile_valid,
                source_shape_zyx=source_shape_zyx,
            )
            region_voxels = int(bounds["region_voxels"])
            max_region_voxels = max(max_region_voxels, region_voxels)
            if region_voxels <= 0:
                continue

            tile_height = row1 - row0
            tile_width = col1 - col0
            if (
                region_voxels > int(self.max_slice_fusion_region_voxels)
                and (tile_height > int(self.slice_fusion_min_tile_size) or tile_width > int(self.slice_fusion_min_tile_size))
            ):
                if tile_width >= tile_height and tile_width > int(self.slice_fusion_min_tile_size):
                    mid = col0 + max(1, tile_width // 2)
                    if mid <= col0 or mid >= col1:
                        mid = col0 + tile_width // 2
                    tile_queue.append((row0, row1, col0, mid))
                    tile_queue.append((row0, row1, mid, col1))
                else:
                    mid = row0 + max(1, tile_height // 2)
                    if mid <= row0 or mid >= row1:
                        mid = row0 + tile_height // 2
                    tile_queue.append((row0, mid, col0, col1))
                    tile_queue.append((mid, row1, col0, col1))
                continue

            if region_voxels > int(self.max_slice_fusion_region_voxels):
                raise ValueError(
                    "The selected slice still requires an excessively deep source slab even after tiling. "
                    "Increase the preview downsample or reduce the crop before running PCA fusion."
                )

            source_region = load_volume_region_zyx(
                source_volume_source,
                z_slice=slice(bounds["z0"], bounds["z1"]),
                y_slice=slice(bounds["y0"], bounds["y1"]),
                x_slice=slice(bounds["x0"], bounds["x1"]),
            ).astype(np.float32, copy=False)

            tile_src_x = src_x[row0:row1, col0:col1]
            tile_src_y = src_y[row0:row1, col0:col1]
            tile_src_z = src_z[row0:row1, col0:col1]
            sampled_tile = map_coordinates(
                source_region,
                np.vstack(
                    [
                        (tile_src_z - float(bounds["z0"])).reshape(1, -1),
                        (tile_src_y - float(bounds["y0"])).reshape(1, -1),
                        (tile_src_x - float(bounds["x0"])).reshape(1, -1),
                    ]
                ),
                order=1,
                mode="constant",
                cval=0.0,
            ).reshape(tile_src_x.shape)
            sampled_tile = np.where(tile_valid, sampled_tile, 0.0)
            sampled_source[row0:row1, col0:col1] = sampled_tile.astype(np.float32, copy=False)
            processed_tiles += 1

        return sampled_source, {
            "processed_tiles": int(processed_tiles),
            "max_region_voxels": int(max_region_voxels),
        }

    @staticmethod
    def _source_bounds_for_tile(src_x, src_y, src_z, valid_mask, source_shape_zyx):
        z_floor = int(np.floor(np.min(src_z[valid_mask])))
        z_ceil = int(np.ceil(np.max(src_z[valid_mask])))
        y_floor = int(np.floor(np.min(src_y[valid_mask])))
        y_ceil = int(np.ceil(np.max(src_y[valid_mask])))
        x_floor = int(np.floor(np.min(src_x[valid_mask])))
        x_ceil = int(np.ceil(np.max(src_x[valid_mask])))

        z0 = max(0, z_floor - 1)
        y0 = max(0, y_floor - 1)
        x0 = max(0, x_floor - 1)
        z1 = min(int(source_shape_zyx[0]), z_ceil + 2)
        y1 = min(int(source_shape_zyx[1]), y_ceil + 2)
        x1 = min(int(source_shape_zyx[2]), x_ceil + 2)
        region_voxels = int(max(z1 - z0, 0) * max(y1 - y0, 0) * max(x1 - x0, 0))
        return {
            "z0": int(z0),
            "z1": int(z1),
            "y0": int(y0),
            "y1": int(y1),
            "x0": int(x0),
            "x1": int(x1),
            "region_voxels": int(region_voxels),
        }

    def _resolve_registration_fusion_context(self, result_record):
        metadata = getattr(result_record, "metadata", {}) or {}
        source_volume_source, _source_preview_downsample = self._resolve_role_export_spec(result_record, role="source")
        target_volume_source, _target_preview_downsample = self._resolve_role_export_spec(result_record, role="target")

        source_scan = self.main.scans.get(metadata.get("source_scan_id"))
        target_scan = self.main.scans.get(metadata.get("target_scan_id"))

        transform = metadata.get("icp_transformation")
        if transform is None:
            registration = getattr(self.main, "registration", None)
            if (
                registration is not None
                and getattr(registration, "result_scan_id", None) == result_record.scan_id
                and getattr(registration, "icp_result", None) is not None
            ):
                transform = np.asarray(registration.icp_result.transformation, dtype=float).tolist()

        fusion_volume_metadata = metadata.get("fusion_volume_metadata") or {}
        if not fusion_volume_metadata:
            registration = getattr(self.main, "registration", None)
            if (
                registration is not None
                and getattr(registration, "result_scan_id", None) == result_record.scan_id
                and getattr(registration, "icp_result", None) is not None
            ):
                _volume_source, fallback_meta = registration._build_fused_overlay_volume_source()
                if fallback_meta.get("fusion_method") == "registered volume overlay":
                    fusion_volume_metadata = fallback_meta

        if source_volume_source is None or target_volume_source is None:
            return {"error": "This result tab is missing its source/target volume references."}
        if transform is None:
            return {"error": "No ICP transformation matrix is stored on this result tab yet."}
        if fusion_volume_metadata.get("fusion_method") != "registered volume overlay":
            return {
                "error": (
                    "This result tab does not have an overlay-based registered volume preview. "
                    "PCA slice fusion needs the overlay preview so the current Z slice can be mapped back to the target stack."
                )
            }

        transform = np.asarray(transform, dtype=float)
        if transform.shape != (4, 4) or not np.isfinite(transform).all():
            return {"error": "The stored ICP transformation matrix is invalid."}

        return {
            "error": None,
            "source_volume_source": source_volume_source,
            "target_volume_source": target_volume_source,
            "source_scan": source_scan,
            "target_scan": target_scan,
            "transform": transform,
            "fusion_volume_metadata": fusion_volume_metadata,
        }

    def _current_result_preview_metadata(self, result_record):
        tab = getattr(result_record, "tab", None)
        if tab is None:
            raise ValueError("The selected result tab is missing its viewer state.")

        getter = getattr(tab, "get_volume_preview_metadata", None)
        preview_metadata = getter() if getter is not None else None
        if preview_metadata is None:
            raise ValueError(
                "Open the selected registration result tab and wait for its volume preview to finish loading before running PCA fusion."
            )
        return preview_metadata

    @staticmethod
    def _result_preview_to_target_native_grid(result_record, preview_metadata, overlay_meta):
        tab = getattr(result_record, "tab", None)
        slice_viewer = getattr(tab, "slice_viewer", None)
        if slice_viewer is None:
            raise ValueError("The selected result tab does not have a slice viewer.")

        slice_positions = slice_viewer.get_all_slice_positions()
        result_preview_z = int(slice_positions.get(2, (0, 0))[0])
        result_origin_zyx = tuple(int(v) for v in preview_metadata.get("crop_origin_zyx", (0, 0, 0)))
        result_step = max(1, int(preview_metadata.get("downsample_zyx", 1)))
        result_shape_zyx = tuple(int(v) for v in preview_metadata.get("crop_shape_zyx", (0, 0, 0)))
        if len(result_shape_zyx) != 3 or min(result_shape_zyx) <= 0:
            raise ValueError("The loaded result preview metadata is incomplete.")

        overlay_origin_zyx = tuple(int(v) for v in overlay_meta.get("target_crop_origin_zyx", (0, 0, 0)))
        overlay_step = max(1, int(overlay_meta.get("target_downsample_zyx", 1)))

        fused_preview_z = result_origin_zyx[0] + result_preview_z * result_step
        target_native_z = overlay_origin_zyx[0] + fused_preview_z * overlay_step
        target_native_step = result_step * overlay_step

        y_count = int(result_shape_zyx[1])
        x_count = int(result_shape_zyx[2])
        target_y_start = overlay_origin_zyx[1] + result_origin_zyx[1] * overlay_step
        target_x_start = overlay_origin_zyx[2] + result_origin_zyx[2] * overlay_step
        target_y_indices = target_y_start + target_native_step * np.arange(y_count, dtype=np.int64)
        target_x_indices = target_x_start + target_native_step * np.arange(x_count, dtype=np.int64)

        return {
            "result_preview_z": result_preview_z,
            "target_native_z": int(target_native_z),
            "target_native_step": int(target_native_step),
            "target_y_indices": target_y_indices.astype(np.float32, copy=False),
            "target_x_indices": target_x_indices.astype(np.float32, copy=False),
            "target_y_slice": slice(int(target_y_indices[0]), int(target_y_indices[-1]) + target_native_step, int(target_native_step)),
            "target_x_slice": slice(int(target_x_indices[0]), int(target_x_indices[-1]) + target_native_step, int(target_native_step)),
        }

    @staticmethod
    def _scan_voxel_size_mm(scan, volume_source):
        candidates = []
        if scan is not None and getattr(scan, "voxel_size_mm", None) is not None:
            candidates.append(scan.voxel_size_mm)
        if volume_source is not None and getattr(volume_source, "voxel_size_mm", None) is not None:
            candidates.append(volume_source.voxel_size_mm)

        for value in candidates:
            try:
                value = float(value)
            except Exception:
                continue
            if np.isfinite(value) and value > 0.0:
                return value
        return 0.0

    @staticmethod
    def _format_metric(value):
        if value is None:
            return "--"
        return f"{float(value):.6f}"

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
