import copy
import numpy as np
import open3d as o3d


def _rotation_matrix_xyz(rx_deg, ry_deg, rz_deg):
    rx, ry, rz = np.deg2rad([rx_deg, ry_deg, rz_deg])

    cx, sx = np.cos(rx), np.sin(rx)
    cy, sy = np.cos(ry), np.sin(ry)
    cz, sz = np.cos(rz), np.sin(rz)

    rx_m = np.array(
        [
            [1.0, 0.0, 0.0],
            [0.0, cx, -sx],
            [0.0, sx, cx],
        ],
        dtype=float,
    )

    ry_m = np.array(
        [
            [cy, 0.0, sy],
            [0.0, 1.0, 0.0],
            [-sy, 0.0, cy],
        ],
        dtype=float,
    )

    rz_m = np.array(
        [
            [cz, -sz, 0.0],
            [sz, cz, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=float,
    )

    return rz_m @ ry_m @ rx_m


def make_affine_matrix(
    rotation_deg=(0.0, 0.0, 0.0),
    scale=(1.0, 1.0, 1.0),
    translation=(0.0, 0.0, 0.0),
):
    r = _rotation_matrix_xyz(*rotation_deg)
    s = np.diag(np.asarray(scale, dtype=float))
    a = r @ s

    m = np.eye(4, dtype=float)
    m[:3, :3] = a
    m[:3, 3] = np.asarray(translation, dtype=float)
    return m


def apply_affine_to_points(points: np.ndarray, affine_4x4: np.ndarray) -> np.ndarray:
    pts = np.asarray(points, dtype=float)
    ones = np.ones((pts.shape[0], 1), dtype=float)
    pts_h = np.hstack([pts, ones])
    out = (affine_4x4 @ pts_h.T).T
    return out[:, :3]


def apply_affine_to_pcd(pcd: o3d.geometry.PointCloud, affine_4x4: np.ndarray):
    out = copy.deepcopy(pcd)
    pts = np.asarray(out.points)
    out.points = o3d.utility.Vector3dVector(apply_affine_to_points(pts, affine_4x4))

    if out.has_normals():
        normals = np.asarray(out.normals)
        rot = affine_4x4[:3, :3]
        transformed_normals = (rot @ normals.T).T
        norms = np.linalg.norm(transformed_normals, axis=1, keepdims=True)
        norms = np.where(norms == 0.0, 1.0, norms)
        transformed_normals /= norms
        out.normals = o3d.utility.Vector3dVector(transformed_normals)

    return out


def crop_partial_point_cloud(pcd: o3d.geometry.PointCloud, keep_ratio: float = 0.5):
    pts = np.asarray(pcd.points)
    if pts.shape[0] == 0:
        return copy.deepcopy(pcd)

    keep_ratio = float(np.clip(keep_ratio, 0.01, 1.0))

    mins = pts.min(axis=0)
    maxs = pts.max(axis=0)
    spans = maxs - mins

    x_cut = mins[0] + keep_ratio * spans[0]
    mask = pts[:, 0] <= x_cut

    cropped = o3d.geometry.PointCloud()
    cropped.points = o3d.utility.Vector3dVector(pts[mask])

    if pcd.has_colors():
        colors = np.asarray(pcd.colors)
        cropped.colors = o3d.utility.Vector3dVector(colors[mask])

    if pcd.has_normals():
        normals = np.asarray(pcd.normals)
        cropped.normals = o3d.utility.Vector3dVector(normals[mask])

    return cropped