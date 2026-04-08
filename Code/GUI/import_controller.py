import os
import numpy as np
from PySide6.QtWidgets import QMessageBox
from makeGeometry import VolumeSource, get_mesh_from_ct_stack, inspect_tiff_stack
from GUI.dialogs.xray_import_dialog import XRayImportDialog


class ImportController:
    """Handle the various "import" related actions that were cluttering the main
    window class.

    This includes the CT demo button, the X‑ray import dialog and file
    loading routines.  All state is kept on the owning window but the
    behaviours have been moved out to shrink ``main_window.py``.
    """

    def __init__(self, main_window):
        self.main = main_window

    def scan_reset(self):
        """Clear registration state while keeping imported scan tabs intact."""
        mw = self.main
        mw.registration.reset_state()
        mw.btn_prev_step.setEnabled(False)
        mw.btn_next_step.setEnabled(False)
        mw.progressBar.setValue(0)
        mw.label_ransac_fitness.setText("--")
        mw.label_ransac_rmse.setText("--")
        mw.label_icp_fitness.setText("--")
        mw.label_icp_rmse.setText("--")

    def ct_demo(self):
        """Generate and display a demo CT point cloud."""
        mw = self.main
        try:
            mw.statusbar.showMessage("Generating demo CT point cloud...")
            demo_folder = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '..', '..', '120kv_FDK')
            )

            mesh, level = get_mesh_from_ct_stack(
                folder_path=demo_folder,
                downsample_zyx=4,
                crop_zyx=(256, 256, 256),
                level=None,
            )
            volume_source = VolumeSource(
                folder_path=demo_folder,
                voxel_size_mm=None,
                crop_zyx=(256, 256, 256),
                default_downsample_zyx=4,
            )
            pcd = mesh.sample_points_poisson_disk(number_of_points=5000)

            print("MC level:", level)
            print("PCD points:", np.asarray(pcd.points).shape[0])
            print("Mesh verts:", np.asarray(mesh.vertices).shape[0])
            scan_id = mw.add_scan_tab(
                name=f"Demo CT {mw.scanTabs.count() + 1}",
                pcd=pcd,
                mesh=mesh,
                modality="ct-demo",
                path=demo_folder,
                volume_source=volume_source,
                metadata={
                    
                    "Points": np.asarray(pcd.points).shape[0],
                   
                    "Mesh source": "CT stack marching cubes",
                    "MC level": level,
                    "3D volume": "lazy preview available",
                },
            )
            if mw.source_scan_id is None:
                mw.source_scan_id = scan_id
                mw._sync_selection_ui()
            mw.registration.apply_suggested_ransac_parameters(show_status=False)

            mw.statusbar.showMessage("Demo CT point cloud generated and displayed.")

        except Exception as e:
            QMessageBox.critical(mw, "Error", str(e))
            mw.statusbar.showMessage("Error generating demo CT point cloud.")

    # ------------------------------------------------------------------
    # X-ray import helpers
    # ------------------------------------------------------------------

    def open_xray_dialog(self):
        dialog = XRayImportDialog(self.main)

        if dialog.exec():
            params = dialog.get_import_params()
            self.import_xray_data(params)

    def import_xray_data(self, params):
        mw = self.main
        if params.import_type == "tiff stack folder":
            self.load_tiff_stack(
                folder_path=params.path,
                voxel_size_mm=params.voxel_size_mm,
                roi_xyz=params.roi_xyz,
                downsampling=params.downsampling,
                pcd_points=params.pcd_points,
                level=params.level,
            )

        elif params.import_type == "h5":
            self.load_h5(params.path)

        elif params.import_type == "npy":
            self.load_npy(params.path)

        else:
            mw.statusbar.showMessage(f"Unknown import type: {params.import_type}")

    def load_h5(self, file_path):
        mw = self.main
        mw.statusbar.showMessage("H5 import not implemented yet.")
        print(f"[TODO] load_h5: {file_path}")

    def load_npy(self, file_path):
        mw = self.main
        mw.statusbar.showMessage("NPY import not implemented yet.")
        print(f"[TODO] load_npy: {file_path}")

    def load_tiff_stack(self, folder_path, voxel_size_mm, roi_xyz, downsampling, pcd_points, level=None):
        mw = self.main
        try:
            mw.statusbar.showMessage("Loading TIFF stack...")

            crop_zyx = (roi_xyz[2], roi_xyz[1], roi_xyz[0])
            stack_info = inspect_tiff_stack(folder_path)

            mesh, level = get_mesh_from_ct_stack(
                folder_path=folder_path,
                voxel_size_mm=voxel_size_mm,
                downsample_zyx=downsampling,
                crop_zyx=crop_zyx,
                level=level,
            )
            volume_source = VolumeSource(
                folder_path=folder_path,
                voxel_size_mm=voxel_size_mm,
                crop_zyx=crop_zyx,
                default_downsample_zyx=downsampling,
            )
            pcd = mesh.sample_points_poisson_disk(number_of_points=pcd_points)

            print("Imported TIFF stack from:", folder_path)
            print("Voxel size (mm):", voxel_size_mm)
            print("ROI XYZ:", roi_xyz)
            print("Crop ZYX:", crop_zyx)
            print("Downsampling:", downsampling)
            print("Point count:", pcd_points)
            print("MC level:", level)

            scan_id = mw.add_scan_tab(
                name=f"Imported CT {mw.scanTabs.count() + 1}",
                pcd=pcd,
                mesh=mesh,
                modality="xray-tiff-stack",
                path=folder_path,
                voxel_size_mm=voxel_size_mm,
                metadata={
                    "Voxel (mm)": voxel_size_mm,
                    "ROI XYZ": roi_xyz,
                    "Downsampling": downsampling,
                    "Points": pcd_points,
                    "Mesh source": "CT stack marching cubes",
                    "MC level": level,
                    "Stack shape ZYX": stack_info["shape_zyx"],
                    "Stack dtype": stack_info["dtype"],
                    "3D volume": "lazy preview available",
                },
                volume_source=volume_source,
            )
            if mw.source_scan_id is None:
                mw.source_scan_id = scan_id
            elif mw.target_scan_id is None:
                mw.target_scan_id = scan_id
            mw._sync_selection_ui()
            mw.registration.apply_suggested_ransac_parameters(show_status=False)

            mw.statusbar.showMessage("TIFF stack imported successfully.")

        except Exception as e:
            QMessageBox.critical(mw, "Import Error", str(e))
            mw.statusbar.showMessage("Error importing TIFF stack.")
