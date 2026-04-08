from dataclasses import dataclass


@dataclass
class XRayImportParams:
    import_type: str
    path: str
    voxel_size_mm: float
    roi_xyz: tuple[int, int, int]
    downsampling: int
    pcd_points: int
    level: int
    dataset_path: str | None = None
