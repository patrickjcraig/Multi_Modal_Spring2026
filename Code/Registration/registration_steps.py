"""Utility routines for registration stage callbacks.

This module provides wrappers around Open3D's registration algorithms that
allow the caller to observe stage results in the GUI.  The
existing high-level functions in ``open3d_ICP.py`` only expose the final
outcome; these helpers provide a small callback layer so the GUI can show
completed global and local registration states without having to animate
every intermediate iteration.

"""


def iterative_ransac(
    pcd1_down,
    pcd2_down,
    pcd1_fpfh,
    pcd2_fpfh,
    voxel_size,
    ransac_dist_multiplier=1.5,
    max_iterations=100000,
    validation_iterations=1000,
    step=1,
    callback=None,
    global_transform_model="rigid",
):
    """Run RANSAC once and optionally emit a single callback.

    The earlier implementation repeatedly re-ran RANSAC in small iteration
    increments so the GUI could animate intermediate states. That was very
    expensive because each callback triggered a fresh global registration run.

    This helper now performs one RANSAC solve using ``max_iterations`` and
    ``validation_iterations`` as the Open3D convergence settings. If a
    ``callback`` is supplied, it is invoked once with ``(max_iterations,
    result)`` so the GUI still receives a stage-complete update.
    """
    # avoid relative imports beyond top-level; open3d_ICP is a top-level module
    from open3d_ICP import run_RANSAC

    result = run_RANSAC(
        pcd1_down,
        pcd2_down,
        pcd1_fpfh,
        pcd2_fpfh,
        voxel_size,
        ransac_dist_multiplier,
        max_iterations,
        validation_iterations,
        global_transform_model=global_transform_model,
    )
    if callback is not None:
        callback(max_iterations, result)
    return result


def iterative_icp(
    pcd1,
    pcd2,
    initial_transformation,
    voxel_size,
    icp_dist_multiplier=0.4,
    max_iterations=50,
    step=1,
    callback=None,
):
    """Run ICP once and optionally emit a single callback.

    The previous implementation replayed ICP with increasing iteration counts
    so the GUI could animate each local-refinement step. That is left below as
    commented reference code in case we want to generate a figure from the
    intermediate poses later, but the normal workflow now runs one ICP solve
    and exposes the final local result through the previous/next stage viewer.
    """
    from open3d_ICP import run_ICP

    result = run_ICP(
        pcd1,
        pcd2,
        initial_transformation,
        voxel_size,
        icp_dist_multiplier,
        max_iterations=max_iterations,
    )
    if callback is not None:
        callback(max_iterations, result)
    return result

    # Legacy iterative ICP animation path kept for future figures/reference.
    # if initial_transformation is None:
    #     import numpy as _np
    #     starting = _np.eye(4)
    # else:
    #     starting = initial_transformation
    #
    # best = None
    # for it in range(step, max_iterations + 1, step):
    #     crit = o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=it)
    #     result = o3d.pipelines.registration.registration_icp(
    #         pcd1,
    #         pcd2,
    #         voxel_size * icp_dist_multiplier,
    #         starting,
    #         o3d.pipelines.registration.TransformationEstimationPointToPoint(),
    #         criteria=crit,
    #     )
    #     best = result
    #     if callback is not None:
    #         callback(it, result)
    # return best
