import copy
import os
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

        self.reset_state()

    def reset_state(self):
        # state owned by the controller
        self.step_history = []
        self.current_step = 0
        self.icp_thread = None
        self.result_scan_id = None
        self.source_scan = None
        self.target_scan = None

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
        mw.statusbar.showMessage(
            f"Currently running ICP registration: {self.source_scan.name} -> {self.target_scan.name}"
        )

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

        self.result_scan_id = mw.add_scan_tab(
            name=f"Registration {self.source_scan.name} -> {self.target_scan.name}",
            modality="registration-result",
            is_result=True,
            metadata={"Source": self.source_scan.name, "Target": self.target_scan.name},
        )

        self.icp_thread = ICPWorkerThread(
            voxel_size=voxel_size,
            ransac_dist_mult=ransac_dist_mult,
            ransac_max_iter=ransac_max_iter,
            ransac_validation=ransac_validation,
            icp_dist_mult=icp_dist_mult,
            source_pcd=self.source_scan.pcd,
            target_pcd=self.target_scan.pcd,
        )
        self.icp_thread.step.connect(self._on_registration_step)
        self.icp_thread.finished.connect(self._on_registration_complete)
        self.icp_thread.error.connect(self._on_registration_error)
        self.icp_thread.start()

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
            mw.statusbar.showMessage(
                'Registration complete! Fitness: {:.6f}, RMSE: {:.6f}'.format(
                    self.icp_result.fitness, self.icp_result.inlier_rmse))
        else:
            mw.statusbar.showMessage('Registration complete!')

        mw.toolButton.setEnabled(True)

    def _update_results_display(self):
        mw = self.main
        if hasattr(self, 'ransac_result') and self.ransac_result is not None:
            mw.label_ransac_fitness.setText(f"{self.ransac_result.fitness:.6f}")
            mw.label_ransac_rmse.setText(f"{self.ransac_result.inlier_rmse:.6f}")
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
        self.step_history.append((stage, iteration, data))
        self.current_step = len(self.step_history) - 1

        if stage == 0:
            self.pcd1 = data.get("pcd1")
            self.pcd2 = data.get("pcd2")
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
            mw.statusbar.showMessage("Loaded point clouds")
            overlay = ""
        elif stage == 1:
            pct = int(iteration / total * 100) if total else 0
            mw.progressBar.setValue(pct)
            mw.statusbar.showMessage(f"RANSAC {iteration}/{total}")
            overlay = f"RANSAC {iteration}/{total}"
        elif stage == 2:
            pct = int(iteration / total * 100) if total else 0
            mw.progressBar.setValue(pct)
            mw.statusbar.showMessage(f"ICP {iteration}/{total}")
            overlay = f"ICP {iteration}/{total}"
        record = mw.scans.get(self.result_scan_id)
        if record is not None:
            record.tab.viewer.set_overlay_text(overlay)

        mw.btn_prev_step.setEnabled(self.current_step > 0)
        mw.btn_next_step.setEnabled(self.current_step < len(self.step_history) - 1)

    def _display_registration_results(self):
        mw = self.main
        source_temp = copy.deepcopy(self.pcd1)
        target_temp = copy.deepcopy(self.pcd2)
        source_temp.paint_uniform_color([1.0, 0.706, 0.0])
        target_temp.paint_uniform_color([0.0, 0.651, 0.929])

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
            total = payload.get('total', '?')
            mw.label_step_info.setText(f"RANSAC {iteration}/{total}")
        elif stage == 2:
            trans = payload.get('icp').transformation if payload.get('icp') else None
            if trans is not None:
                source_temp.transform(trans)
            total = payload.get('total', '?')
            mw.label_step_info.setText(f"ICP {iteration}/{total}")

        info_text = " | ".join([
            f"Registration result",
            f"Source: {self.source_scan.name if self.source_scan else 'Unknown'}",
            f"Target: {self.target_scan.name if self.target_scan else 'Unknown'}",
            f"Stage: {mw.label_step_info.text()}",
        ])
        mw.update_scan_tab(
            self.result_scan_id,
            info_text=info_text,
            point_clouds=[
                ("Source", source_temp, None),
                ("Target", target_temp, None),
            ],
        )
