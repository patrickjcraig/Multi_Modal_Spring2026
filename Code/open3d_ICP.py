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
def run_RANSAC(pcd1_down, pcd2_down, pcd1_fpfh, pcd2_fpfh, voxel_size, 
               ransac_dist_multiplier=1.5, max_iterations=100000, validation_iterations=1000):
    distance_threshold = voxel_size * ransac_dist_multiplier
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
        o3d.pipelines.registration.RANSACConvergenceCriteria(max_iterations, validation_iterations),
    )
    return result


def run_ICP(pcd1, pcd2, initial_transform, voxel_size, icp_dist_multiplier=0.4):
    distance_threshold = voxel_size * icp_dist_multiplier
    result = o3d.pipelines.registration.registration_icp(
        pcd1,
        pcd2,
        distance_threshold,
        initial_transform,
        o3d.pipelines.registration.TransformationEstimationPointToPoint(),
    )
    return result

def run_full_registration(
    voxel_size=2.0,
    ransac_dist_multiplier=1.5,
    ransac_max_iter=100000,
    ransac_validation=1000,
    icp_dist_multiplier=0.4,
    icp_max_iter=50,
    source_pcd=None,
    target_pcd=None,
    step_callback=None,
    ransac_step=1,
    icp_step=1,
):
    """Run a full registration pipeline and optionally report intermediate steps.

    The behaviour is similar to the original function, but when a
    ``step_callback`` is provided the RANSAC and ICP stages are executed using
    the helpers in ``Registration/registration_steps.py``.  Those helpers
    repeatedly invoke Open3D with increasing iteration limits and call back
    for each increment.  ``step_callback`` is therefore called with three
    arguments: ``(stage, iteration, data)`` where ``stage`` is an integer
    (0=raw clouds, 1=ransac, 2=icp) and ``iteration`` is the cumulative
    iteration count within that stage.  ``data`` is a dictionary containing
    the objects produced at that iteration.

    The parameters ``ransac_step`` and ``icp_step`` control how often the
    callback occurs.  For example ``ransac_step=1000`` will report every
    thousandth RANSAC iteration.
    """
    # import here to avoid circular dependency
    from Registration import registration_steps

    if source_pcd is not None and target_pcd is not None:
        pcd1 = copy.deepcopy(source_pcd)
        pcd2 = copy.deepcopy(target_pcd)
        pcd1_down, pcd1_fpfh = preprocess_point_cloud(pcd1, voxel_size)
        pcd2_down, pcd2_fpfh = preprocess_point_cloud(pcd2, voxel_size)
    else:
        pcd1, pcd2, pcd1_down, pcd2_down, pcd1_fpfh, pcd2_fpfh = import_dataset(voxel_size)

    # stage 0: raw clouds
    if step_callback is not None:
        step_callback(0, 0, {"pcd1": pcd1, "pcd2": pcd2})

    # stage 1: ransac
    if step_callback is None:
        result_ransac = run_RANSAC(
            pcd1_down,
            pcd2_down,
            pcd1_fpfh,
            pcd2_fpfh,
            voxel_size,
            ransac_dist_multiplier,
            ransac_max_iter,
            ransac_validation,
        )
    else:
        def r_cb(it, res):
            step_callback(1, it, {"ransac": res, "total": ransac_max_iter})
        result_ransac = registration_steps.iterative_ransac(
            pcd1_down,
            pcd2_down,
            pcd1_fpfh,
            pcd2_fpfh,
            voxel_size,
            ransac_dist_multiplier,
            ransac_max_iter,
            ransac_validation,
            step=ransac_step,
            callback=r_cb,
        )

    # stage 2: icp
    if step_callback is None:
        result_icp = run_ICP(
            pcd1,
            pcd2,
            result_ransac.transformation,
            voxel_size,
            icp_dist_multiplier,
        )
    else:
        def i_cb(it, res):
            step_callback(2, it, {"icp": res, "total": icp_max_iter})
        result_icp = registration_steps.iterative_icp(
            pcd1,
            pcd2,
            result_ransac.transformation,
            voxel_size,
            icp_dist_multiplier,
            max_iterations=icp_max_iter,
            step=icp_step,
            callback=i_cb,
        )

    return {
        "pcd1": pcd1,
        "pcd2": pcd2,
        "ransac": result_ransac,
        "icp": result_icp,
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

        # create a single viewer window that will show both stages and a
        # progress bar in its status bar
        from GUI.icp_worker import PointCloudViewerWindow
        viewer = PointCloudViewerWindow()
        viewer.show()

        saved = {}
        def cb(stage, it, data):
            # store things we might need later (pcd1/pcd2, results)
            saved.update(data)
            total = data.get('total')
            viewer.update_stage(stage, it, total)

            if stage == 0:
                # raw clouds: show both original point clouds
                viewer.clear()
                viewer.add_point_cloud("Source", saved['pcd1'])
                viewer.add_point_cloud("Target", saved['pcd2'])
            elif stage == 1:
                # RANSAC iteration: transform source and redisplay
                import copy as _copy
                src = _copy.deepcopy(saved['pcd1'])
                src.transform(saved['ransac'].transformation)
                viewer.clear()
                viewer.add_point_cloud("Source", src)
                viewer.add_point_cloud("Target", saved['pcd2'])
            elif stage == 2:
                import copy as _copy
                src = _copy.deepcopy(saved['pcd1'])
                src.transform(saved['icp'].transformation)
                viewer.clear()
                viewer.add_point_cloud("Source", src)
                viewer.add_point_cloud("Target", saved['pcd2'])

        results = run_full_registration(
            voxel_size=voxel_size,
            step_callback=cb,
            ransac_step=1,
            icp_step=1,
        )
        # final result already displayed by callback, but keep reference
        print(results['icp'])
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
