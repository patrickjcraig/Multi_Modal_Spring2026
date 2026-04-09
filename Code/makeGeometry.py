import os
import re
from dataclasses import dataclass
import numpy as np
import open3d as o3d
import h5py
import cv2

import tifffile as tiff
import dask.array as da
from dask import delayed
from skimage.measure import marching_cubes


@dataclass(frozen=True)
class VolumeSource:
    """Lightweight descriptor for lazily loading a volume preview."""

    path: str
    source_type: str = "tiff_stack"
    dataset_path: str | None = None
    voxel_size_mm: float | None = None
    crop_zyx: tuple[int, int, int] | None = None
    default_downsample_zyx: int = 4
    max_preview_voxels: int = 8_000_000

    @property
    def folder_path(self):
        return self.path


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


def _sorted_pngs(folder):
    files = [f for f in os.listdir(folder) if f.lower().endswith(".png")]
    files.sort()
    return [os.path.join(folder, f) for f in files]


def _lazy_slice(path):
    suffix = os.path.splitext(path)[1].lower()
    if suffix in {".tif", ".tiff"}:
        return tiff.imread(path)

    if suffix == ".png":
        image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if image is None:
            raise FileNotFoundError(f"Unable to read image slice '{path}'")
        if image.ndim == 3:
            if image.shape[2] == 1:
                image = image[:, :, 0]
            elif image.shape[2] == 3:
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            elif image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
            else:
                raise ValueError(f"Unsupported PNG channel count {image.shape[2]} in '{path}'")
        if image.ndim != 2:
            raise ValueError(f"Expected a 2D grayscale slice from '{path}', got shape {tuple(int(v) for v in image.shape)}")
        return image

    raise ValueError(f"Unsupported slice extension '{suffix}'")


def _make_lazy_volume_zyx(folder, source_type="tiff_stack"):
    if source_type == "tiff_stack":
        paths = _sorted_tiffs(folder)
    elif source_type == "png_stack":
        paths = _sorted_pngs(folder)
    else:
        raise ValueError(f"Unsupported stack source type '{source_type}'")

    if not paths:
        if source_type == "png_stack":
            raise FileNotFoundError("No PNG files found in folder")
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


def _downsampled_shape(shape_zyx, downsample_zyx):
    step = max(1, int(downsample_zyx))
    return tuple(int((int(v) + step - 1) // step) for v in shape_zyx)


def _extract_subvolume_from_array(array_zyx, downsample_zyx, crop_zyx):
    downsample_zyx = max(1, int(downsample_zyx))
    shape_ds = _downsampled_shape(array_zyx.shape, downsample_zyx)

    if crop_zyx is not None:
        z0, z1, y0, y1, x0, x1 = _center_crop_bounds(shape_ds, crop_zyx)
    else:
        z0, y0, x0 = 0, 0, 0
        z1, y1, x1 = shape_ds

    sub = np.asarray(
        array_zyx[
            z0 * downsample_zyx:z1 * downsample_zyx:downsample_zyx,
            y0 * downsample_zyx:y1 * downsample_zyx:downsample_zyx,
            x0 * downsample_zyx:x1 * downsample_zyx:downsample_zyx,
        ]
    )
    return sub, (z0, z1, y0, y1, x0, x1)


def _validate_numeric_3d_array(shape, dtype, source_name):
    if len(shape) != 3:
        raise ValueError(f"{source_name} must contain a 3D volume, got shape {tuple(int(v) for v in shape)}")
    if not np.issubdtype(np.dtype(dtype), np.number):
        raise ValueError(f"{source_name} must contain a numeric array, got dtype {dtype}")


def load_npy_volume(file_path: str):
    array_zyx = np.load(file_path, mmap_mode="r", allow_pickle=False)
    _validate_numeric_3d_array(array_zyx.shape, array_zyx.dtype, os.path.basename(file_path))
    return array_zyx


def list_h5_volume_datasets(file_path: str):
    datasets = []

    with h5py.File(file_path, "r") as handle:
        def visitor(name, obj):
            if not isinstance(obj, h5py.Dataset):
                return
            if len(obj.shape) != 3:
                return
            if not np.issubdtype(obj.dtype, np.number):
                return

            spacing = obj.attrs.get("spacing_zyx_mm")
            if spacing is not None:
                spacing = tuple(float(v) for v in np.asarray(spacing).reshape(-1))

            datasets.append(
                {
                    "path": f"/{name.lstrip('/')}",
                    "shape_zyx": tuple(int(v) for v in obj.shape),
                    "dtype": str(obj.dtype),
                    "spacing_zyx_mm": spacing,
                }
            )

        handle.visititems(visitor)

    return datasets


def _resolve_h5_dataset_path(file_path: str, dataset_path: str | None = None):
    datasets = list_h5_volume_datasets(file_path)
    if not datasets:
        raise ValueError("No 3D numeric datasets were found in the H5 file.")

    if dataset_path:
        normalized_path = dataset_path if dataset_path.startswith("/") else f"/{dataset_path}"
        for entry in datasets:
            if entry["path"] == normalized_path:
                return normalized_path, entry
        raise ValueError(f"H5 dataset '{normalized_path}' was not found or is not a 3D numeric volume.")

    if len(datasets) == 1:
        entry = datasets[0]
        return entry["path"], entry

    paths = ", ".join(entry["path"] for entry in datasets)
    raise ValueError(f"Multiple 3D datasets found in H5 file. Choose one of: {paths}")


def inspect_h5_volume(file_path: str, dataset_path: str | None = None):
    resolved_path, entry = _resolve_h5_dataset_path(file_path, dataset_path)
    info = dict(entry)
    info["dataset_path"] = resolved_path
    return info


def load_h5_volume(file_path: str, dataset_path: str | None = None):
    resolved_path, _entry = _resolve_h5_dataset_path(file_path, dataset_path)
    handle = h5py.File(file_path, "r")
    dataset = handle[resolved_path]
    try:
        _validate_numeric_3d_array(dataset.shape, dataset.dtype, f"{os.path.basename(file_path)}:{resolved_path}")
    except Exception:
        handle.close()
        raise
    return handle, dataset, resolved_path


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


def inspect_png_stack(folder_path: str):
    """Return shape/dtype metadata without loading the full PNG stack."""
    paths = _sorted_pngs(folder_path)
    if not paths:
        raise FileNotFoundError("No PNG files found in folder")

    sample = _lazy_slice(paths[0])
    return {
        "shape_zyx": (len(paths), *sample.shape),
        "dtype": str(sample.dtype),
        "slice_count": len(paths),
    }


def inspect_array_volume(file_path: str, file_type: str, dataset_path: str | None = None):
    file_type = file_type.strip().lower()

    if file_type == "npy":
        array_zyx = load_npy_volume(file_path)
        return {
            "shape_zyx": tuple(int(v) for v in array_zyx.shape),
            "dtype": str(array_zyx.dtype),
        }

    if file_type == "h5":
        return inspect_h5_volume(file_path, dataset_path)

    raise ValueError(f"Unsupported file type '{file_type}'")


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


def _resolve_surface_level(sub_zyx, level, default_mode="percentile"):
    if sub_zyx.size == 0:
        raise ValueError("ROI produced an empty volume")

    vmin = float(np.min(sub_zyx))
    vmax = float(np.max(sub_zyx))
    if not np.isfinite(vmin) or not np.isfinite(vmax):
        raise ValueError("ROI contains non-finite values")
    if vmax <= vmin:
        raise ValueError(
            f"ROI intensity range is flat ({vmin:g} to {vmax:g}); choose a different ROI or preprocess the SAM stack."
        )

    if level is None:
        if default_mode == "midpoint":
            candidate = vmin + 0.5 * (vmax - vmin)
        else:
            candidate = float(np.percentile(sub_zyx, 99.5))
    else:
        candidate = float(level)

    if not (vmin < candidate < vmax):
        fallback = vmin + 0.5 * (vmax - vmin)
        print(
            f"Requested marching-cubes level {candidate:g} is outside the data range "
            f"[{vmin:g}, {vmax:g}]; using {fallback:g} instead."
        )
        candidate = fallback

    return candidate


def _mesh_from_subvolume_zyx(sub_zyx, voxel_size_mm, downsample_zyx, bounds_zyx, level):
    if sub_zyx.size == 0:
        raise ValueError("ROI produced an empty volume")

    level = _resolve_surface_level(sub_zyx, level, default_mode="percentile")

    s = voxel_size_mm * downsample_zyx
    spacing = (s, s, s)
    z0, _z1, y0, _y1, x0, _x1 = bounds_zyx

    verts, faces, normals, values = marching_cubes(
        sub_zyx,
        level=level,
        spacing=spacing,
        allow_degenerate=False,
    )

    verts[:, 0] += z0 * s
    verts[:, 1] += y0 * s
    verts[:, 2] += x0 * s
    verts = np.ascontiguousarray(verts[:, [2, 1, 0]])

    mesh = o3d.geometry.TriangleMesh()
    mesh.vertices = o3d.utility.Vector3dVector(verts.astype(np.float64, copy=False))
    mesh.triangles = o3d.utility.Vector3iVector(faces.astype(np.int32, copy=False))
    mesh.compute_vertex_normals()
    return mesh, level


def load_ct_volume_preview(
    volume_source: VolumeSource,
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

    if volume_source.source_type in {"tiff_stack", "png_stack"}:
        vol = _make_lazy_volume_zyx(volume_source.path, volume_source.source_type)
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
        full_shape_zyx = tuple(int(v) for v in vol.shape)
        dtype = str(vol.dtype)
    else:
        if volume_source.source_type == "npy":
            array_zyx = load_npy_volume(volume_source.path)
        elif volume_source.source_type == "h5":
            handle, dataset, _resolved_path = load_h5_volume(volume_source.path, volume_source.dataset_path)
            array_zyx = dataset
        else:
            raise ValueError(f"Unsupported volume source type '{volume_source.source_type}'")

        try:
            effective_downsample = downsample_zyx
            shape_ds = _downsampled_shape(array_zyx.shape, effective_downsample)
            if crop_zyx is not None:
                z0, z1, y0, y1, x0, x1 = _center_crop_bounds(shape_ds, crop_zyx)
            else:
                z0, y0, x0 = 0, 0, 0
                z1, y1, x1 = shape_ds

            preview_voxels = int((z1 - z0) * (y1 - y0) * (x1 - x0))
            if preview_voxels > max_preview_voxels:
                guard_factor = int(np.ceil((preview_voxels / max_preview_voxels) ** (1.0 / 3.0)))
                guard_factor = max(2, guard_factor)
                effective_downsample *= guard_factor
                if crop_zyx is not None:
                    guarded_crop = tuple(max(1, int(np.ceil(v / guard_factor))) for v in crop_zyx)
                else:
                    guarded_crop = None
                sub_zyx, (z0, z1, y0, y1, x0, x1) = _extract_subvolume_from_array(
                    array_zyx,
                    effective_downsample,
                    guarded_crop,
                )
            else:
                sub_zyx, (z0, z1, y0, y1, x0, x1) = _extract_subvolume_from_array(
                    array_zyx,
                    effective_downsample,
                    crop_zyx,
                )

            full_shape_zyx = tuple(int(v) for v in array_zyx.shape)
            dtype = str(array_zyx.dtype)
        finally:
            if volume_source.source_type == "h5":
                handle.close()

    sub_zyx = _normalize_volume_to_uint8(sub_zyx)
    sub_xyz = np.ascontiguousarray(np.transpose(sub_zyx, (2, 1, 0)))

    metadata = {
        "shape_zyx": full_shape_zyx,
        "preview_shape_xyz": tuple(int(v) for v in sub_xyz.shape),
        "dtype": dtype,
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

    vol = _make_lazy_volume_zyx(folder_path, "tiff_stack")               # dask (Z,Y,X)
    vol_ds = vol[::downsample_zyx, ::downsample_zyx, ::downsample_zyx]

    z0, z1, y0, y1, x0, x1 = _center_crop_bounds(vol_ds.shape, crop_zyx)
    sub = vol_ds[z0:z1, y0:y1, x0:x1].compute()            # numpy array (small)

    return _mesh_from_subvolume_zyx(
        sub_zyx=sub,
        voxel_size_mm=voxel_size_mm,
        downsample_zyx=downsample_zyx,
        bounds_zyx=(z0, z1, y0, y1, x0, x1),
        level=level,
    )


def get_mesh_from_png_stack(
    folder_path: str,
    voxel_size_mm: float = 0.006937965888099794,
    downsample_zyx: int = 2,
    crop_zyx: tuple[int, int, int] = (256, 256, 256),
    level: float | None = None,
):
    vol = _make_lazy_volume_zyx(folder_path, "png_stack")
    vol_ds = vol[::downsample_zyx, ::downsample_zyx, ::downsample_zyx]

    z0, z1, y0, y1, x0, x1 = _center_crop_bounds(vol_ds.shape, crop_zyx)
    sub = vol_ds[z0:z1, y0:y1, x0:x1].compute()
    level = _resolve_surface_level(sub, level, default_mode="midpoint")

    return _mesh_from_subvolume_zyx(
        sub_zyx=sub,
        voxel_size_mm=voxel_size_mm,
        downsample_zyx=downsample_zyx,
        bounds_zyx=(z0, z1, y0, y1, x0, x1),
        level=level,
    )


def get_mesh_from_array_volume(
    file_path: str,
    file_type: str,
    voxel_size_mm: float = 0.006937965888099794,
    downsample_zyx: int = 2,
    crop_zyx: tuple[int, int, int] = (256, 256, 256),
    level: float | None = None,
    dataset_path: str | None = None,
):
    file_type = file_type.strip().lower()

    if file_type == "npy":
        array_zyx = load_npy_volume(file_path)
        handle = None
    elif file_type == "h5":
        handle, array_zyx, dataset_path = load_h5_volume(file_path, dataset_path)
    else:
        raise ValueError(f"Unsupported file type '{file_type}'")

    try:
        sub_zyx, bounds_zyx = _extract_subvolume_from_array(array_zyx, downsample_zyx, crop_zyx)
        return _mesh_from_subvolume_zyx(
            sub_zyx=sub_zyx,
            voxel_size_mm=voxel_size_mm,
            downsample_zyx=downsample_zyx,
            bounds_zyx=bounds_zyx,
            level=level,
        )
    finally:
        if handle is not None:
            handle.close()


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
