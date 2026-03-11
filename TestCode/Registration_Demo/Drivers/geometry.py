import os
import numpy as np
import open3d as o3d
import tifffile as tiff
import dask.array as da
from dask import delayed
from skimage.measure import marching_cubes


def get_pcd_from_stl(path: str | None = None, n_points: int = 2000):
    if path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(script_dir, "TestPart.stl")

    mesh = o3d.io.read_triangle_mesh(path)
    if mesh.is_empty():
        raise ValueError(f"Could not load mesh: {path}")

    mesh.compute_vertex_normals()
    pcd = mesh.sample_points_poisson_disk(number_of_points=n_points)
    return pcd


def _sorted_tiffs(folder_path: str):
    files = [
        f for f in os.listdir(folder_path)
        if f.lower().endswith((".tif", ".tiff"))
    ]
    files.sort()
    return [os.path.join(folder_path, f) for f in files]


def _lazy_read_slice(path: str):
    return tiff.imread(path)


def _make_lazy_volume_zyx(folder_path: str):
    tiff_paths = _sorted_tiffs(folder_path)
    if not tiff_paths:
        raise FileNotFoundError(f"No TIFF files found in folder: {folder_path}")

    first = _lazy_read_slice(tiff_paths[0])
    if first.ndim != 2:
        raise ValueError(
            f"Expected 2D TIFF slices, got shape {first.shape} in {tiff_paths[0]}"
        )

    h, w = first.shape
    dtype = first.dtype

    lazy_stack = da.stack(
        [
            da.from_delayed(
                delayed(_lazy_read_slice)(path),
                shape=(h, w),
                dtype=dtype,
            )
            for path in tiff_paths
        ],
        axis=0,
    )
    return lazy_stack


def _clamp_crop_size(shape_zyx, crop_size_zyx):
    zmax, ymax, xmax = shape_zyx
    sz, sy, sx = crop_size_zyx

    sz = max(1, min(int(sz), int(zmax)))
    sy = max(1, min(int(sy), int(ymax)))
    sx = max(1, min(int(sx), int(xmax)))

    return sz, sy, sx


def _downsample_crop_size(crop_size_zyx, downsample_zyx: int):
    sz, sy, sx = crop_size_zyx
    return (
        max(1, (sz + downsample_zyx - 1) // downsample_zyx),
        max(1, (sy + downsample_zyx - 1) // downsample_zyx),
        max(1, (sx + downsample_zyx - 1) // downsample_zyx),
    )


def get_mesh_from_ct_stack(
    folder_path: str,
    voxel_size_mm: float,
    downsample_zyx: int = 2,
    roi_size_zyx: tuple[int, int, int] | None = None,
    level: float | None = None,
):
    """
    Returns an Open3D TriangleMesh extracted from a CT TIFF stack using marching cubes.

    Assumes ROI starts at (0, 0, 0) in the original volume.
    The only ROI input is the requested size in (Z, Y, X).
    """

    vol_zyx = _make_lazy_volume_zyx(folder_path)
    vol_ds = vol_zyx[::downsample_zyx, ::downsample_zyx, ::downsample_zyx]

    if roi_size_zyx is None:
        crop_ds = vol_ds.shape
    else:
        crop_ds = _downsample_crop_size(roi_size_zyx, downsample_zyx)
        crop_ds = _clamp_crop_size(vol_ds.shape, crop_ds)

    sz, sy, sx = crop_ds

    z0, y0, x0 = 0, 0, 0
    z1, y1, x1 = sz, sy, sx

    subvol = vol_ds[z0:z1, y0:y1, x0:x1].compute()

    if subvol.size == 0:
        raise ValueError("ROI produced an empty volume")

    print(f"Full volume shape (ZYX): {tuple(int(v) for v in vol_zyx.shape)}")
    print(f"Downsampled volume shape (ZYX): {tuple(int(v) for v in vol_ds.shape)}")
    print(f"Requested ROI size original (ZYX): {roi_size_zyx}")
    print(f"Actual ROI size downsampled (ZYX): {(sz, sy, sx)}")
    print(f"ROI intensity min/max: {float(subvol.min())} / {float(subvol.max())}")

    if level is None:
        p50 = np.percentile(subvol, 50)
        p995 = np.percentile(subvol, 99.5)
        level = float(0.5 * (p50 + p995))

    print(f"Marching cubes level: {level}")

    s = voxel_size_mm * downsample_zyx
    spacing = (s, s, s)

    verts, faces, normals, values = marching_cubes(
        subvol,
        level=level,
        spacing=spacing,
        allow_degenerate=False,
    )

    # marching_cubes returns coordinates in local ROI order: Z, Y, X
    verts[:, 0] += z0 * s
    verts[:, 1] += y0 * s
    verts[:, 2] += x0 * s

    # reorder to X, Y, Z for rendering / Open3D convention
    verts_xyz = verts[:, [2, 1, 0]]
    normals_xyz = normals[:, [2, 1, 0]]

    mesh = o3d.geometry.TriangleMesh()
    mesh.vertices = o3d.utility.Vector3dVector(verts_xyz.astype(np.float64, copy=False))
    mesh.triangles = o3d.utility.Vector3iVector(faces.astype(np.int32, copy=False))
    mesh.vertex_normals = o3d.utility.Vector3dVector(normals_xyz.astype(np.float64, copy=False))

    return mesh, level


def get_pcd_from_ct_stack(
    folder_path: str,
    voxel_size_mm: float,
    downsample_zyx: int = 2,
    roi_size_zyx: tuple[int, int, int] | None = None,
    level: float | None = None,
    n_points: int = 2000,
):
    mesh, used_level = get_mesh_from_ct_stack(
        folder_path=folder_path,
        voxel_size_mm=voxel_size_mm,
        downsample_zyx=downsample_zyx,
        roi_size_zyx=roi_size_zyx,
        level=level,
    )

    if len(mesh.vertices) == 0:
        raise ValueError("Generated mesh is empty")

    mesh.compute_vertex_normals()
    pcd = mesh.sample_points_poisson_disk(number_of_points=n_points)

    return pcd, mesh, used_level

'''
if __name__ == "__main__":
    folder = os.path.join("..", "120kv_FDK")

    pcd, mesh, level = get_pcd_from_ct_stack(
        folder_path=folder,
        voxel_size_mm=0.0004631795192807952,
        downsample_zyx=4,
        roi_size_zyx=(2943, 2304, 2943),
        level=None,
        n_points=50000,
    )

    print("Mesh verts:", np.asarray(mesh.vertices).shape[0])
    print("PCD points:", np.asarray(pcd.points).shape[0])
'''