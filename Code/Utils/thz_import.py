from __future__ import annotations

from dataclasses import dataclass
import os

import numpy as np
from scipy.fft import fft, fftfreq
from scipy.interpolate import griddata


@dataclass(frozen=True)
class THzScanInfo:
    t2t_path: str
    cmt_path: str | None
    begin_ps: float
    dt_ps: float
    trace_samples: int | None
    resolution_x_mm: float | None
    resolution_y_mm: float | None
    size_x_mm: float | None
    size_y_mm: float | None


def find_companion_cmt(t2t_path: str) -> str | None:
    stem, _suffix = os.path.splitext(os.path.abspath(t2t_path))
    candidate = f"{stem}.cmt"
    if os.path.isfile(candidate):
        return candidate
    return None


def inspect_thz_scan(t2t_path: str, cmt_path: str | None = None) -> THzScanInfo:
    begin_ps, dt_ps, trace_samples = _parse_t2t_header(t2t_path)
    resolved_cmt = _resolve_cmt_path(t2t_path, cmt_path)
    cmt = parse_cmt_file(resolved_cmt) if resolved_cmt else {}
    return THzScanInfo(
        t2t_path=os.path.abspath(t2t_path),
        cmt_path=resolved_cmt,
        begin_ps=begin_ps,
        dt_ps=dt_ps,
        trace_samples=trace_samples,
        resolution_x_mm=_coerce_positive_float(cmt.get("ResolutionX")),
        resolution_y_mm=_coerce_positive_float(cmt.get("ResolutionY")),
        size_x_mm=_coerce_positive_float(cmt.get("SizeX")),
        size_y_mm=_coerce_positive_float(cmt.get("SizeY")),
    )


def build_thz_fft_npy_volume(
    t2t_path: str,
    target_freq_thz: float,
    output_dir: str,
    cmt_path: str | None = None,
    pseudo_depth_mm: float = 0.0,
) -> dict:
    t2t_path = os.path.abspath(t2t_path)
    if not os.path.isfile(t2t_path):
        raise FileNotFoundError(f"THz trace file was not found: {t2t_path}")

    resolved_cmt = _resolve_cmt_path(t2t_path, cmt_path)
    cmt = parse_cmt_file(resolved_cmt) if resolved_cmt else {}

    begin_ps, dt_ps, trace_samples = _parse_t2t_header(t2t_path)
    raw_rows = np.loadtxt(t2t_path, delimiter=",", skiprows=4, dtype=np.float32, ndmin=2)
    if raw_rows.shape[1] < 5:
        raise ValueError("THz trace file must contain X, Y, Z and at least one time-domain sample.")

    # The exporter keeps every other row starting at the first row to use the
    # magnitude traces and drop the interleaved phase rows.
    amplitude_rows = np.ascontiguousarray(raw_rows[::2])
    if amplitude_rows.size == 0:
        raise ValueError("The THz trace file did not contain any usable FFT rows.")

    signal_matrix = amplitude_rows[:, 3:]
    if signal_matrix.shape[1] <= 1:
        raise ValueError("The THz trace file does not contain enough time samples for an FFT image.")

    time_step_s = float(dt_ps) * 1e-12
    target_freq_hz = float(target_freq_thz) * 1e12
    freqs_hz = fftfreq(signal_matrix.shape[1], d=time_step_s)
    positive_indices = np.flatnonzero(freqs_hz >= 0.0)
    if positive_indices.size == 0:
        raise ValueError("Unable to derive a non-negative frequency axis from the THz trace file.")

    positive_freqs_hz = freqs_hz[positive_indices]
    positive_index = int(np.argmin(np.abs(positive_freqs_hz - target_freq_hz)))
    freq_index = int(positive_indices[positive_index])
    actual_freq_hz = float(freqs_hz[freq_index])

    fft_values = fft(signal_matrix, axis=1)
    fft_amplitudes = np.abs(fft_values[:, freq_index]).astype(np.float32, copy=False)

    x_mm = np.abs(amplitude_rows[:, 0].astype(np.float64, copy=False)) / 10000.0
    y_mm = amplitude_rows[:, 1].astype(np.float64, copy=False) / 10000.0

    resolution_x_mm = _coerce_positive_float(cmt.get("ResolutionX"))
    resolution_y_mm = _coerce_positive_float(cmt.get("ResolutionY"))
    if resolution_x_mm is None:
        resolution_x_mm = _infer_axis_step_mm(x_mm)
    if resolution_y_mm is None:
        resolution_y_mm = _infer_axis_step_mm(y_mm)
    if resolution_x_mm is None or resolution_y_mm is None:
        raise ValueError("Unable to infer the THz scan pixel spacing from the .cmt file or raw coordinates.")

    image_yx, image_meta = _rasterize_fft_image(
        x_mm=x_mm,
        y_mm=y_mm,
        fft_amplitudes=fft_amplitudes,
        resolution_x_mm=resolution_x_mm,
        resolution_y_mm=resolution_y_mm,
    )

    pixel_size_mm = float((resolution_x_mm + resolution_y_mm) * 0.5)
    pseudo_depth_mm = max(float(pseudo_depth_mm), 0.0)
    if pseudo_depth_mm > 0.0:
        volume_zyx, pseudo_meta = _build_height_map_volume(
            image_yx=image_yx,
            pixel_size_mm=pixel_size_mm,
            pseudo_depth_mm=pseudo_depth_mm,
        )
        volume_kind = "height_map"
    else:
        volume_zyx = image_yx[np.newaxis, :, :].astype(np.float32, copy=False)
        pseudo_meta = {
            "z_slices": 1,
            "depth_mm": pixel_size_mm,
        }
        volume_kind = "single_slice"

    os.makedirs(output_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(t2t_path))[0]
    freq_label = f"{actual_freq_hz * 1e-12:.3f}".replace(".", "p")
    npy_path = os.path.join(output_dir, f"{stem}_fft_{freq_label}THz.npy")
    np.save(npy_path, volume_zyx, allow_pickle=False)

    size_x_mm = _coerce_positive_float(cmt.get("SizeX"))
    size_y_mm = _coerce_positive_float(cmt.get("SizeY"))
    return {
        "npy_path": npy_path,
        "t2t_path": t2t_path,
        "cmt_path": resolved_cmt,
        "target_freq_thz": float(target_freq_thz),
        "actual_freq_thz": actual_freq_hz * 1e-12,
        "begin_ps": begin_ps,
        "time_step_ps": dt_ps,
        "trace_samples": int(signal_matrix.shape[1]),
        "raw_row_count": int(raw_rows.shape[0]),
        "fft_point_count": int(amplitude_rows.shape[0]),
        "resolution_x_mm": float(resolution_x_mm),
        "resolution_y_mm": float(resolution_y_mm),
        "pixel_size_mm": pixel_size_mm,
        "size_x_mm": size_x_mm,
        "size_y_mm": size_y_mm,
        "grid_shape_xy": (int(image_meta["nx"]), int(image_meta["ny"])),
        "missing_pixels": int(image_meta["missing_pixels"]),
        "extent_x_mm": float(image_meta["extent_x_mm"]),
        "extent_y_mm": float(image_meta["extent_y_mm"]),
        "scaled_pixel_map_ready": bool(image_meta["scaled_pixel_map_ready"]),
        "volume_kind": volume_kind,
        "pseudo_depth_mm": float(pseudo_meta["depth_mm"]),
        "z_slices": int(pseudo_meta["z_slices"]),
    }


def parse_cmt_file(cmt_path: str) -> dict[str, str]:
    if not cmt_path:
        return {}
    cmt_path = os.path.abspath(cmt_path)
    if not os.path.isfile(cmt_path):
        raise FileNotFoundError(f"THz metadata file was not found: {cmt_path}")

    parsed: dict[str, str] = {}
    with open(cmt_path, "r", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or ":" not in line:
                continue
            key, value = line.split(":", 1)
            parsed[key.strip()] = value.strip()
    return parsed


def _parse_t2t_header(t2t_path: str) -> tuple[float, float, int | None]:
    with open(t2t_path, "r", encoding="utf-8", errors="replace") as handle:
        header_lines = [handle.readline().strip() for _ in range(4)]
        first_trace_line = handle.readline().strip()

    if len(header_lines) < 4 or not header_lines[0].startswith("Pr-TF-File"):
        raise ValueError("Unsupported THz trace file header.")

    trace_row = [part.strip() for part in header_lines[2].split(",")]
    if len(trace_row) < 3 or trace_row[0].upper() != "TRACE":
        raise ValueError("Unable to parse THz timing metadata from the trace header.")

    begin_ps = float(trace_row[1])
    dt_ps = float(trace_row[2])

    trace_samples = None
    data_row = [part.strip() for part in header_lines[3].split(",")]
    if len(data_row) >= 4 and data_row[3].lower() == "data":
        first_trace_values = [part.strip() for part in first_trace_line.split(",") if part.strip()]
        if len(first_trace_values) > 3:
            trace_samples = len(first_trace_values) - 3
    return begin_ps, dt_ps, trace_samples


def _resolve_cmt_path(t2t_path: str, cmt_path: str | None) -> str | None:
    if cmt_path:
        candidate = os.path.abspath(cmt_path)
        if not os.path.isfile(candidate):
            raise FileNotFoundError(f"Selected THz metadata file was not found: {candidate}")
        return candidate
    return find_companion_cmt(t2t_path)


def _coerce_positive_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        numeric = float(str(value).split()[0])
    except (TypeError, ValueError, IndexError):
        return None
    if not np.isfinite(numeric) or numeric <= 0.0:
        return None
    return float(numeric)


def _infer_axis_step_mm(axis_mm: np.ndarray) -> float | None:
    rounded = np.unique(np.round(np.asarray(axis_mm, dtype=np.float64), 4))
    if rounded.size < 2:
        return None
    deltas = np.diff(np.sort(rounded))
    deltas = deltas[deltas > 1e-6]
    if deltas.size == 0:
        return None
    return float(np.median(deltas))


def _rasterize_fft_image(
    x_mm: np.ndarray,
    y_mm: np.ndarray,
    fft_amplitudes: np.ndarray,
    resolution_x_mm: float,
    resolution_y_mm: float,
) -> tuple[np.ndarray, dict]:
    x_min = float(np.min(x_mm))
    x_max = float(np.max(x_mm))
    y_min = float(np.min(y_mm))
    y_max = float(np.max(y_mm))

    nx = int(np.round((x_max - x_min) / float(resolution_x_mm))) + 1
    ny = int(np.round((y_max - y_min) / float(resolution_y_mm))) + 1
    nx = max(nx, 1)
    ny = max(ny, 1)

    x_idx = np.clip(np.round((x_mm - x_min) / float(resolution_x_mm)).astype(int), 0, nx - 1)
    y_idx = np.clip(np.round((y_mm - y_min) / float(resolution_y_mm)).astype(int), 0, ny - 1)

    image_yx = np.zeros((ny, nx), dtype=np.float32)
    sample_counts = np.zeros((ny, nx), dtype=np.int32)
    np.add.at(image_yx, (y_idx, x_idx), fft_amplitudes)
    np.add.at(sample_counts, (y_idx, x_idx), 1)

    filled = sample_counts > 0
    if np.any(filled):
        image_yx[filled] /= sample_counts[filled].astype(np.float32, copy=False)

    missing_pixels = int(np.count_nonzero(~filled))
    if missing_pixels and np.any(filled):
        grid_x_mm = x_min + np.arange(nx, dtype=np.float32) * np.float32(resolution_x_mm)
        grid_y_mm = y_min + np.arange(ny, dtype=np.float32) * np.float32(resolution_y_mm)
        grid_x, grid_y = np.meshgrid(grid_x_mm, grid_y_mm)

        points = np.column_stack((x_mm, y_mm))
        interpolated = griddata(points, fft_amplitudes, (grid_x, grid_y), method="linear")
        if interpolated is not None:
            image_yx[~filled] = np.nan_to_num(
                interpolated[~filled],
                nan=0.0,
                posinf=0.0,
                neginf=0.0,
            ).astype(np.float32, copy=False)

    return image_yx, {
        "nx": nx,
        "ny": ny,
        "missing_pixels": missing_pixels,
        "extent_x_mm": (nx - 1) * float(resolution_x_mm),
        "extent_y_mm": (ny - 1) * float(resolution_y_mm),
        "scaled_pixel_map_ready": nx > 1 and ny > 1 and resolution_x_mm > 0.0 and resolution_y_mm > 0.0,
    }


def _build_height_map_volume(
    image_yx: np.ndarray,
    pixel_size_mm: float,
    pseudo_depth_mm: float,
) -> tuple[np.ndarray, dict]:
    nz = max(2, int(np.ceil(float(pseudo_depth_mm) / float(pixel_size_mm))))
    actual_depth_mm = float(nz) * float(pixel_size_mm)

    image = np.asarray(image_yx, dtype=np.float32)
    if image.size == 0:
        return np.zeros((nz, 1, 1), dtype=np.float32), {"z_slices": nz, "depth_mm": actual_depth_mm}

    lo, hi = np.percentile(image, (1.0, 99.5))
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        normalized = np.zeros_like(image, dtype=np.float32)
    else:
        normalized = np.clip((image - float(lo)) / float(hi - lo), 0.0, 1.0).astype(np.float32, copy=False)

    height_voxels = np.clip(
        np.rint(normalized * float(nz - 1)).astype(np.int32, copy=False) + 1,
        1,
        nz,
    )

    volume_zyx = np.zeros((nz, image.shape[0], image.shape[1]), dtype=np.float32)
    z_indices = np.arange(nz, dtype=np.int32)[:, None, None]
    volume_zyx[z_indices < height_voxels[None, :, :]] = 1.0
    return volume_zyx, {"z_slices": nz, "depth_mm": actual_depth_mm}
