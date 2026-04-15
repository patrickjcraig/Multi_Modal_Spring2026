from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass
class GlobalScaleEstimate:
    scale: float
    method: str
    confidence: float
    detail: str


def _safe_point_array(pcd, max_points: int = 150_000) -> np.ndarray:
    points = np.asarray(pcd.points, dtype=float)
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError("Point cloud must contain Nx3 points.")
    if points.shape[0] <= max_points:
        return points

    keep = float(max_points) / float(max(points.shape[0], 1))
    keep = max(1e-4, min(1.0, keep))
    idx = np.random.default_rng(42).choice(points.shape[0], size=int(points.shape[0] * keep), replace=False)
    return points[idx]


def _project_to_image(points_xyz: np.ndarray, image_size: int = 512) -> tuple[np.ndarray, float]:
    centered = points_xyz - np.mean(points_xyz, axis=0, keepdims=True)
    _, singular_values, vh = np.linalg.svd(centered, full_matrices=False)
    if singular_values.size < 2 or singular_values[1] <= 1e-12:
        raise ValueError("Insufficient geometric variation for projection.")

    basis = vh[:2, :].T
    projected = centered @ basis

    mins = np.min(projected, axis=0)
    maxs = np.max(projected, axis=0)
    extents = np.maximum(maxs - mins, 1e-9)
    span = float(max(extents[0], extents[1]))

    usable = float(image_size - 1) * 0.88
    px_per_unit = usable / span
    center_2d = 0.5 * (mins + maxs)
    coords = (projected - center_2d) * px_per_unit + float(image_size - 1) * 0.5

    img = np.zeros((image_size, image_size), dtype=np.uint8)
    xi = np.clip(np.rint(coords[:, 0]).astype(int), 0, image_size - 1)
    yi = np.clip(np.rint(coords[:, 1]).astype(int), 0, image_size - 1)
    img[yi, xi] = 255

    try:
        import cv2

        img = cv2.GaussianBlur(img, (5, 5), 0)
        img = cv2.dilate(img, np.ones((3, 3), dtype=np.uint8), iterations=1)
    except Exception:
        # Keep pure NumPy image if OpenCV processing is unavailable.
        pass

    return img, px_per_unit


def _estimate_scale_from_homography(src_img: np.ndarray, dst_img: np.ndarray) -> tuple[float, float, str] | None:
    try:
        import cv2
    except Exception:
        return None

    orb = cv2.ORB_create(nfeatures=2500)
    kp1, des1 = orb.detectAndCompute(src_img, None)
    kp2, des2 = orb.detectAndCompute(dst_img, None)

    if des1 is None or des2 is None or len(kp1) < 12 or len(kp2) < 12:
        return None

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    pairs = matcher.knnMatch(des1, des2, k=2)

    good = []
    for pair in pairs:
        if len(pair) < 2:
            continue
        m, n = pair
        if m.distance < 0.78 * n.distance:
            good.append(m)

    if len(good) < 10:
        return None

    src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

    H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 4.0)
    if H is None:
        return None

    denom = float(H[2, 2]) if abs(float(H[2, 2])) > 1e-12 else 1.0
    A = (H[:2, :2] / denom).astype(float)
    svals = np.linalg.svd(A, compute_uv=False)
    if np.any(~np.isfinite(svals)):
        return None

    # Isotropic approximation of local affine scaling.
    scale = float(math.sqrt(max(1e-12, abs(np.linalg.det(A)))))

    inliers = int(mask.sum()) if mask is not None else 0
    inlier_ratio = float(inliers) / float(max(len(good), 1))
    anisotropy = float(max(svals) / max(min(svals), 1e-9))
    detail = f"matches={len(good)} inliers={inliers} anisotropy={anisotropy:.3f}"
    return scale, inlier_ratio, detail


def _estimate_scale_from_radius(points_src: np.ndarray, points_dst: np.ndarray) -> tuple[float, str]:
    src_center = np.mean(points_src, axis=0, keepdims=True)
    dst_center = np.mean(points_dst, axis=0, keepdims=True)

    src_r = np.linalg.norm(points_src - src_center, axis=1)
    dst_r = np.linalg.norm(points_dst - dst_center, axis=1)

    src_q = float(np.percentile(src_r, 80))
    dst_q = float(np.percentile(dst_r, 80))
    if src_q <= 1e-12 or not np.isfinite(src_q) or not np.isfinite(dst_q):
        raise ValueError("Could not compute a stable geometric fallback scale.")

    scale = dst_q / src_q
    detail = f"radius80 src={src_q:.6g} dst={dst_q:.6g}"
    return float(scale), detail


def estimate_global_scale(source_pcd, target_pcd, min_scale: float = 0.1, max_scale: float = 10.0) -> GlobalScaleEstimate:
    points_src = _safe_point_array(source_pcd)
    points_dst = _safe_point_array(target_pcd)

    if points_src.shape[0] < 100 or points_dst.shape[0] < 100:
        return GlobalScaleEstimate(
            scale=1.0,
            method="identity",
            confidence=0.0,
            detail="Too few points for scale estimation",
        )

    try:
        src_img, src_px = _project_to_image(points_src)
        dst_img, dst_px = _project_to_image(points_dst)
        homo = _estimate_scale_from_homography(src_img, dst_img)
        if homo is not None:
            pixel_scale, inlier_ratio, detail = homo
            world_scale = pixel_scale * (src_px / max(dst_px, 1e-12))
            if np.isfinite(world_scale) and min_scale <= world_scale <= max_scale and inlier_ratio >= 0.12:
                return GlobalScaleEstimate(
                    scale=float(world_scale),
                    method="homography",
                    confidence=float(min(1.0, max(0.0, inlier_ratio))),
                    detail=detail,
                )
    except Exception:
        # Fall back to geometric radius estimate below.
        pass

    fallback_scale, fallback_detail = _estimate_scale_from_radius(points_src, points_dst)
    fallback_scale = float(np.clip(fallback_scale, min_scale, max_scale))
    return GlobalScaleEstimate(
        scale=fallback_scale,
        method="radius80",
        confidence=0.35,
        detail=fallback_detail,
    )
