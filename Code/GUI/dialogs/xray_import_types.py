from dataclasses import dataclass


@dataclass
class VolumeImportParams:
    import_type: str
    path: str
    voxel_size_mm: float
    roi_xyz: tuple[int, int, int]
    downsampling: int
    pcd_points: int
    level: int
    dataset_path: str | None = None


XRayImportParams = VolumeImportParams
SAMImportParams = VolumeImportParams
