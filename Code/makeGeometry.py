import os
import re
from dataclasses import dataclass
import numpy as np
import open3d as o3d

import tifffile as tiff
import dask.array as da
from dask import delayed
from skimage.measure import marching_cubes


@dataclass(frozen=True)
class VolumeSource:
    """Lightweight descriptor for lazily loading a TIFF stack volume preview."""

    folder_path: str
    voxel_size_mm: float | None = None
    crop_zyx: tuple[int, int, int] | None = None
    default_downsample_zyx: int = 4
    max_preview_voxels: int = 8_000_000


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


def inspect_tiff_stack(folder_path: str):
    """Return shape/dtype metadata without loading the full TIFF stack."""
    paths = _sorted_tiffs(folder_path)
    if not paths:
        raise FileNotFoundError("No tif/tiff files found in folder")

    sample = _lazy_slice(paths[0])
    return {
        "shape_zyx": (len(paths), *sample.shape),
        "dtype": str(sample.dtype),
        "slice_count": len(paths),
    }


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


def _normalize_volume_to_uint8(volume):
    """Convert a preview volume to uint8 while avoiding full-stack assumptions."""
    if volume.dtype == np.uint8:
        return np.ascontiguousarray(volume)

    if volume.size == 0:
        return np.zeros(volume.shape, dtype=np.uint8)

    lo, hi = np.percentile(volume, (1.0, 99.5))
    if hi <= lo:
        return np.zeros(volume.shape, dtype=np.uint8)

    scaled = (volume.astype(np.float32, copy=False) - float(lo)) * (255.0 / float(hi - lo))
    np.clip(scaled, 0.0, 255.0, out=scaled)
    return np.ascontiguousarray(scaled.astype(np.uint8, copy=False))


def load_ct_volume_preview(
    folder_path: str,
    downsample_zyx: int = 4,
    crop_zyx: tuple[int, int, int] | None = (256, 256, 256),
    max_preview_voxels: int = 8_000_000,
):
    """
    Lazily load a GPU-friendly TIFF stack preview volume.

    The returned array is uint8 and transposed to XYZ order for pyqtgraph's
    GLVolumeItem.  Only the downsampled/cropped preview is computed.
    """
    downsample_zyx = max(1, int(downsample_zyx))
    max_preview_voxels = max(1, int(max_preview_voxels))

    vol = _make_lazy_volume_zyx(folder_path)
    effective_downsample = downsample_zyx
    vol_ds = vol[::effective_downsample, ::effective_downsample, ::effective_downsample]

    if crop_zyx is not None:
        z0, z1, y0, y1, x0, x1 = _center_crop_bounds(vol_ds.shape, crop_zyx)
        preview = vol_ds[z0:z1, y0:y1, x0:x1]
    else:
        z0, y0, x0 = 0, 0, 0
        z1, y1, x1 = vol_ds.shape
        preview = vol_ds

    preview_voxels = int(np.prod(preview.shape))
    if preview_voxels > max_preview_voxels:
        guard_factor = int(np.ceil((preview_voxels / max_preview_voxels) ** (1.0 / 3.0)))
        guard_factor = max(2, guard_factor)
        effective_downsample *= guard_factor
        vol_ds = vol[::effective_downsample, ::effective_downsample, ::effective_downsample]
        if crop_zyx is not None:
            guarded_crop = tuple(max(1, int(np.ceil(v / guard_factor))) for v in crop_zyx)
            z0, z1, y0, y1, x0, x1 = _center_crop_bounds(vol_ds.shape, guarded_crop)
            preview = vol_ds[z0:z1, y0:y1, x0:x1]
        else:
            z0, y0, x0 = 0, 0, 0
            z1, y1, x1 = vol_ds.shape
            preview = vol_ds

    sub_zyx = preview.compute()
    sub_zyx = _normalize_volume_to_uint8(sub_zyx)
    sub_xyz = np.ascontiguousarray(np.transpose(sub_zyx, (2, 1, 0)))

    metadata = {
        "shape_zyx": tuple(int(v) for v in vol.shape),
        "preview_shape_xyz": tuple(int(v) for v in sub_xyz.shape),
        "dtype": str(vol.dtype),
        "downsample_zyx": effective_downsample,
        "crop_origin_zyx": (int(z0), int(y0), int(x0)),
        "crop_shape_zyx": (int(z1 - z0), int(y1 - y0), int(x1 - x0)),
        "preview_voxels": int(sub_xyz.size),
    }
    return sub_xyz, metadata


def get_mesh_from_ct_stack(
    folder_path: str,
    voxel_size_mm: float = 0.006937965888099794,
    downsample_zyx: int = 2,                      
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

    # marching_cubes returns coordinates in array index order (Z, Y, X).
    # Keep world coords aligned with the volume viewer by converting to (X, Y, Z).
    verts[:, 0] += z0 * s
    verts[:, 1] += y0 * s
    verts[:, 2] += x0 * s
    verts = np.ascontiguousarray(verts[:, [2, 1, 0]])

    mesh = o3d.geometry.TriangleMesh()
    mesh.vertices = o3d.utility.Vector3dVector(verts.astype(np.float64, copy=False))
    mesh.triangles = o3d.utility.Vector3iVector(faces.astype(np.int32, copy=False))
    mesh.compute_vertex_normals()
    return mesh, level


def get_pcd_from_ct_stack(
    folder_path: str,
    voxel_size_mm: float = 0.006937965888099794,
    downsample_zyx: int = 2,
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
    folder = os.path.join("..", "120kv_FDK")

    pcd, mesh, level = get_pcd_from_ct_stack(
        folder_path=folder,
        downsample_zyx=4,
        crop_zyx=(2943, 2304, 2943), 
        level=None,
        n_points=50_000,
    )

    print("MC level:", level)
    print("Mesh verts:", np.asarray(mesh.vertices).shape[0])
    print("PCD points:", np.asarray(pcd.points).shape[0])

    #o3d.visualization.draw_geometries([mesh])
    # or:
    o3d.visualization.draw_geometries([pcd])
