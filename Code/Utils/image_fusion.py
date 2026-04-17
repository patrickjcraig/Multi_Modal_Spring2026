import numpy as np
from skimage.metrics import structural_similarity


def normalize_image_uint8(image, lower_percentile=1.0, upper_percentile=99.0):
    array = np.asarray(image, dtype=np.float32)
    finite_mask = np.isfinite(array)
    if not np.any(finite_mask):
        return np.zeros(array.shape, dtype=np.uint8)

    finite_values = array[finite_mask]
    low = float(np.percentile(finite_values, lower_percentile))
    high = float(np.percentile(finite_values, upper_percentile))
    if not np.isfinite(low) or not np.isfinite(high) or high <= low:
        low = float(np.min(finite_values))
        high = float(np.max(finite_values))
        if not np.isfinite(low) or not np.isfinite(high) or high <= low:
            return np.zeros(array.shape, dtype=np.uint8)

    scaled = (array - low) * (255.0 / max(high - low, 1e-12))
    scaled[~finite_mask] = 0.0
    np.clip(scaled, 0.0, 255.0, out=scaled)
    return scaled.astype(np.uint8, copy=False)


def pca_fuse_images(base_image_uint8, overlay_image_uint8, valid_mask=None):
    base = np.asarray(base_image_uint8, dtype=np.float32) / 255.0
    overlay = np.asarray(overlay_image_uint8, dtype=np.float32) / 255.0
    if base.shape != overlay.shape:
        raise ValueError("PCA fusion images must share the same shape")

    if valid_mask is None:
        valid_mask = np.ones(base.shape, dtype=bool)
    else:
        valid_mask = np.asarray(valid_mask, dtype=bool)
        if valid_mask.shape != base.shape:
            raise ValueError("Fusion valid mask must match image shape")

    sample_count = int(np.count_nonzero(valid_mask))
    if sample_count < 2:
        weights = np.array([0.5, 0.5], dtype=np.float32)
        covariance = np.zeros((2, 2), dtype=np.float32)
        eigenvalues = np.zeros(2, dtype=np.float32)
    else:
        samples = np.column_stack((base[valid_mask], overlay[valid_mask]))
        covariance = np.cov(samples, rowvar=False).astype(np.float32, copy=False)
        eigenvalues, eigenvectors = np.linalg.eigh(covariance)
        principal = np.abs(eigenvectors[:, int(np.argmax(eigenvalues))]).astype(np.float32, copy=False)
        if float(np.sum(principal)) <= 1e-12:
            weights = np.array([0.5, 0.5], dtype=np.float32)
        else:
            weights = principal / float(np.sum(principal))

    fused = weights[0] * base + weights[1] * overlay
    if valid_mask is not None:
        fused = np.where(valid_mask, fused, base)

    fused_uint8 = np.clip(np.rint(fused * 255.0), 0.0, 255.0).astype(np.uint8)
    return fused_uint8, {
        "weights": (float(weights[0]), float(weights[1])),
        "covariance": covariance.tolist(),
        "eigenvalues": [float(v) for v in np.ravel(eigenvalues)],
        "valid_pixels": sample_count,
    }


def compute_similarity_metrics(reference_uint8, comparison_uint8, valid_mask=None):
    reference = np.asarray(reference_uint8, dtype=np.float32)
    comparison = np.asarray(comparison_uint8, dtype=np.float32)
    if reference.shape != comparison.shape:
        raise ValueError("Similarity inputs must share the same shape")

    if valid_mask is None:
        valid_mask = np.ones(reference.shape, dtype=bool)
    else:
        valid_mask = np.asarray(valid_mask, dtype=bool)
        if valid_mask.shape != reference.shape:
            raise ValueError("Similarity mask must match image shape")

    if int(np.count_nonzero(valid_mask)) < 2:
        return {
            "pixels": int(np.count_nonzero(valid_mask)),
            "mae": None,
            "rmse": None,
            "nrmse": None,
            "ssim": None,
            "psnr_db": None,
            "corrcoef": None,
        }

    ref_valid = reference[valid_mask]
    cmp_valid = comparison[valid_mask]
    diff = cmp_valid - ref_valid
    mae = float(np.mean(np.abs(diff)))
    mse = float(np.mean(np.square(diff)))
    rmse = float(np.sqrt(max(mse, 0.0)))
    dynamic_range = float(np.max(ref_valid) - np.min(ref_valid))
    nrmse = None if dynamic_range <= 1e-12 else float(rmse / dynamic_range)
    psnr_db = None if mse <= 1e-12 else float(20.0 * np.log10(255.0 / np.sqrt(mse)))

    ref_std = float(np.std(ref_valid))
    cmp_std = float(np.std(cmp_valid))
    if ref_std <= 1e-12 or cmp_std <= 1e-12:
        corrcoef = 1.0 if np.allclose(ref_valid, cmp_valid) else 0.0
    else:
        corrcoef = float(np.corrcoef(ref_valid, cmp_valid)[0, 1])

    rows, cols = np.nonzero(valid_mask)
    r0, r1 = int(np.min(rows)), int(np.max(rows)) + 1
    c0, c1 = int(np.min(cols)), int(np.max(cols)) + 1
    ref_crop = reference[r0:r1, c0:c1].copy()
    cmp_crop = comparison[r0:r1, c0:c1].copy()
    crop_mask = valid_mask[r0:r1, c0:c1]
    fill_value = float(np.mean(ref_valid))
    ref_crop[~crop_mask] = fill_value
    cmp_crop[~crop_mask] = fill_value
    ssim_range = float(max(np.max(ref_crop), np.max(cmp_crop)) - min(np.min(ref_crop), np.min(cmp_crop)))
    if ssim_range <= 1e-12:
        ssim_value = 1.0 if np.allclose(ref_crop, cmp_crop) else 0.0
    else:
        min_side = int(min(ref_crop.shape))
        if min_side < 3:
            ssim_value = None
        else:
            win_size = min(7, min_side)
            if win_size % 2 == 0:
                win_size -= 1
            ssim_value = float(
                structural_similarity(
                    ref_crop,
                    cmp_crop,
                    data_range=ssim_range,
                    win_size=win_size,
                )
            )

    return {
        "pixels": int(ref_valid.size),
        "mae": mae,
        "rmse": rmse,
        "nrmse": nrmse,
        "ssim": ssim_value,
        "psnr_db": psnr_db,
        "corrcoef": corrcoef,
    }
