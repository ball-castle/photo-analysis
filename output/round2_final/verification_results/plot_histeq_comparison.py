from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

base = Path(r"C:\Users\CAI BIN\Desktop\photo_analysis\output")
verify = base / "round2_final" / "verification_results"
paths = [
    base / "data" / "processed" / "dark_face_512.png",
    base / "results" / "histogram_equalized.png",
    verify / "matlab_histeq_default64.png",
    verify / "matlab_histeq_256.png",
]
labels = [
    "Input image",
    "Python CDF-min mapping",
    "MATLAB histeq(I), default 64 bins",
    "MATLAB histeq(I, 256)",
]
fig, axes = plt.subplots(2, 2, figsize=(9.0, 7.2), constrained_layout=True)
for ax, path, label in zip(axes.flat, paths, labels):
    with Image.open(path) as im:
        arr = np.asarray(im.convert("L"), dtype=np.uint8)
    ax.imshow(arr, cmap="gray", vmin=0, vmax=255)
    ax.set_title(label, fontsize=10)
    ax.axis("off")
fig.savefig(verify / "matlab_histeq_bins_comparison.png", dpi=180)
plt.close(fig)
