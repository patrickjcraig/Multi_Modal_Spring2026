# open3d ICP
# https://www.open3d.org/docs/latest/tutorial/pipelines/icp_registration.html
import copy
import open3d as o3d
import numpy as np
from makeGeometry import get_pcd_from_stl

# Draws the point clouds after registration for the ICP and RANSAC steps
def draw_registration_result(source, target, transformation):
    source_temp = copy.deepcopy(source)
    target_temp = copy.deepcopy(target)
    source_temp.paint_uniform_color([1.0, 0.706, 0.0])
    target_temp.paint_uniform_color([0.0, 0.651, 0.929])
    source_temp.transform(transformation)
    
    # Use OpenGL renderer if available
    try:
        from test import PointCloudViewerWindow
        viewer = PointCloudViewerWindow()
        viewer.add_point_cloud("Source", source_temp)
        viewer.add_point_cloud("Target", target_temp)
        viewer.show()
    except ImportError:
        # Fallback to open3d visualization
        o3d.visualization.draw([source_temp, target_temp])

# Preprocesses the point cloud by downsampling, estimating normals, and computing FPFH features
def preprocess_point_cloud(pcd, voxel_size):
    pcd_down = pcd.voxel_down_sample(voxel_size)
    pcd_down.estimate_normals(
        o3d.geometry.KDTreeSearchParamHybrid(radius=voxel_size * 2.0, max_nn=30)
    )
    fpfh = o3d.pipelines.registration.compute_fpfh_feature(
        pcd_down,
        o3d.geometry.KDTreeSearchParamHybrid(radius=voxel_size * 5.0, max_nn=100),
    )
    return pcd_down, fpfh

# Imports the point clouds, applies transformations to one of them, and runs preprocessing
def import_dataset(voxel_size):
    pcd1 = get_pcd_from_stl()
    pcd2 = get_pcd_from_stl()

    pcd2.translate([100, 100, 100])
    pcd2.rotate(o3d.geometry.get_rotation_matrix_from_xyz((0.2, 0.2, 0.2)))

    pcd1_down, pcd1_fpfh = preprocess_point_cloud(pcd1, voxel_size)
    pcd2_down, pcd2_fpfh = preprocess_point_cloud(pcd2, voxel_size)

    return pcd1, pcd2, pcd1_down, pcd2_down, pcd1_fpfh, pcd2_fpfh

# RANSAC 
def run_RANSAC(pcd1_down, pcd2_down, pcd1_fpfh, pcd2_fpfh, voxel_size):
    distance_threshold = voxel_size * 1.5
    result = o3d.pipelines.registration.registration_ransac_based_on_feature_matching(
        pcd1_down,
        pcd2_down,
        pcd1_fpfh,
        pcd2_fpfh,
        True,
        distance_threshold,
        o3d.pipelines.registration.TransformationEstimationPointToPoint(False),
        4,
        [
            o3d.pipelines.registration.CorrespondenceCheckerBasedOnEdgeLength(0.9),
            o3d.pipelines.registration.CorrespondenceCheckerBasedOnDistance(distance_threshold),
        ],
        o3d.pipelines.registration.RANSACConvergenceCriteria(100000, 1000),
    )
    return result


def run_ICP(pcd1, pcd2, initial_transform, voxel_size):
    distance_threshold = voxel_size * 0.4
    result = o3d.pipelines.registration.registration_icp(
        pcd1,
        pcd2,
        distance_threshold,
        initial_transform,
        o3d.pipelines.registration.TransformationEstimationPointToPoint(),
    )
    return result

def run_full_registration(voxel_size=2.0): # adding callable function for UI to interact with
    pcd1, pcd2, pcd1_down, pcd2_down, pcd1_fpfh, pcd2_fpfh = import_dataset(voxel_size)

    result_ransac = run_RANSAC(
        pcd1_down, pcd2_down, pcd1_fpfh, pcd2_fpfh, voxel_size
    )

    result_icp = run_ICP(
        pcd1, pcd2, result_ransac.transformation, voxel_size
    )

    return {
        "pcd1": pcd1,
        "pcd2": pcd2,
        "ransac": result_ransac,
        "icp": result_icp
    }

if __name__ == "__main__": # this is so this does not run until the main window is open, allows this to be imported into test.py
    import sys
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QSurfaceFormat
    
    # Configure OpenGL surface format
    format = QSurfaceFormat()
    format.setSamples(4)
    format.setMajorVersion(4)
    format.setMinorVersion(1)
    format.setProfile(QSurfaceFormat.CoreProfile)
    format.setDepthBufferSize(24)
    QSurfaceFormat.setDefaultFormat(format)
    
    app = QApplication(sys.argv)
    
    # Try to load real data, fallback to synthetic if file doesn't exist
    try:
        voxel_size = 2.0
        pcd1, pcd2, pcd1_down, pcd2_down, pcd1_fpfh, pcd2_fpfh = import_dataset(voxel_size)

        result_ransac = run_RANSAC(pcd1_down, pcd2_down, pcd1_fpfh, pcd2_fpfh, voxel_size)
        result_icp = run_ICP(pcd1, pcd2, result_ransac.transformation, voxel_size)

        print(result_icp)
        
        # Visualize with OpenGL
        draw_registration_result(pcd1, pcd2, result_icp.transformation)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"Could not load real data: {e}")
        print("Creating synthetic point clouds for testing...")
        
        # Create synthetic point clouds for testing
        from test import PointCloudViewerWindow
        
        # Create a simple cube point cloud
        pcd1 = o3d.geometry.PointCloud()
        pcd1.points = o3d.utility.Vector3dVector(np.random.rand(2000, 3) * 100 - 50)
        pcd1.paint_uniform_color([1.0, 0.706, 0.0])
        
        pcd2 = o3d.geometry.PointCloud()
        pcd2.points = o3d.utility.Vector3dVector(np.random.rand(2000, 3) * 100 - 50)
        pcd2.paint_uniform_color([0.0, 0.651, 0.929])
        
        # Show the synthetic clouds
        viewer = PointCloudViewerWindow()
        viewer.add_point_cloud("Cloud 1", pcd1)
        viewer.add_point_cloud("Cloud 2", pcd2)
        viewer.show()
    
    sys.exit(app.exec())



# Scaling, point cloud normalization,
# Basic UI stack, writing paper (overleaf doc)
# "Slice of missing data" demonstration with scaling