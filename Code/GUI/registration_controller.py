import copy
import os
import numpy as np
from PySide6.QtCore import QObject

from GUI.icp_worker import ICPWorkerThread
from Utils.dataframe_utils import pcd_to_df, tf_to_df, reg_to_df


class RegistrationController(QObject):
    """Encapsulate all of the registration-related logic and UI updates.

    The controller holds the point cloud state and history as well as the
    callbacks that were previously implemented directly in
    ``main_window.AppTest``.  By moving the functionality here we keep the
    main window class focused on wiring widgets together and leave the heavy
    lifting in a smaller, testable helper object.
    """

    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self.max_display_points = 80000

        self.reset_state()

    def reset_state(self):
        # state owned by the controller
        self.step_history = []
        self.current_step = 0
        self.icp_thread = None
        self.result_scan_id = None
        self.source_scan = None
        self.target_scan = None
        self.global_transform_model = "rigid"
        self.global_stage_name = "Global RANSAC"
        self.local_stage_name = "Local ICP"
        self._display_source_mesh_base = None
        self._display_target_mesh_base = None
        self.pre_scale_context = None
        self.registration_voxel_size_used = None
        self.scale_diagnostics = None

    # ------------------------------------------------------------------
    # Public methods hooked to UI signals
    # ------------------------------------------------------------------

    def run_scan(self):
        """Start a registration run using values from the UI."""
        mw = self.main
        self.source_scan, self.target_scan = mw.get_registration_pair()

        if self.source_scan is None or self.target_scan is None:
            mw.statusbar.showMessage("Choose a source and target tab before running registration.")
            return

        if self.source_scan.scan_id == self.target_scan.scan_id:
            mw.statusbar.showMessage("Source and target scans must be different tabs.")
            return

        if self.source_scan.pcd is None or self.target_scan.pcd is None:
            mw.statusbar.showMessage("Both selected scans need point cloud data.")
            return

        mw.toolButton.setEnabled(False)
        mw.progressBar.setValue(0)

        # reset history and UI state
        self.step_history = []
        self.current_step = 0
        mw.btn_prev_step.setEnabled(False)
        mw.btn_next_step.setEnabled(False)

        # Clear previous results
        mw.label_ransac_fitness.setText("--")
        mw.label_ransac_rmse.setText("--")
        mw.label_icp_fitness.setText("--")
        mw.label_icp_rmse.setText("--")

        voxel_size = mw.spinBox_voxel_size.value()
        ransac_dist_mult = mw.spinBox_ransac_dist.value()
        ransac_max_iter = mw.spinBox_ransac_max_iter.value()
        ransac_validation = mw.spinBox_ransac_validation.value()
        icp_dist_mult = mw.spinBox_icp_dist.value()
        self.global_transform_model = mw.combo_global_transform_model.currentData() or "rigid"
        self.scale_diagnostics = self._registration_scale_diagnostics(self.source_scan, self.target_scan)
        source_spacing_mm = self._effective_spacing_mm(self.source_scan)
        target_spacing_mm = self._effective_spacing_mm(self.target_scan)
        if self.global_transform_model == "similarity":
            mw.label_ransac_rmse_label.setText("Inlier RMSE / Scale:")
        else:
            mw.label_ransac_rmse_label.setText("Inlier RMSE:")
        diag_note = ""
        if self.scale_diagnostics is not None:
            spacing_ratio = self.scale_diagnostics.get("spacing_ratio")
            extent_ratio = self.scale_diagnostics.get("extent_ratio")
            if spacing_ratio is not None:
                diag_note += f" | spacing ratio={float(spacing_ratio):.3f}"
            if extent_ratio is not None:
                diag_note += f" | bbox ratio={float(extent_ratio):.3f}"
        mw.statusbar.showMessage(
            f"Running {self._describe_global_stage()} -> {self.local_stage_name}: "
            f"{self.source_scan.name} -> {self.target_scan.name}{diag_note}"
        )

        if self.scale_diagnostics is not None:
            print("Registration scale diagnostics:", self.scale_diagnostics)

        self._display_source_mesh_base = self._prepare_display_mesh(
            self.source_scan.mesh if self.source_scan is not None else None
        )
        self._display_target_mesh_base = self._prepare_display_mesh(
            self.target_scan.mesh if self.target_scan is not None else None
        )

        result_volume_source = None
        if self.target_scan is not None and self.target_scan.volume_source is not None:
            result_volume_source = self.target_scan.volume_source
        elif self.source_scan is not None:
            result_volume_source = self.source_scan.volume_source

        self.result_scan_id = mw.add_scan_tab(
            name=f"Registration {self.source_scan.name} -> {self.target_scan.name}",
            modality="registration-result",
            is_result=True,
            volume_source=result_volume_source,
            metadata={
                "Source": self.source_scan.name,
                "Target": self.target_scan.name,
                "Global stage": self._describe_global_stage(),
                "Local stage": self.local_stage_name,
                "Pre-scale": "pending",
                "Scale diagnostics": self._format_scale_diagnostics(self.scale_diagnostics),
                "3D volume": "reference scan volume attached",
            },
        )

        self.icp_thread = ICPWorkerThread(
            voxel_size=voxel_size,
            ransac_dist_mult=ransac_dist_mult,
            ransac_max_iter=ransac_max_iter,
            ransac_validation=ransac_validation,
            icp_dist_mult=icp_dist_mult,
            source_pcd=self.source_scan.pcd,
            target_pcd=self.target_scan.pcd,
            global_transform_model=self.global_transform_model,
            source_spacing_mm=source_spacing_mm,
            target_spacing_mm=target_spacing_mm,
        )
        self.icp_thread.step.connect(self._on_registration_step)
        self.icp_thread.finished.connect(self._on_registration_complete)
        self.icp_thread.error.connect(self._on_registration_error)
        self.icp_thread.start()

    def suggest_ransac_parameters(self, source_scan=None, target_scan=None, global_transform_model=None):
        """Suggest registration parameters from imported scan metadata."""
        mw = self.main
        source_scan = source_scan or self.source_scan or mw.scans.get(mw.source_scan_id)
        target_scan = target_scan or self.target_scan or mw.scans.get(mw.target_scan_id)
        global_transform_model = global_transform_model or (mw.combo_global_transform_model.currentData() or "rigid")

        scans = [scan for scan in (source_scan, target_scan) if scan is not None]
        effective_spacings = []
        point_counts = []
        for scan in scans:
            spacing = self._effective_spacing_mm(scan)
            if spacing is not None:
                effective_spacings.append(spacing)

            if scan.pcd is not None:
                point_counts.append(len(np.asarray(scan.pcd.points)))
            else:
                point_count = scan.metadata.get("Points") if scan.metadata else None
                if point_count is not None:
                    point_counts.append(int(point_count))

        if effective_spacings:
            voxel_size = max(effective_spacings)
        else:
            voxel_size = mw.spinBox_voxel_size.value()

        bbox_diagonals = []
        for scan in scans:
            bbox = self._pcd_bbox_metrics(scan.pcd if scan is not None else None)
            if bbox is not None and np.isfinite(bbox["diagonal"]) and bbox["diagonal"] > 0:
                bbox_diagonals.append(float(bbox["diagonal"]))

        # Keep auto voxel physically meaningful relative to object size.
        if bbox_diagonals:
            min_diag = min(bbox_diagonals)
            min_reasonable = max(1e-5, 0.005 * min_diag)
            max_reasonable = max(min_reasonable, 0.08 * min_diag)
            voxel_size = float(np.clip(voxel_size, min_reasonable, max_reasonable))

        max_point_count = max(point_counts, default=5000)
        dist_multiplier = 1.5
        max_iterations = 40000

        if max_point_count >= 50000:
            max_iterations = 80000
        elif max_point_count >= 20000:
            max_iterations = 60000
        elif max_point_count >= 5000:
            max_iterations = 45000

        if global_transform_model == "similarity":
            dist_multiplier = 2.0
            max_iterations = int(max_iterations * 1.4)

        if len(effective_spacings) == 2:
            spacing_ratio = max(effective_spacings) / max(min(effective_spacings), 1e-9)
            if spacing_ratio > 1.25:
                dist_multiplier += 0.2
                max_iterations = int(max_iterations * 1.2)

        if len(bbox_diagonals) == 2:
            extent_ratio = max(bbox_diagonals) / max(min(bbox_diagonals), 1e-9)
            if extent_ratio > 1.15:
                dist_multiplier += 0.1
                max_iterations = int(max_iterations * 1.1)

        validation_iterations = max(1000, int(max_iterations * 0.02))
        validation_iterations = min(validation_iterations, 100000)

        voxel_size = float(np.clip(voxel_size, mw.spinBox_voxel_size.minimum(), mw.spinBox_voxel_size.maximum()))
        dist_multiplier = float(np.clip(dist_multiplier, mw.spinBox_ransac_dist.minimum(), mw.spinBox_ransac_dist.maximum()))
        max_iterations = int(np.clip(max_iterations, mw.spinBox_ransac_max_iter.minimum(), mw.spinBox_ransac_max_iter.maximum()))
        validation_iterations = int(np.clip(validation_iterations, mw.spinBox_ransac_validation.minimum(), mw.spinBox_ransac_validation.maximum()))

        return {
            "voxel_size": voxel_size,
            "ransac_dist_multiplier": dist_multiplier,
            "ransac_max_iter": max_iterations,
            "ransac_validation": validation_iterations,
        }

    def apply_suggested_ransac_parameters(self, source_scan=None, target_scan=None, show_status=False):
        suggestions = self.suggest_ransac_parameters(source_scan=source_scan, target_scan=target_scan)
        mw = self.main
        mw.spinBox_voxel_size.setValue(suggestions["voxel_size"])
        mw.spinBox_ransac_dist.setValue(suggestions["ransac_dist_multiplier"])
        mw.spinBox_ransac_max_iter.setValue(suggestions["ransac_max_iter"])
        mw.spinBox_ransac_validation.setValue(suggestions["ransac_validation"])

        if show_status:
            details = self._registration_scale_diagnostics(source_scan or self.source_scan, target_scan or self.target_scan)
            details_text = self._format_scale_diagnostics(details)
            mw.statusbar.showMessage(
                "Suggested registration parameters updated from scan spacing/size and RANSAC mode"
                + (f" | {details_text}" if details_text else "")
            )

    def prev_step(self):
        """Go back one entry in the history."""
        if self.current_step > 0:
            self.current_step -= 1
            self._display_registration_results()
            mw = self.main
            mw.btn_next_step.setEnabled(True)
            if self.current_step == 0:
                mw.btn_prev_step.setEnabled(False)

    def next_step(self):
        """Advance one entry in the history."""
        if self.current_step < len(self.step_history) - 1:
            self.current_step += 1
            self._display_registration_results()
            mw = self.main
            mw.btn_prev_step.setEnabled(True)
            if self.current_step == len(self.step_history) - 1:
                mw.btn_next_step.setEnabled(False)

    def save_dataframes(self):
        """Export the current data and results to CSV files."""
        mw = self.main
        if not hasattr(self, 'pcd1'):
            mw.statusbar.showMessage('No valid data is available.')
            return

        pcd1_df = pcd_to_df(self.pcd1)
        pcd2_df = pcd_to_df(self.pcd2)

        if getattr(self, 'icp_result', None) is not None:
            icp_tf_df = tf_to_df(self.icp_result)
            icp_df = reg_to_df(self.icp_result)
        else:
            import pandas as _pd
            icp_tf_df = _pd.DataFrame()
            icp_df = _pd.DataFrame()

        if getattr(self, 'ransac_result', None) is not None:
            ransac_tf_df = tf_to_df(self.ransac_result)
            ransac_df = reg_to_df(self.ransac_result)
        else:
            import pandas as _pd
            ransac_tf_df = _pd.DataFrame()
            ransac_df = _pd.DataFrame()

        code_dir = os.path.dirname(os.path.abspath(__file__))
        ws_dir = os.path.dirname(code_dir)
        base = os.path.join(ws_dir, 'TestData')
        os.makedirs(base, exist_ok=True)

        pcd1_df.to_csv(os.path.join(base, 'pcd1_raw.csv'), index=False)
        pcd2_df.to_csv(os.path.join(base, 'pcd2_raw.csv'), index=False)
        icp_tf_df.to_csv(os.path.join(base, 'icp_transform.csv'), index=False)
        icp_df.to_csv(os.path.join(base, 'icp_metadata.csv'), index=False)
        ransac_tf_df.to_csv(os.path.join(base, 'ransac_transform.csv'), index=False)
        ransac_df.to_csv(os.path.join(base, 'ransac_metadata.csv'), index=False)

        mw.statusbar.showMessage('The data has been saved successfully.')

    # ------------------------------------------------------------------
    # Internal callbacks and helpers
    # ------------------------------------------------------------------

    def _on_registration_complete(self, results):
        mw = self.main
        self.pcd1 = results.get('pcd1', getattr(self, 'pcd1', None))
        self.pcd2 = results.get('pcd2', getattr(self, 'pcd2', None))
        if results.get('ransac') is not None:
            self.ransac_result = results['ransac']
        if results.get('icp') is not None:
            self.icp_result = results['icp']
        self.global_transform_model = results.get("global_transform_model", self.global_transform_model)
        self.pre_scale_context = results.get("pre_scale")
        self.registration_voxel_size_used = results.get("registration_voxel_size")

        self._update_results_display()

        if self.step_history:
            self.current_step = len(self.step_history) - 1
        else:
            self.current_step = 0
        self._display_registration_results()

        mw.btn_prev_step.setEnabled(self.current_step > 0)
        mw.btn_next_step.setEnabled(False)

        mw.progressBar.setValue(100)
        if getattr(self, 'icp_result', None) is not None:
            voxel_note = ""
            if self.registration_voxel_size_used is not None:
                try:
                    requested = float(self.main.spinBox_voxel_size.value())
                    used = float(self.registration_voxel_size_used)
                    if used > requested:
                        voxel_note = f" | guard voxel: {used:.6g}"
                except Exception:
                    voxel_note = ""
            mw.statusbar.showMessage(
                '{} complete! Fitness: {:.6f}, RMSE: {:.6f}{}'.format(
                    self.local_stage_name,
                    self.icp_result.fitness, self.icp_result.inlier_rmse, voxel_note))
        else:
            mw.statusbar.showMessage('Registration complete!')

        mw.toolButton.setEnabled(True)

    def _update_results_display(self):
        mw = self.main
        if hasattr(self, 'ransac_result') and self.ransac_result is not None:
            mw.label_ransac_fitness.setText(f"{self.ransac_result.fitness:.6f}")
            details = [f"RMSE: {self.ransac_result.inlier_rmse:.6f}"]
            scale = self._extract_uniform_scale(self.ransac_result.transformation)
            if self.global_transform_model == "similarity":
                details.append(f"Scale: {scale:.6f}")
            mw.label_ransac_rmse.setText(" | ".join(details))
        else:
            mw.label_ransac_fitness.setText("--")
            mw.label_ransac_rmse.setText("--")

        if hasattr(self, 'icp_result') and self.icp_result is not None:
            mw.label_icp_fitness.setText(f"{self.icp_result.fitness:.6f}")
            mw.label_icp_rmse.setText(f"{self.icp_result.inlier_rmse:.6f}")
        else:
            mw.label_icp_fitness.setText("--")
            mw.label_icp_rmse.setText("--")

    def _on_registration_error(self, error_msg):
        mw = self.main
        mw.statusbar.showMessage(f'Error during registration: {error_msg}')
        mw.toolButton.setEnabled(True)

    def _on_registration_step(self, stage, iteration, data):
        mw = self.main
        # Keep exactly one snapshot per stage: raw, post-RANSAC, post-ICP.
        replaced = False
        for idx, (existing_stage, _existing_iter, _existing_data) in enumerate(self.step_history):
            if existing_stage == stage:
                self.step_history[idx] = (stage, iteration, data)
                replaced = True
                break
        if not replaced:
            self.step_history.append((stage, iteration, data))
            self.step_history.sort(key=lambda row: row[0])

        self.current_step = max(0, len(self.step_history) - 1)

        if stage == 0:
            self.pcd1 = data.get("pcd1")
            self.pcd2 = data.get("pcd2")
            self.pre_scale_context = data.get("pre_scale")
        elif stage == 1:
            self.ransac_result = data.get("ransac")
        elif stage == 2:
            self.icp_result = data.get("icp")

        self._display_registration_results()
        if 'ransac' in data or 'icp' in data:
            self._update_results_display()

        total = data.get('total', 1)
        if stage == 0:
            mw.progressBar.setValue(0)
            scale_text = ""
            if self.pre_scale_context and self.pre_scale_context.get("enabled"):
                scale_text = (
                    f" | pre-scale x{float(self.pre_scale_context.get('scale', 1.0)):.4f}"
                    f" ({self.pre_scale_context.get('method', 'unknown')})"
                )
            guard_text = ""
            guard_voxel = data.get("registration_voxel_size")
            if guard_voxel is not None:
                try:
                    requested = float(mw.spinBox_voxel_size.value())
                    used = float(guard_voxel)
                    if used > requested:
                        guard_text = f" | guard voxel {used:.6g}"
                except Exception:
                    guard_text = ""
            mw.statusbar.showMessage(f"Loaded point clouds{scale_text}{guard_text}")
            overlay = ""
        elif stage == 1:
            mw.progressBar.setValue(60)
            mw.statusbar.showMessage(f"{self.global_stage_name} complete")
            overlay = f"{self.global_stage_name} complete"
        elif stage == 2:
            mw.progressBar.setValue(100)
            mw.statusbar.showMessage(f"{self.local_stage_name} complete")
            overlay = f"{self.local_stage_name} complete"
        record = mw.scans.get(self.result_scan_id)
        if record is not None:
            record.tab.viewer.set_overlay_text(overlay)

        mw.btn_prev_step.setEnabled(self.current_step > 0)
        mw.btn_next_step.setEnabled(self.current_step < len(self.step_history) - 1)

    def _display_registration_results(self):
        mw = self.main
        source_temp = self._prepare_display_cloud(self.pcd1)
        target_temp = self._prepare_display_cloud(self.pcd2)
        source_temp.paint_uniform_color([1.0, 0.706, 0.0])
        target_temp.paint_uniform_color([0.0, 0.651, 0.929])

        source_mesh_temp = copy.deepcopy(self._display_source_mesh_base) if self._display_source_mesh_base is not None else None
        target_mesh_temp = copy.deepcopy(self._display_target_mesh_base) if self._display_target_mesh_base is not None else None

        if self.step_history:
            stage, iteration, payload = self.step_history[self.current_step]
        else:
            stage, iteration, payload = 0, 0, {}

        if stage == 0:
            mw.label_step_info.setText("Raw point clouds")
        elif stage == 1:
            trans = payload.get('ransac').transformation if payload.get('ransac') else None
            if trans is not None:
                source_temp.transform(trans)
                if source_mesh_temp is not None:
                    source_mesh_temp.transform(trans)
            mw.label_step_info.setText(f"{self._describe_global_stage()} complete")
        elif stage == 2:
            trans = payload.get('icp').transformation if payload.get('icp') else None
            if trans is not None:
                source_temp.transform(trans)
                if source_mesh_temp is not None:
                    source_mesh_temp.transform(trans)
            mw.label_step_info.setText(f"{self.local_stage_name} complete")

        meshes = []
        if source_mesh_temp is not None:
            meshes.append(("Source Mesh", source_mesh_temp, (1.0, 0.706, 0.0)))
        if target_mesh_temp is not None:
            meshes.append(("Target Mesh", target_mesh_temp, (0.0, 0.651, 0.929)))

        info_text = " | ".join([
            f"Registration result",
            f"Source: {self.source_scan.name if self.source_scan else 'Unknown'}",
            f"Target: {self.target_scan.name if self.target_scan else 'Unknown'}",
            f"Global: {self._describe_global_stage()}",
            f"Local: {self.local_stage_name}",
            f"Stage: {mw.label_step_info.text()}",
        ])
        if self.pre_scale_context and self.pre_scale_context.get("enabled"):
            info_text += (
                f" | Pre-scale: x{float(self.pre_scale_context.get('scale', 1.0)):.6f}"
                f" ({self.pre_scale_context.get('method', 'unknown')})"
            )
        if self.scale_diagnostics is not None:
            info_text += f" | Scale diagnostics: {self._format_scale_diagnostics(self.scale_diagnostics)}"
        if stage == 1 and payload.get("ransac") is not None and self.global_transform_model == "similarity":
            info_text += f" | Global scale: {self._extract_uniform_scale(payload['ransac'].transformation):.6f}"
        elif stage == 2 and payload.get("icp") is not None and self.global_transform_model == "similarity":
            info_text += f" | Current scale: {self._extract_uniform_scale(payload['icp'].transformation):.6f}"
        mw.update_scan_tab(
            self.result_scan_id,
            info_text=info_text,
            point_clouds=[
                ("Source", source_temp, None),
                ("Target", target_temp, None),
            ],
            meshes=meshes,
        )

    def _describe_global_stage(self):
        if self.global_transform_model == "similarity":
            return f"{self.global_stage_name} (Similarity / uniform scale)"
        return f"{self.global_stage_name} (Rigid)"

    @staticmethod
    def _extract_uniform_scale(transformation):
        linear = np.asarray(transformation, dtype=float)[:3, :3]
        column_norms = np.linalg.norm(linear, axis=0)
        return float(np.mean(column_norms))

    def _prepare_display_cloud(self, pcd):
        cloud = copy.deepcopy(pcd)
        point_count = len(np.asarray(cloud.points))
        if point_count <= self.max_display_points:
            return cloud

        keep_ratio = float(self.max_display_points) / float(max(point_count, 1))
        keep_ratio = max(0.0001, min(1.0, keep_ratio))
        return cloud.random_down_sample(keep_ratio)

    def _prepare_display_mesh(self, mesh, max_triangles=120000):
        if mesh is None:
            return None

        prepared = copy.deepcopy(mesh)
        try:
            triangle_count = len(np.asarray(prepared.triangles))
            if triangle_count > int(max_triangles):
                prepared = prepared.simplify_quadric_decimation(int(max_triangles))
            prepared.compute_vertex_normals()
        except Exception:
            return copy.deepcopy(mesh)
        return prepared

    @staticmethod
    def _effective_spacing_mm(scan):
        if scan is None or scan.voxel_size_mm is None:
            return None

        downsampling = 1
        if getattr(scan, "volume_source", None) is not None:
            downsampling = max(1, int(getattr(scan.volume_source, "default_downsample_zyx", 1)))
        elif scan.metadata:
            downsampling = max(1, int(scan.metadata.get("Downsampling", 1)))

        return float(scan.voxel_size_mm) * float(downsampling)

    @staticmethod
    def _pcd_bbox_metrics(pcd):
        if pcd is None:
            return None
        pts = np.asarray(pcd.points, dtype=float)
        if pts.ndim != 2 or pts.shape[0] < 3 or pts.shape[1] != 3:
            return None
        mins = np.min(pts, axis=0)
        maxs = np.max(pts, axis=0)
        extents = maxs - mins
        return {
            "extent_x": float(extents[0]),
            "extent_y": float(extents[1]),
            "extent_z": float(extents[2]),
            "diagonal": float(np.linalg.norm(extents)),
        }

    def _registration_scale_diagnostics(self, source_scan, target_scan):
        if source_scan is None or target_scan is None:
            return None

        src_spacing = self._effective_spacing_mm(source_scan)
        dst_spacing = self._effective_spacing_mm(target_scan)
        src_bbox = self._pcd_bbox_metrics(source_scan.pcd)
        dst_bbox = self._pcd_bbox_metrics(target_scan.pcd)

        spacing_ratio = None
        if src_spacing is not None and dst_spacing is not None and src_spacing > 0 and dst_spacing > 0:
            spacing_ratio = float(max(src_spacing, dst_spacing) / max(min(src_spacing, dst_spacing), 1e-9))

        extent_ratio = None
        if src_bbox is not None and dst_bbox is not None:
            d1 = float(src_bbox["diagonal"])
            d2 = float(dst_bbox["diagonal"])
            if d1 > 0 and d2 > 0 and np.isfinite(d1) and np.isfinite(d2):
                extent_ratio = float(max(d1, d2) / max(min(d1, d2), 1e-9))

        diagnostics = {
            "source_spacing_mm": None if src_spacing is None else float(src_spacing),
            "target_spacing_mm": None if dst_spacing is None else float(dst_spacing),
            "spacing_ratio": spacing_ratio,
            "source_bbox": src_bbox,
            "target_bbox": dst_bbox,
            "extent_ratio": extent_ratio,
        }
        return diagnostics

    @staticmethod
    def _format_scale_diagnostics(diagnostics):
        if diagnostics is None:
            return ""
        chunks = []
        src_spacing = diagnostics.get("source_spacing_mm")
        dst_spacing = diagnostics.get("target_spacing_mm")
        spacing_ratio = diagnostics.get("spacing_ratio")
        extent_ratio = diagnostics.get("extent_ratio")
        if src_spacing is not None and dst_spacing is not None:
            chunks.append(f"spacing(mm) src={src_spacing:.6g} tgt={dst_spacing:.6g}")
        if spacing_ratio is not None:
            chunks.append(f"spacing_ratio={float(spacing_ratio):.3f}")
        if extent_ratio is not None:
            chunks.append(f"bbox_ratio={float(extent_ratio):.3f}")
        return " | ".join(chunks)
