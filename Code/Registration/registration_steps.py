"""Utility routines for registration with iteration callbacks.

This module provides wrappers around Open3D's registration algorithms that
allow the caller to observe intermediate results on each iteration.  The
existing high-level functions in ``open3d_ICP.py`` only expose the final
outcome; here we re-run the algorithm in small increments and invoke a
callback for every step.  The GUI code can then animate the transformation
as the algorithm progresses.

Note that these implementations are *not* intended for production use; they
are slow since they repeat some work for each callback.  For exploratory
visualization on test meshes (e.g. ``TestPart.stl``) the overhead is
acceptable.

"""

import open3d as o3d


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
):
    """Run RANSAC and invoke ``callback`` every ``step`` iterations.

    Parameters mirror those in :func:`open3d_ICP.run_RANSAC` except that
    ``max_iterations`` is the total number of iterations we will simulate and
    ``step`` controls the granularity of callbacks.  For each callback we
    simply call the original RANSAC helper with the current iteration
    limit; the returned result represents the best transform seen so far.

    The ``callback`` (if supplied) receives two arguments ``(iter, result)``
    where ``iter`` is the current iteration count and ``result`` is the
    ``RegistrationResult`` object returned by Open3D.

    Returns
    -------
    RegistrationResult
        The final result after ``max_iterations`` iterations.
    """
    # avoid relative imports beyond top-level; open3d_ICP is a top-level module
    from open3d_ICP import run_RANSAC

    best = None
    # iterate in increments, keeping track of the best result seen so far
    for it in range(step, max_iterations + 1, step):
        res = run_RANSAC(
            pcd1_down,
            pcd2_down,
            pcd1_fpfh,
            pcd2_fpfh,
            voxel_size,
            ransac_dist_multiplier,
            it,
            validation_iterations,
        )
        # if we haven't recorded a result yet, or this one is better, update
        if best is None:
            best = res
        else:
            # choose the result with higher fitness (more inliers)
            try:
                if res.fitness > best.fitness: # first check fitness
                    best = res
                elif res.fitness == best.fitness and res.inlier_rmse < best.inlier_rmse: # if fitness is equal, check RMSE
                    best = res
            except AttributeError:
                # fallback to using inlier_rmse if fitness is unavailable
                if getattr(res, "inlier_rmse", float("inf")) < getattr(best, "inlier_rmse", float("inf")):
                    best = res
        if callback is not None:
            callback(it, res)
    return best


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
    """Run ICP in a loop, invoking ``callback`` after each ``step`` iterations.

    The Open3D ICP wrapper accepts an ``ICPConvergenceCriteria`` object where
    ``max_iteration`` specifies how many iterations to perform.  We iterate
    ourselves in chunks of size ``step`` and feed the resulting transformation
    back as the starting guess for the next chunk, collecting intermediate
    results along the way.

    ``callback`` is called with ``(iter, result)`` where ``iter`` is the
    cumulative number of ICP iterations executed so far.

    Returns
    -------
    RegistrationResult
        The final ICP result.
    """
    # open3d_ICP lives at workspace root/Code/open3d_ICP.py
    from open3d_ICP import run_ICP

    # make sure we use a valid 4x4 matrix as the starting guess
    if initial_transformation is None:
        import numpy as _np
        starting = _np.eye(4)
    else:
        starting = initial_transformation

    best = None
    # iterate with an increasing total-iteration criterion so that each
    # callback corresponds to the result after ``it`` total ICP iterations.
    for it in range(step, max_iterations + 1, step):
        crit = o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=it)
        result = o3d.pipelines.registration.registration_icp(
            pcd1,
            pcd2,
            voxel_size * icp_dist_multiplier,
            starting,
            o3d.pipelines.registration.TransformationEstimationPointToPoint(),
            criteria=crit,
        )
        best = result
        if callback is not None:
            callback(it, result)
    return best
