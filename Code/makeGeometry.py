import os
import re
import numpy as np
import open3d as o3d

import tifffile as tiff
import dask.array as da
from dask import delayed
from skimage.measure import marching_cubes


# use open3d to make some shapes.
def get_pcd_from_stl(path=None):
    if path is None:
        # Default to TestPart.stl in the same directory as this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(script_dir, "TestPart.stl")
    
    mesh = o3d.io.read_triangle_mesh(path)
    mesh.compute_vertex_normals()

    pcd = mesh.sample_points_poisson_disk(number_of_points=2000)
    #o3d.visualization.draw([mesh, pcd])

    return pcd

def _sorted_tiffs(folder):
    files = [f for f in os.listdir(folder) if f.lower().endswith((".tif", ".tiff"))]
    files.sort()
    return [os.path.join(folder, f) for f in files]


def _lazy_slice(path):
    return tiff.imread(path)


def _make_lazy_volume_zyx(folder):
    paths = _sorted_tiffs(folder)
    if not paths:
        raise FileNotFoundError("No tif/tiff files found in folder")

    a0 = _lazy_slice(paths[0])
    H, W = a0.shape
    dtype = a0.dtype

    vol = da.stack(
        [
            da.from_delayed(delayed(_lazy_slice)(p), shape=(H, W), dtype=dtype)
            for p in paths
        ],
        axis=0,  # (Z, Y, X)
    )
    return vol


def _center_crop_bounds(shape_zyx, crop_zyx):
    Z, Y, X = shape_zyx
    cz, cy, cx = crop_zyx

    z0 = max(0, Z // 2 - cz // 2)
    y0 = max(0, Y // 2 - cy // 2)
    x0 = max(0, X // 2 - cx // 2)

    z1 = min(Z, z0 + cz)
    y1 = min(Y, y0 + cy)
    x1 = min(X, x0 + cx)
    return z0, z1, y0, y1, x0, x1


def get_mesh_from_ct_stack(
    folder_path: str,
    voxel_size_mm: float = 0.006937965888099794,  
    downsample_zyx: int = 3,                      
    crop_zyx: tuple[int, int, int] = (256, 256, 256),
    level: float | None = None,
):
    """
    Returns an Open3D TriangleMesh extracted from a CT TIFF stack using marching cubes.

    Memory-safe approach:
      - lazy load full stack
      - uniformly downsample (Z,Y,X) with slicing
      - compute only a cropped subvolume
      - run marching cubes on that subvolume
    """

    vol = _make_lazy_volume_zyx(folder_path)               # dask (Z,Y,X)
    vol_ds = vol[::downsample_zyx, ::downsample_zyx, ::downsample_zyx]

    z0, z1, y0, y1, x0, x1 = _center_crop_bounds(vol_ds.shape, crop_zyx)
    sub = vol_ds[z0:z1, y0:y1, x0:x1].compute()            # numpy array (small)

    # Pick a starting iso-level if not provided
    if level is None:
        level = float(np.percentile(sub, 99.5))

    # spacing in mm after downsampling
    s = voxel_size_mm * downsample_zyx
    spacing = (s, s, s)

    verts, faces, normals, values = marching_cubes(
        sub,
        level=level,
        spacing=spacing,
        allow_degenerate=False,
    )

    # Put mesh into "global" coordinates of the downsampled volume (optional but useful later)
    verts[:, 0] += z0 * s
    verts[:, 1] += y0 * s
    verts[:, 2] += x0 * s

    mesh = o3d.geometry.TriangleMesh()
    mesh.vertices = o3d.utility.Vector3dVector(verts.astype(np.float64, copy=False))
    mesh.triangles = o3d.utility.Vector3iVector(faces.astype(np.int32, copy=False))
    mesh.compute_vertex_normals()
    return mesh, level


def get_pcd_from_ct_stack(
    folder_path: str,
    voxel_size_mm: float = 0.006937965888099794,
    downsample_zyx: int = 4,
    crop_zyx: tuple[int, int, int] = (256, 256, 256),
    level: float | None = None,
    n_points: int = 2000,
):
    """
    Returns an Open3D PointCloud of the via extracted from CT.
    Mirrors the output style of get_pcd_from_stl() :contentReference[oaicite:4]{index=4}.
    """
    mesh, used_level = get_mesh_from_ct_stack(
        folder_path=folder_path,
        voxel_size_mm=voxel_size_mm,
        downsample_zyx=downsample_zyx,
        crop_zyx=crop_zyx,
        level=level,
    )
    pcd = mesh.sample_points_poisson_disk(number_of_points=n_points)
    return pcd, mesh, used_level



if __name__ == "__main__":
    folder = os.path.join("..", "reconstruction_v1")

    pcd, mesh, level = get_pcd_from_ct_stack(
        folder_path=folder,
        downsample_zyx=4,
        crop_zyx=(256, 256, 256),
        level=None,
        n_points=5000,
    )

    print("MC level:", level)
    print("Mesh verts:", np.asarray(mesh.vertices).shape[0])
    print("PCD points:", np.asarray(pcd.points).shape[0])

    o3d.visualization.draw_geometries([mesh])
    # or:
    # o3d.visualization.draw_geometries([pcd])