import copy
import open3d as o3d


def preprocess_point_cloud(pcd, voxel_size):
    pcd_down = copy.deepcopy(pcd).voxel_down_sample(voxel_size)

    normal_radius = voxel_size * 2.0
    feature_radius = voxel_size * 5.0

    pcd_down.estimate_normals(
        o3d.geometry.KDTreeSearchParamHybrid(radius=normal_radius, max_nn=30)
    )

    fpfh = o3d.pipelines.registration.compute_fpfh_feature(
        pcd_down,
        o3d.geometry.KDTreeSearchParamHybrid(radius=feature_radius, max_nn=100),
    )

    return pcd_down, fpfh


def run_ransac_registration(
    source,
    target,
    voxel_size=0.02,
    distance_threshold=0.05,
    max_iteration=100000,
    confidence=0.999,
    mutual_filter=False,
):
    source_down, source_fpfh = preprocess_point_cloud(source, voxel_size)
    target_down, target_fpfh = preprocess_point_cloud(target, voxel_size)

    result = o3d.pipelines.registration.registration_ransac_based_on_feature_matching(
        source_down,
        target_down,
        source_fpfh,
        target_fpfh,
        mutual_filter=bool(mutual_filter),
        max_correspondence_distance=distance_threshold,
        estimation_method=o3d.pipelines.registration.TransformationEstimationPointToPoint(False),
        ransac_n=4,
        checkers=[
            o3d.pipelines.registration.CorrespondenceCheckerBasedOnEdgeLength(0.9),
            o3d.pipelines.registration.CorrespondenceCheckerBasedOnDistance(distance_threshold),
        ],
        criteria=o3d.pipelines.registration.RANSACConvergenceCriteria(
            max_iteration,
            confidence,
        ),
    )

    debug = {
        "source_down": source_down,
        "target_down": target_down,
        "source_fpfh": source_fpfh,
        "target_fpfh": target_fpfh,
    }

    return result, debug