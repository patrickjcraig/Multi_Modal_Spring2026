import os
import numpy as np
import tifffile as tiff
import dask.array as da
from dask import delayed
import napari

from skimage.measure import marching_cubes

def sorted_tiffs(folder):
    files = [f for f in os.listdir(folder) if f.lower().endswith((".tif", ".tiff"))]
    files.sort()
    return [os.path.join(folder, f) for f in files]

def lazy_slice(path, yx_roi=None, downsample=1):
    a = tiff.imread(path)  # uint16
    if yx_roi is not None:
        y0, y1, x0, x1 = yx_roi
        a = a[y0:y1, x0:x1]
    if downsample > 1:
        a = a[::downsample, ::downsample]  # in-plane only
    return a

def make_lazy_volume(folder, yx_roi=None, downsample=1):
    paths = sorted_tiffs(folder)
    if not paths:
        raise FileNotFoundError("No tif/tiff files found")

    a0 = lazy_slice(paths[0], yx_roi=yx_roi, downsample=downsample)
    H, W = a0.shape
    dtype = a0.dtype

    lazy_arrays = [
        da.from_delayed(
            delayed(lazy_slice)(p, yx_roi=yx_roi, downsample=downsample),
            shape=(H, W),
            dtype=dtype,
        )
        for p in paths
    ]

    vol = da.stack(lazy_arrays, axis=0)  # (Z, Y, X)
    return vol

def center_crop_bounds(shape_zyx, crop_zyx):
    """Return z0:z1, y0:y1, x0:x1 centered in the volume."""
    Z, Y, X = shape_zyx
    cz, cy, cx = crop_zyx

    z0 = max(0, Z // 2 - cz // 2)
    y0 = max(0, Y // 2 - cy // 2)
    x0 = max(0, X // 2 - cx // 2)

    z1 = min(Z, z0 + cz)
    y1 = min(Y, y0 + cy)
    x1 = min(X, x0 + cx)

    return (z0, z1, y0, y1, x0, x1)

def mesh_from_subvolume(subvol_np, spacing_zyx_mm, level=None):
    """
    subvol_np: numpy array (Z,Y,X)
    spacing_zyx_mm: tuple (sz, sy, sx)
    level: iso threshold; if None, pick a high percentile as a starting point
    """
    print("Subvolume dtype:", subvol_np.dtype, "shape:", subvol_np.shape)
    vmin, vmax = int(subvol_np.min()), int(subvol_np.max())
    print("Subvolume range:", vmin, "to", vmax)

    if level is None:
        # Start-point heuristic; adjust after you see the mesh
        level = float(np.percentile(subvol_np, 99.5))
        print("Auto level (99.5th percentile):", level)
    else:
        print("Using level:", level)

    verts, faces, normals, values = marching_cubes(
        subvol_np,
        level=level,
        spacing=spacing_zyx_mm,  # IMPORTANT: makes geometry correct in mm
        allow_degenerate=False,
    )

    # napari expects faces as (N, 3) int
    faces = faces.astype(np.int32, copy=False)
    return verts, faces, normals, values, level

if __name__ == "__main__":
    #folder = os.path.join("..", "reconstruction_v1")
    folder = os.path.join("..", "120kv_FDK")

    yx_roi = None
    #yx_roi = (246, 246 + 1124, 0, 2938)
    
    loader_downsample = 1
    vol = make_lazy_volume(folder, yx_roi=yx_roi, downsample=loader_downsample)  # (Z,Y,X)

    view_downsample = 4
    vol_ds = vol[::view_downsample, ::view_downsample, ::view_downsample]  # (Z,Y,X)

    crop_zyx = (256, 256, 256)
    z0, z1, y0, y1, x0, x1 = center_crop_bounds(vol_ds.shape, crop_zyx)
    sub = vol_ds[z0:z1, y0:y1, x0:x1].compute()  # small numpy array

    base_voxel_mm = 0.006937965888099794

    s = base_voxel_mm * view_downsample
    spacing_zyx_mm = (s, s, s)
    print("Spacing (Z,Y,X) mm:", spacing_zyx_mm)

    verts, faces, normals, values, level = mesh_from_subvolume(
        subvol_np=sub,
        spacing_zyx_mm=spacing_zyx_mm,
        level=None,  # start with auto; you can set a fixed number later
    )

    # ----- Napari visualization -----
    import napari
    viewer = napari.Viewer()

    viewer.add_image(
        vol_ds,
        name="CT downsampled (iso)",
        contrast_limits=(vol_ds.min().compute(), vol_ds.max().compute()),
    )

    viewer.add_surface(
        (verts, faces),
        name=f"MC mesh (level={level:.1f})",
        opacity=0.8,
    )

    viewer.dims.ndisplay = 3
    napari.run()