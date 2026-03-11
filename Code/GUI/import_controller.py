import os
import numpy as np
from PySide6.QtWidgets import QMessageBox
from makeGeometry import get_pcd_from_ct_stack
from Widgets.pointcloud_widget import PointCloudWidget
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
        """Clear any stored point clouds / results and restore the OpenGL widget. """
        mw = self.main
        mw.pcd1 = None
        mw.pcd2 = None
        mw.ransac_result = None
        mw.icp_result = None
        mw.current_step = 0

        mw._setup_opengl_widget()

        mw.btn_prev_step.setEnabled(False)
        mw.btn_next_step.setEnabled(False)

    def ct_demo(self):
        """Generate and display a demo CT point cloud."""
        mw = self.main
        try:
            mw.statusbar.showMessage("Generating demo CT point cloud...")
            demo_folder = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '..', '..', '120kv_FDK')
            )

            pcd, mesh, level = get_pcd_from_ct_stack(
                folder_path=demo_folder,
                downsample_zyx=4,
                crop_zyx=(256, 256, 256),
                level=None,
                n_points=5000,
            )

            print("MC level:", level)
            print("PCD points:", np.asarray(pcd.points).shape[0])
            print("Mesh verts:", np.asarray(mesh.vertices).shape[0])

            # reset previous state & widget
            self.scan_reset()
            mw.pcd1 = pcd
            mw.mesh1 = mesh

            geometry = mw.openGLWidget.geometry()
            parent = mw.openGLWidget.parent()
            mw.openGLWidget.setParent(None)
            mw.openGLWidget.deleteLater()

            mw.openGLWidget = PointCloudWidget(parent)
            mw.openGLWidget.setGeometry(geometry)
            mw.openGLWidget.show()

            mw.openGLWidget.add_point_cloud("Demo CT", pcd)
            mw.openGLWidget.update()

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

    def load_tiff_stack(self, folder_path, voxel_size_mm, roi_xyz, downsampling, pcd_points):
        mw = self.main
        try:
            mw.statusbar.showMessage("Loading TIFF stack...")

            crop_zyx = (roi_xyz[2], roi_xyz[1], roi_xyz[0])

            pcd, mesh, level = get_pcd_from_ct_stack(
                folder_path=folder_path,
                downsample_zyx=downsampling,
                crop_zyx=crop_zyx,
                level=None,
                n_points=pcd_points,
            )

            print("Imported TIFF stack from:", folder_path)
            print("Voxel size (mm):", voxel_size_mm)
            print("ROI XYZ:", roi_xyz)
            print("Crop ZYX:", crop_zyx)
            print("Downsampling:", downsampling)
            print("Point count:", pcd_points)
            print("MC level:", level)

            self.scan_reset()

            mw.pcd1 = pcd
            mw.mesh1 = mesh
            mw.voxel_size_mm = voxel_size_mm
            mw.import_path = folder_path
            mw.import_roi_xyz = roi_xyz
            mw.import_downsampling = downsampling
            mw.import_pcd_points = pcd_points

            geometry = mw.openGLWidget.geometry()
            parent = mw.openGLWidget.parent()

            mw.openGLWidget.setParent(None)
            mw.openGLWidget.deleteLater()

            mw.openGLWidget = PointCloudWidget(parent)
            mw.openGLWidget.setGeometry(geometry)
            mw.openGLWidget.show()

            mw.openGLWidget.add_point_cloud("Imported CT", pcd)
            mw.openGLWidget.update()

            mw.statusbar.showMessage("TIFF stack imported successfully.")

        except Exception as e:
            QMessageBox.critical(mw, "Import Error", str(e))
            mw.statusbar.showMessage("Error importing TIFF stack.")
