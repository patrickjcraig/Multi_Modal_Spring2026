import numpy as np


def _normalize_to_unit(array):
    arr = np.asarray(array)
    if arr.size == 0:
        return np.zeros(arr.shape, dtype=np.float32)

    if np.issubdtype(arr.dtype, np.floating):
        src = np.asarray(arr, dtype=np.float32)
        finite = src[np.isfinite(src)]
        if finite.size == 0:
            return np.zeros(arr.shape, dtype=np.float32)
        lo = float(np.min(finite))
        hi = float(np.max(finite))
    elif np.issubdtype(arr.dtype, np.integer):
        info = np.iinfo(arr.dtype)
        lo = float(info.min)
        hi = float(info.max)
        src = np.asarray(arr, dtype=np.float32)
    else:
        src = np.asarray(arr, dtype=np.float32)
        lo = float(np.min(src))
        hi = float(np.max(src))

    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        return np.zeros(arr.shape, dtype=np.float32)

    unit = (src - lo) / (hi - lo)
    np.clip(unit, 0.0, 1.0, out=unit)
    return unit.astype(np.float32, copy=False)


def apply_gamma_contrast_to_unit(unit, gamma=1.0, contrast=1.0):
    """Apply contrast then gamma to an image/volume already scaled to [0, 1]."""
    data = np.asarray(unit, dtype=np.float32)
    gamma = max(float(gamma), 1e-3)
    contrast = max(float(contrast), 1e-3)

    adjusted = (data - 0.5) * contrast + 0.5
    np.clip(adjusted, 0.0, 1.0, out=adjusted)

    # gamma > 1 darkens, gamma < 1 brightens.
    if abs(gamma - 1.0) > 1e-6:
        adjusted = np.power(adjusted, gamma, dtype=np.float32)

    np.clip(adjusted, 0.0, 1.0, out=adjusted)
    return adjusted


def apply_gamma_contrast_uint8(array, gamma=1.0, contrast=1.0):
    """Return a uint8 view with gamma/contrast enhancement applied."""
    unit = _normalize_to_unit(array)
    enhanced = apply_gamma_contrast_to_unit(unit, gamma=gamma, contrast=contrast)
    out = np.rint(enhanced * 255.0).astype(np.uint8)
    return out
