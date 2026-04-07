import cv2
import numpy as np
from pathlib import Path

# ---- calibration ----
SAM_UM_PER_PX = 1.0
CT_UM_PER_PX = 0.4631795192807952

UPSCALE_FACTOR = SAM_UM_PER_PX / CT_UM_PER_PX  # ~2.15898

# ---- file paths ----
base_dir = Path(__file__).resolve().parent
sam_path = base_dir / "w_AG5.png"          # change if needed
out_path = base_dir / "w_AG5_upscaled_to_ct_scale.png"

# ---- load image ----
sam = cv2.imread(str(sam_path), cv2.IMREAD_UNCHANGED)
if sam is None:
    raise FileNotFoundError(f"Could not load {sam_path}")

h, w = sam.shape[:2]

# ---- resize ----
new_w = int(round(w * UPSCALE_FACTOR))
new_h = int(round(h * UPSCALE_FACTOR))

sam_upscaled = cv2.resize(
    sam,
    (new_w, new_h),
    interpolation=cv2.INTER_CUBIC  # good for upscaling
)

# ---- save ----
ok = cv2.imwrite(str(out_path), sam_upscaled)
if not ok:
    raise IOError(f"Could not save {out_path}")

print(f"SAM original size : {w} x {h}")
print(f"Scale factor      : {UPSCALE_FACTOR:.6f}")
print(f"SAM resized size  : {new_w} x {new_h}")
print(f"Saved to          : {out_path}")