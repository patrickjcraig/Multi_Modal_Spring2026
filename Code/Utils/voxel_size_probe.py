from __future__ import annotations

import configparser
import os
from dataclasses import dataclass

import numpy as np


@dataclass
class VoxelProbeResult:
    voxel_size_mm: float | None
    source: str | None = None
    note: str | None = None


def _parse_slice_txt_voxel(slice_txt_path: str) -> float | None:
    parser = configparser.ConfigParser()
    try:
        parser.read(slice_txt_path)
    except Exception:
        return None

    if not parser.has_section("VolumeData"):
        return None

    raw = parser.get("VolumeData", "voxel_size", fallback="").strip()
    if not raw:
        return None

    try:
        voxel = float(raw)
    except ValueError:
        return None

    if not np.isfinite(voxel) or voxel <= 0:
        return None

    return voxel


def _slice_txt_candidates(path: str) -> list[str]:
    path = os.path.abspath(path)
    dirs: list[str] = []

    if os.path.isdir(path):
        dirs.append(path)
        parent = os.path.dirname(path)
        if parent and parent != path:
            dirs.append(parent)
    else:
        base_dir = os.path.dirname(path)
        dirs.append(base_dir)
        parent = os.path.dirname(base_dir)
        if parent and parent != base_dir:
            dirs.append(parent)

    candidates: list[str] = []
    for directory in dirs:
        if not directory:
            continue
        candidates.append(os.path.join(directory, "slice.txt"))

    return candidates


def probe_voxel_size_from_slice_txt(path: str) -> VoxelProbeResult:
    for candidate in _slice_txt_candidates(path):
        if not os.path.isfile(candidate):
            continue
        voxel = _parse_slice_txt_voxel(candidate)
        if voxel is not None:
            source = f"slice.txt ({os.path.relpath(candidate, os.path.dirname(os.path.abspath(path)))})"
            return VoxelProbeResult(voxel_size_mm=voxel, source=source)
    return VoxelProbeResult(voxel_size_mm=None)


def probe_voxel_size_from_spacing_zyx(spacing_zyx_mm) -> VoxelProbeResult:
    if spacing_zyx_mm is None:
        return VoxelProbeResult(voxel_size_mm=None)

    try:
        spacing = np.asarray(spacing_zyx_mm, dtype=float).reshape(-1)
    except Exception:
        return VoxelProbeResult(voxel_size_mm=None)

    if spacing.size < 3:
        return VoxelProbeResult(voxel_size_mm=None)

    spacing = spacing[:3]
    if np.any(~np.isfinite(spacing)) or np.any(spacing <= 0):
        return VoxelProbeResult(voxel_size_mm=None)

    if np.allclose(spacing, spacing[0], rtol=1e-4, atol=1e-7):
        return VoxelProbeResult(
            voxel_size_mm=float(spacing[0]),
            source="H5 spacing_zyx_mm",
        )

    mean_spacing = float(np.mean(spacing))
    note = f"anisotropic spacing zyx={tuple(float(v) for v in spacing)}"
    return VoxelProbeResult(
        voxel_size_mm=mean_spacing,
        source="H5 spacing_zyx_mm (mean)",
        note=note,
    )


def probe_voxel_size(import_type: str, path: str, spacing_zyx_mm=None) -> VoxelProbeResult:
    import_type = (import_type or "").strip().lower()

    if import_type == "h5":
        from_spacing = probe_voxel_size_from_spacing_zyx(spacing_zyx_mm)
        if from_spacing.voxel_size_mm is not None:
            return from_spacing

    return probe_voxel_size_from_slice_txt(path)
