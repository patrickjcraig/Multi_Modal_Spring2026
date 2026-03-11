import copy
import numpy as np
import open3d as o3d


def pcd_to_gl_data(pcd: o3d.geometry.PointCloud, color=(1.0, 1.0, 1.0)):
    points = np.asarray(pcd.points, dtype=np.float32)

    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError("Point cloud positions must have shape (N, 3)")

    if pcd.has_colors():
        colors = np.asarray(pcd.colors, dtype=np.float32)
    else:
        base_color = np.asarray(color, dtype=np.float32).reshape(1, 3)
        colors = np.repeat(base_color, points.shape[0], axis=0)

    return {
        "positions": points,
        "colors": colors,
        "mode": "points",
    }


def mesh_to_gl_data(mesh: o3d.geometry.TriangleMesh, color=(0.7, 0.7, 0.7)):
    mesh_local = copy.deepcopy(mesh)
    if not mesh_local.has_vertex_normals():
        mesh_local.compute_vertex_normals()

    vertices = np.asarray(mesh_local.vertices, dtype=np.float32)
    normals = np.asarray(mesh_local.vertex_normals, dtype=np.float32)
    triangles = np.asarray(mesh_local.triangles, dtype=np.uint32)

    if mesh_local.has_vertex_colors():
        colors = np.asarray(mesh_local.vertex_colors, dtype=np.float32)
    else:
        base_color = np.asarray(color, dtype=np.float32).reshape(1, 3)
        colors = np.repeat(base_color, vertices.shape[0], axis=0)

    return {
        "positions": vertices,
        "normals": normals,
        "colors": colors,
        "indices": triangles,
        "mode": "mesh",
    }


def transform_points(points: np.ndarray, transform: np.ndarray) -> np.ndarray:
    pts = np.asarray(points, dtype=np.float32)
    t = np.asarray(transform, dtype=np.float32)

    ones = np.ones((pts.shape[0], 1), dtype=np.float32)
    pts_h = np.hstack([pts, ones])
    out = (t @ pts_h.T).T
    return out[:, :3]


def apply_transform_to_gl_object(gl_obj: dict, transform: np.ndarray) -> dict:
    out = dict(gl_obj)
    out["positions"] = transform_points(gl_obj["positions"], transform)
    return out