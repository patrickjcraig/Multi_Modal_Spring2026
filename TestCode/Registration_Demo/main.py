import argparse
import sys
import numpy as np

from PySide6.QtWidgets import QApplication

from Drivers.geometry import get_pcd_from_ct_stack
from Drivers.transforms import (
    make_affine_matrix,
    apply_affine_to_pcd,
    crop_partial_point_cloud,
)
from Drivers.registration import run_ransac_registration
from Drivers.scene_adapter import pcd_to_gl_data, apply_transform_to_gl_object
from Shaders.gl_scene import GLSceneObject
from Shaders.gl_viewer import GLViewer


def parse_args():
    parser = argparse.ArgumentParser(
        description="RANSAC affine registration testbed with PySide6 + PyOpenGL viewer"
    )

    parser.add_argument("--ct-folder", type=str, required=True, help="Path to TIFF stack folder")
    parser.add_argument("--voxel-size-mm", type=float, default=0.0004631795192807952, help="Voxel size in mm")

    parser.add_argument("--downsample", type=int, default=4, help="Downsample factor in z,y,x")
    parser.add_argument("--mc-level", type=float, default=None, help="Marching cubes iso-level")
    parser.add_argument("--n-points", type=int, default=5000, help="Poisson sampled points")

    # ROI size only, starting from 0,0,0
    parser.add_argument("--roi-sx", type=int, default=512)
    parser.add_argument("--roi-sy", type=int, default=512)
    parser.add_argument("--roi-sz", type=int, default=512)

    # Synthetic affine transform
    parser.add_argument("--rot-x-deg", type=float, default=0.0)
    parser.add_argument("--rot-y-deg", type=float, default=0.0)
    parser.add_argument("--rot-z-deg", type=float, default=15.0)

    parser.add_argument("--scale-x", type=float, default=1.0)
    parser.add_argument("--scale-y", type=float, default=1.0)
    parser.add_argument("--scale-z", type=float, default=1.0)

    parser.add_argument("--shift-x", type=float, default=0.0, help="Translation in mm")
    parser.add_argument("--shift-y", type=float, default=0.0, help="Translation in mm")
    parser.add_argument("--shift-z", type=float, default=0.0, help="Translation in mm")

    parser.add_argument("--partial", action="store_true", help="Crop transformed cloud for partial overlap")
    parser.add_argument("--partial-ratio", type=float, default=0.5, help="Fraction kept in x slab")

    # Registration
    parser.add_argument("--feature-voxel", type=float, default=0.02, help="FPFH preprocessing voxel size")
    parser.add_argument("--ransac-distance", type=float, default=0.05, help="RANSAC correspondence threshold")
    parser.add_argument("--max-iter", type=int, default=100000, help="RANSAC max iterations")
    parser.add_argument("--confidence", type=float, default=0.999, help="RANSAC confidence")

    return parser.parse_args()


def main():
    args = parse_args()

    roi_size_zyx = (
        args.roi_sz,
        args.roi_sy,
        args.roi_sx,
    )

    source_pcd, source_mesh, used_level = get_pcd_from_ct_stack(
        folder_path=args.ct_folder,
        voxel_size_mm=args.voxel_size_mm,
        downsample_zyx=args.downsample,
        roi_size_zyx=roi_size_zyx,
        level=args.mc_level,
        n_points=args.n_points,
    )

    print(f"Source mesh vertices: {np.asarray(source_mesh.vertices).shape[0]}")
    print(f"Source cloud points: {np.asarray(source_pcd.points).shape[0]}")

    gt_affine = make_affine_matrix(
        rotation_deg=(args.rot_x_deg, args.rot_y_deg, args.rot_z_deg),
        scale=(args.scale_x, args.scale_y, args.scale_z),
        translation=(args.shift_x, args.shift_y, args.shift_z),
    )

    target_pcd = apply_affine_to_pcd(source_pcd, gt_affine)

    if args.partial:
        target_pcd = crop_partial_point_cloud(target_pcd, keep_ratio=args.partial_ratio)
        print(f"Partial target cloud points: {np.asarray(target_pcd.points).shape[0]}")

    result, debug = run_ransac_registration(
        source=source_pcd,
        target=target_pcd,
        voxel_size=args.feature_voxel,
        distance_threshold=args.ransac_distance,
        max_iteration=args.max_iter,
        confidence=args.confidence,
    )

    print("\n=== Registration Result ===")
    print("Fitness:", result.fitness)
    print("Inlier RMSE:", result.inlier_rmse)
    print("Ground truth transform:\n", gt_affine)
    print("Estimated transform:\n", result.transformation)

    source_gl = pcd_to_gl_data(source_pcd, color=(1.0, 0.0, 0.0))
    target_gl = pcd_to_gl_data(target_pcd, color=(0.0, 1.0, 0.0))
    aligned_source_gl = apply_transform_to_gl_object(source_gl, result.transformation)

    source_obj = GLSceneObject(
        name="aligned_source",
        positions=aligned_source_gl["positions"],
        colors=aligned_source_gl["colors"],
        point_size=4.0,
        visible=True,
    )

    target_obj = GLSceneObject(
        name="target",
        positions=target_gl["positions"],
        colors=target_gl["colors"],
        point_size=4.0,
        visible=True,
    )

    app = QApplication(sys.argv)
    viewer = GLViewer()
    viewer.setWindowTitle("PyOpenGL Registration Viewer")
    viewer.resize(1200, 800)
    viewer.set_scene_objects([source_obj, target_obj])
    viewer.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()