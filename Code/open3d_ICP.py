# open3d ICP
# https://www.open3d.org/docs/latest/tutorial/pipelines/icp_registration.html
import copy
import open3d as o3d
import numpy as np
from makeGeometry import get_pcd_from_stl
from Registration.scale_estimation import estimate_global_scale


GLOBAL_TRANSFORM_RIGID = "rigid"
GLOBAL_TRANSFORM_SIMILARITY = "similarity"
MAX_REGISTRATION_POINTS = 120_000
MAX_FEATURE_POINTS = 60_000
SIMILARITY_PRESCALE_MIN = 0.80
SIMILARITY_PRESCALE_MAX = 1.25
SIMILARITY_LOW_CONFIDENCE_DAMPING = 0.35
SIMILARITY_MIN_CONFIDENCE_FULL_APPLY = 0.45
SPACING_PRESCALE_MIN = 0.70
SPACING_PRESCALE_MAX = 1.50
SPACING_PRESCALE_TRIGGER = 0.02


def uses_uniform_scaling(global_transform_model):
    return global_transform_model == GLOBAL_TRANSFORM_SIMILARITY


def _extract_uniform_scale(transformation):
    linear = np.asarray(transformation, dtype=float)[:3, :3]
    column_norms = np.linalg.norm(linear, axis=0)
    return float(np.mean(column_norms))


def _transform_is_finite(transformation):
    t = np.asarray(transformation, dtype=float)
    return t.shape == (4, 4) and bool(np.all(np.isfinite(t)))


def _resolve_ransac_confidence(validation_iterations):
    """Map legacy UI input to Open3D's confidence parameter.

    Open3D 0.19 expects RANSACConvergenceCriteria(max_iteration, confidence).
    The existing UI exposes an integer field historically treated like
    "validation iterations". We preserve that UX by mapping integers >= 2 to
    confidence=1.0 (disable early stop) and allowing direct [0,1] confidence
    if a float is supplied programmatically.
    """
    try:
        value = float(validation_iterations)
    except Exception:
        return 1.0

    if not np.isfinite(value):
        return 1.0
    if value >= 2.0:
        return 1.0
    return float(np.clip(value, 0.90, 1.0))


def _apply_spacing_prescale_if_available(source_pcd, source_spacing_mm, target_spacing_mm):
    if source_spacing_mm is None or target_spacing_mm is None:
        return {
            "enabled": False,
            "applied": False,
            "scale": 1.0,
            "method": "spacing_unavailable",
            "confidence": 0.0,
            "detail": "Missing source/target spacing metadata.",
        }

    try:
        src = float(source_spacing_mm)
        dst = float(target_spacing_mm)
    except Exception:
        return {
            "enabled": False,
            "applied": False,
            "scale": 1.0,
            "method": "spacing_invalid",
            "confidence": 0.0,
            "detail": "Could not parse spacing metadata.",
        }

    if (not np.isfinite(src)) or (not np.isfinite(dst)) or src <= 0.0 or dst <= 0.0:
        return {
            "enabled": False,
            "applied": False,
            "scale": 1.0,
            "method": "spacing_invalid",
            "confidence": 0.0,
            "detail": "Spacing values must be finite and > 0.",
        }

    raw_scale = float(dst / src)
    if abs(raw_scale - 1.0) <= SPACING_PRESCALE_TRIGGER:
        return {
            "enabled": True,
            "applied": False,
            "scale": 1.0,
            "method": "spacing_ratio",
            "confidence": 0.95,
            "detail": f"ratio={raw_scale:.6f} within trigger {SPACING_PRESCALE_TRIGGER:.3f}",
        }

    scale = float(np.clip(raw_scale, SPACING_PRESCALE_MIN, SPACING_PRESCALE_MAX))
    source_pcd.scale(scale, source_pcd.get_center())
    clipped = abs(scale - raw_scale) > 1e-9
    return {
        "enabled": True,
        "applied": True,
        "scale": scale,
        "method": "spacing_ratio",
        "confidence": 0.95,
        "detail": f"raw={raw_scale:.6f} clipped={clipped}",
    }


def _combine_prescale_context(spacing_ctx, similarity_ctx):
    contexts = [ctx for ctx in (spacing_ctx, similarity_ctx) if isinstance(ctx, dict)]
    applied = [ctx for ctx in contexts if bool(ctx.get("applied"))]
    if not contexts:
        return {
            "enabled": False,
            "applied": False,
            "scale": 1.0,
            "method": "none",
            "confidence": 0.0,
            "detail": "",
            "components": [],
        }

    combined_scale = 1.0
    for ctx in applied:
        try:
            combined_scale *= float(ctx.get("scale", 1.0))
        except Exception:
            pass

    methods = [str(ctx.get("method", "unknown")) for ctx in applied]
    details = [str(ctx.get("detail", "")) for ctx in contexts if str(ctx.get("detail", ""))]
    confidence = max([float(ctx.get("confidence", 0.0)) for ctx in contexts] + [0.0])

    return {
        "enabled": True,
        "applied": bool(applied),
        "scale": float(combined_scale),
        "method": "+".join(methods) if methods else "none",
        "confidence": float(confidence),
        "detail": " | ".join(details),
        "components": contexts,
    }


def _apply_uniform_prescale_if_enabled(source_pcd, target_pcd, global_transform_model):
    if not uses_uniform_scaling(global_transform_model):
        return {
            "enabled": False,
            "applied": False,
            "scale": 1.0,
            "method": "disabled",
            "confidence": 0.0,
            "detail": "Global transform model is rigid.",
        }

    estimate = estimate_global_scale(
        source_pcd,
        target_pcd,
        min_scale=SIMILARITY_PRESCALE_MIN,
        max_scale=SIMILARITY_PRESCALE_MAX,
    )
    scale = float(estimate.scale)
    if not np.isfinite(scale) or scale <= 0:
        scale = 1.0

    # Keep similarity mode close to rigid when confidence is low.
    confidence = float(estimate.confidence)
    if confidence < SIMILARITY_MIN_CONFIDENCE_FULL_APPLY:
        delta = scale - 1.0
        scale = 1.0 + delta * SIMILARITY_LOW_CONFIDENCE_DAMPING

    scale = float(np.clip(scale, SIMILARITY_PRESCALE_MIN, SIMILARITY_PRESCALE_MAX))

    center = source_pcd.get_center()
    source_pcd.scale(scale, center)
    return {
        "enabled": True,
        "applied": True,
        "scale": scale,
        "method": estimate.method,
        "confidence": confidence,
        "detail": estimate.detail,
    }

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
    pcd_down, effective_voxel = _adaptive_downsample_for_features(pcd, voxel_size)
    pcd_down.estimate_normals(
        o3d.geometry.KDTreeSearchParamHybrid(radius=effective_voxel * 2.0, max_nn=30)
    )
    fpfh = o3d.pipelines.registration.compute_fpfh_feature(
        pcd_down,
        o3d.geometry.KDTreeSearchParamHybrid(radius=effective_voxel * 5.0, max_nn=100),
    )
    return pcd_down, fpfh, effective_voxel


def _cap_point_count_for_registration(pcd, max_points=MAX_REGISTRATION_POINTS):
    """Reduce very large clouds before feature matching to keep runtime/memory bounded."""
    count = len(np.asarray(pcd.points))
    if count <= int(max_points):
        return pcd
    keep_ratio = float(max_points) / float(max(count, 1))
    keep_ratio = max(0.0001, min(1.0, keep_ratio))
    return pcd.random_down_sample(keep_ratio)


def _adaptive_downsample_for_features(pcd, voxel_size, max_points=MAX_FEATURE_POINTS):
    """Increase voxel size only when needed to keep feature clouds bounded."""
    effective_voxel = max(float(voxel_size), 1e-9)
    max_points = max(1000, int(max_points))

    pcd_down = pcd.voxel_down_sample(effective_voxel)
    if len(np.asarray(pcd_down.points)) <= max_points:
        return pcd_down, effective_voxel

    for _ in range(6):
        count = max(1, len(np.asarray(pcd_down.points)))
        if count <= max_points:
            break
        scale = (float(count) / float(max_points)) ** (1.0 / 3.0)
        scale = max(1.15, min(2.0, scale))
        effective_voxel *= scale
        pcd_down = pcd.voxel_down_sample(effective_voxel)

    count = len(np.asarray(pcd_down.points))
    if count > max_points:
        keep_ratio = float(max_points) / float(max(count, 1))
        keep_ratio = max(0.0001, min(1.0, keep_ratio))
        pcd_down = pcd_down.random_down_sample(keep_ratio)

    return pcd_down, effective_voxel

# Imports the point clouds, applies transformations to one of them, and runs preprocessing
def import_dataset(voxel_size):
    pcd1 = get_pcd_from_stl()
    pcd2 = get_pcd_from_stl()

    pcd2.translate([100, 100, 100])
    pcd2.rotate(o3d.geometry.get_rotation_matrix_from_xyz((0.2, 0.2, 0.2)))

    pcd1_down, pcd1_fpfh, voxel1 = preprocess_point_cloud(pcd1, voxel_size)
    pcd2_down, pcd2_fpfh, voxel2 = preprocess_point_cloud(pcd2, voxel_size)

    return pcd1, pcd2, pcd1_down, pcd2_down, pcd1_fpfh, pcd2_fpfh, max(float(voxel1), float(voxel2))

# RANSAC 
def run_RANSAC(
    pcd1_down,
    pcd2_down,
    pcd1_fpfh,
    pcd2_fpfh,
    voxel_size,
    ransac_dist_multiplier=1.5,
    max_iterations=100000,
    validation_iterations=1000,
    global_transform_model=GLOBAL_TRANSFORM_RIGID,
):
    def _diag_extent(pcd):
        pts = np.asarray(pcd.points)
        if pts.size == 0:
            return 0.0
        mins = np.min(pts, axis=0)
        maxs = np.max(pts, axis=0)
        return float(np.linalg.norm(maxs - mins))

    def _result_score(reg):
        corr = len(reg.correspondence_set) if hasattr(reg, "correspondence_set") else 0
        rmse = float(reg.inlier_rmse) if np.isfinite(reg.inlier_rmse) else 1e9
        return (float(reg.fitness), corr, -rmse)

    distance_threshold = float(voxel_size) * float(ransac_dist_multiplier)
    with_scaling = uses_uniform_scaling(global_transform_model)

    n1 = len(np.asarray(pcd1_down.points))
    n2 = len(np.asarray(pcd2_down.points))
    point_ratio = float(max(n1, n2)) / float(max(1, min(n1, n2)))
    d1 = _diag_extent(pcd1_down)
    d2 = _diag_extent(pcd2_down)
    extent_ratio = float(max(d1, d2)) / float(max(1e-9, min(d1, d2)))
    partial_overlap_hint = (point_ratio >= 1.35) or (extent_ratio >= 1.35)

    # Multiple hypotheses improve robustness when one cloud is contained in the other.
    strategies = [
        {
            "name": "default_relaxed",
            "mutual_filter": False,
            "edge_ratio": 0.9,
            "distance_scale": 1.0,
        },
        {
            "name": "partial_overlap",
            "mutual_filter": False,
            "edge_ratio": 0.75,
            "distance_scale": 1.35,
        },
    ]
    if partial_overlap_hint:
        strategies.append(
            {
                "name": "partial_overlap_wide",
                "mutual_filter": False,
                "edge_ratio": 0.6,
                "distance_scale": 1.7,
            }
        )

    per_attempt_iter = max(20000, int(max_iterations) // max(1, len(strategies)))
    per_attempt_confidence = _resolve_ransac_confidence(validation_iterations)

    best_result = None
    best_name = ""
    for strategy in strategies:
        local_distance = float(distance_threshold) * float(strategy["distance_scale"])
        checkers = [
            o3d.pipelines.registration.CorrespondenceCheckerBasedOnEdgeLength(float(strategy["edge_ratio"])),
            o3d.pipelines.registration.CorrespondenceCheckerBasedOnDistance(local_distance),
        ]
        result = o3d.pipelines.registration.registration_ransac_based_on_feature_matching(
            pcd1_down,
            pcd2_down,
            pcd1_fpfh,
            pcd2_fpfh,
            bool(strategy["mutual_filter"]),
            local_distance,
            o3d.pipelines.registration.TransformationEstimationPointToPoint(with_scaling),
            4,
            checkers,
            o3d.pipelines.registration.RANSACConvergenceCriteria(per_attempt_iter, per_attempt_confidence),
        )
        if best_result is None or _result_score(result) > _result_score(best_result):
            best_result = result
            best_name = str(strategy["name"])

    # FGR fallback can recover from very sparse correspondence sets.
    use_fgr_fallback = best_result is None or float(best_result.fitness) < 0.015
    if use_fgr_fallback:
        fgr_option = o3d.pipelines.registration.FastGlobalRegistrationOption(
            maximum_correspondence_distance=float(distance_threshold) * (1.8 if partial_overlap_hint else 1.3),
            iteration_number=128,
        )
        fgr_result = o3d.pipelines.registration.registration_fgr_based_on_feature_matching(
            pcd1_down,
            pcd2_down,
            pcd1_fpfh,
            pcd2_fpfh,
            fgr_option,
        )
        if best_result is None or _result_score(fgr_result) > _result_score(best_result):
            best_result = fgr_result
            best_name = "fgr_fallback"

    if best_result is None:
        raise RuntimeError("Global registration failed to produce a result.")

    print(
        "Global registration selected:",
        best_name,
        f"fitness={float(best_result.fitness):.6f}",
        f"rmse={float(best_result.inlier_rmse):.6f}",
        f"corr={len(best_result.correspondence_set)}",
        f"partial_overlap_hint={partial_overlap_hint}",
    )
    return best_result


def run_ICP(
    pcd1,
    pcd2,
    initial_transform,
    voxel_size,
    icp_dist_multiplier=0.4,
    max_iterations=50,
    global_transform_model=GLOBAL_TRANSFORM_RIGID,
):
    distance_threshold = voxel_size * icp_dist_multiplier
    criteria = o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=max_iterations)
    with_scaling = uses_uniform_scaling(global_transform_model)
    result = o3d.pipelines.registration.registration_icp(
        pcd1,
        pcd2,
        distance_threshold,
        initial_transform,
        o3d.pipelines.registration.TransformationEstimationPointToPoint(with_scaling),
        criteria=criteria,
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
    global_transform_model=GLOBAL_TRANSFORM_RIGID,
    source_spacing_mm=None,
    target_spacing_mm=None,
):
    """Run full registration and emit only stage-complete callbacks.

    Callback stages are fixed to three entries:
    0 = raw clouds, 1 = post-RANSAC, 2 = post-ICP.
    """

    pre_scale = {
        "enabled": False,
        "applied": False,
        "scale": 1.0,
        "method": "disabled",
        "confidence": 0.0,
        "detail": "",
    }
    spacing_pre_scale = {
        "enabled": False,
        "applied": False,
        "scale": 1.0,
        "method": "spacing_unavailable",
        "confidence": 0.0,
        "detail": "",
    }
    similarity_pre_scale = {
        "enabled": False,
        "applied": False,
        "scale": 1.0,
        "method": "disabled",
        "confidence": 0.0,
        "detail": "",
    }

    if source_pcd is not None and target_pcd is not None:
        pcd1 = copy.deepcopy(source_pcd)
        pcd2 = copy.deepcopy(target_pcd)
        pcd1 = _cap_point_count_for_registration(pcd1)
        pcd2 = _cap_point_count_for_registration(pcd2)
        spacing_pre_scale = _apply_spacing_prescale_if_available(pcd1, source_spacing_mm, target_spacing_mm)
        similarity_pre_scale = _apply_uniform_prescale_if_enabled(pcd1, pcd2, global_transform_model)
        pre_scale = _combine_prescale_context(spacing_pre_scale, similarity_pre_scale)
        pcd1_down, pcd1_fpfh, voxel1 = preprocess_point_cloud(pcd1, voxel_size)
        pcd2_down, pcd2_fpfh, voxel2 = preprocess_point_cloud(pcd2, voxel_size)
        registration_voxel_size = max(float(voxel_size), float(voxel1), float(voxel2))
    else:
        pcd1, pcd2, _pcd1_down, _pcd2_down, _pcd1_fpfh, _pcd2_fpfh, _effective_voxel = import_dataset(voxel_size)
        spacing_pre_scale = _apply_spacing_prescale_if_available(pcd1, source_spacing_mm, target_spacing_mm)
        similarity_pre_scale = _apply_uniform_prescale_if_enabled(pcd1, pcd2, global_transform_model)
        pre_scale = _combine_prescale_context(spacing_pre_scale, similarity_pre_scale)
        pcd1_down, pcd1_fpfh, voxel1 = preprocess_point_cloud(pcd1, voxel_size)
        pcd2_down, pcd2_fpfh, voxel2 = preprocess_point_cloud(pcd2, voxel_size)
        registration_voxel_size = max(float(voxel_size), float(voxel1), float(voxel2))

    if spacing_pre_scale.get("enabled"):
        print(
            "Spacing pre-scale:",
            f"applied={bool(spacing_pre_scale.get('applied'))}",
            f"scale={float(spacing_pre_scale.get('scale', 1.0)):.6f}",
            f"detail={spacing_pre_scale.get('detail', '')}",
        )

    if registration_voxel_size > float(voxel_size):
        print(
            f"Registration guard: requested voxel {float(voxel_size):.6g}, "
            f"using {float(registration_voxel_size):.6g} to bound feature cloud size"
        )

    # stage 0: raw clouds
    if step_callback is not None:
        step_callback(
            0,
            0,
            {
                "pcd1": pcd1,
                "pcd2": pcd2,
                "pre_scale": pre_scale,
                "spacing_pre_scale": spacing_pre_scale,
                "similarity_pre_scale": similarity_pre_scale,
                "registration_voxel_size": registration_voxel_size,
            },
        )

    # stage 1: built-in global RANSAC (single solve)
    result_ransac = run_RANSAC(
        pcd1_down,
        pcd2_down,
        pcd1_fpfh,
        pcd2_fpfh,
        registration_voxel_size,
        ransac_dist_multiplier,
        ransac_max_iter,
        ransac_validation,
        global_transform_model=global_transform_model,
    )
    if step_callback is not None:
        step_callback(
            1,
            1,
            {
                "ransac": result_ransac,
                "total": 1,
                "configured_max_iter": ransac_max_iter,
                "registration_voxel_size": registration_voxel_size,
            },
        )

    # stage 2: built-in local ICP (single solve)
    adaptive_icp_multiplier = float(icp_dist_multiplier)
    adaptive_icp_iters = int(icp_max_iter)
    if float(result_ransac.fitness) < 0.02:
        adaptive_icp_multiplier = max(adaptive_icp_multiplier, 1.1)
        adaptive_icp_iters = max(adaptive_icp_iters, 90)

    result_icp = run_ICP(
        pcd1,
        pcd2,
        result_ransac.transformation,
        registration_voxel_size,
        adaptive_icp_multiplier,
        adaptive_icp_iters,
        global_transform_model=global_transform_model,
    )
    if uses_uniform_scaling(global_transform_model):
        icp_scale = _extract_uniform_scale(result_icp.transformation)
        transform_finite = _transform_is_finite(result_icp.transformation)
        scale_plausible = np.isfinite(icp_scale) and 0.85 <= float(icp_scale) <= 1.15
        print(f"Local ICP similarity scale: {icp_scale:.6f}")
        if (not transform_finite) or (not scale_plausible):
            print("Local ICP similarity became unstable; rerunning local stage as rigid fallback.")
            result_icp = run_ICP(
                pcd1,
                pcd2,
                result_ransac.transformation,
                registration_voxel_size,
                adaptive_icp_multiplier,
                adaptive_icp_iters,
                global_transform_model=GLOBAL_TRANSFORM_RIGID,
            )
    if step_callback is not None:
        step_callback(
            2,
            1,
            {
                "icp": result_icp,
                "total": 1,
                "configured_max_iter": icp_max_iter,
                "registration_voxel_size": registration_voxel_size,
            },
        )

    return {
        "pcd1": pcd1,
        "pcd2": pcd2,
        "ransac": result_ransac,
        "icp": result_icp,
        "global_transform_model": global_transform_model,
        "pre_scale": pre_scale,
        "spacing_pre_scale": spacing_pre_scale,
        "similarity_pre_scale": similarity_pre_scale,
        "registration_voxel_size": registration_voxel_size,
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
