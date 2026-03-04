import os
import h5py
import dask.array as da
from fileimport import make_lazy_volume, center_crop_bounds

def save_dask_volume_to_h5(dask_vol, out_path,
                           dataset_name="volume",
                           spacing_zyx_mm=None,
                           chunk_size=(64, 256, 256)):

    print("Rechunking to:", chunk_size)
    dask_vol = dask_vol.rechunk(chunk_size)

    print("Saving to:", out_path)
    dask_vol.to_hdf5(
        out_path,
        f"/{dataset_name}",
        compression="gzip"
    )

    # Add metadata
    if spacing_zyx_mm is not None:
        with h5py.File(out_path, "a") as f:
            f[dataset_name].attrs["spacing_zyx_mm"] = spacing_zyx_mm

    print("H5 export complete.")


if __name__ == "__main__":

    folder = os.path.join("..", "reconstruction_v1")

    yx_roi = (246, 246 + 1124, 0, 2938)

    vol = make_lazy_volume(folder, yx_roi=yx_roi, downsample=1)
    print("Full volume shape:", vol.shape)

    # Taking sample part (smaller region than full stack)
    crop_zyx = (512, 512, 512)
    z0, z1, y0, y1, x0, x1 = center_crop_bounds(vol.shape, crop_zyx)

    subvol = vol[z0:z1, y0:y1, x0:x1]
    print("Subvolume shape:", subvol.shape)

    base_voxel_mm = 0.006937965888099794
    spacing_zyx_mm = (base_voxel_mm,
                      base_voxel_mm,
                      base_voxel_mm)

    output_path = "reconstruction_partial.h5"

    save_dask_volume_to_h5(
        subvol,
        output_path,
        dataset_name="ct_ic_volume",
        spacing_zyx_mm=spacing_zyx_mm,
        chunk_size=(64, 256, 256)
    )