"""Run the reproducible frequency-domain image-enhancement experiment."""

from __future__ import annotations

import csv
import json
import platform
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from src.frequency_filters import (
    apply_frequency_filter,
    dominant_peak_pairs,
    gaussian_notch_reject,
    high_frequency_emphasis,
    manual_dft2,
    psnr,
    radial_filter,
    to_uint8,
)


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "data" / "source"
RESULTS_DIR = ROOT / "results"
FILTERS = ("ideal", "butterworth", "gaussian")
CUTOFFS = (8.0, 16.0, 32.0, 64.0)
NOISE_SEED = 20261106
NOISE_SIGMA = 20.0

# Coordinates are manual selections from the centered log spectra, in signed
# FFT-bin offsets (row v, column u). Each point selects a conjugate pair.
REAL_NOTCH_CONFIG = {
    "7.PNG": {"centers": [(13, 22), (25, -44)], "d0": 3.0},
    "10.jpg": {
        # First pass: the four isolated carrier/sum/difference peaks. Second
        # pass: the remaining isolated peak at (1, 125); broaden D0 to cover
        # the visible side-lobes around the carrier clusters.
        "centers": [
            (61, -83), (62, 82), (2, 165), (123, -1), (1, 125),
        ],
        "d0": 8.0,
    },
    "11.jpg": {
        # The visible horizontal-stripe fundamental and its in-band harmonics.
        "centers": [(25, 0), (51, 0), (75, 0)],
        "d0": 5.0,
    },
    "16.jpg": {"centers": [(0, 16), (5, 5)], "d0": 3.0},
}
NOTCH_SWEEP = (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0)
SYNTHETIC_SIDE_BAND = 2


def load_gray(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("L"), dtype=np.float64)


def save_gray(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(to_uint8(image), mode="L").save(path)


def display_response(image: np.ndarray) -> np.ndarray:
    """Robustly stretch a signed high-pass response for display only."""
    low, high = np.percentile(image, (1.0, 99.0))
    if high <= low:
        return np.zeros_like(image)
    return np.clip((image - low) / (high - low), 0.0, 1.0)


def log_spectrum(image: np.ndarray, shifted: bool = True) -> np.ndarray:
    spectrum = np.fft.fft2(image)
    if shifted:
        spectrum = np.fft.fftshift(spectrum)
    return np.log1p(np.abs(spectrum))


def save_binary_spectrum(results: Path) -> dict[str, float]:
    image = np.zeros((256, 256), dtype=np.float64)
    image[120:136, 126:130] = 1.0  # 16 rows by 4 columns, centered.
    direct = manual_dft2(image)
    fft = np.fft.fft2(image)
    max_error = float(np.max(np.abs(direct - fft)))

    shifted = np.fft.fftshift(fft)
    restored = np.fft.ifftshift(shifted)
    reconstructed = np.fft.ifft2(restored).real
    reconstruction_error = float(np.max(np.abs(reconstructed - image)))

    figure, axes = plt.subplots(2, 3, figsize=(13, 8), constrained_layout=True)
    axes[0, 0].imshow(image, cmap="gray", vmin=0, vmax=1)
    axes[0, 0].set_title("16 × 4 二值矩形")
    axes[0, 0].axis("off")

    unshifted_mag = np.log1p(np.abs(fft))
    unshifted_phase = np.angle(fft)
    shifted_mag = np.log1p(np.abs(shifted))
    shifted_phase = np.angle(shifted)
    plot_data = [
        (axes[0, 1], unshifted_mag, "未移位幅度谱 log(1+|F|)", "magma"),
        (axes[0, 2], unshifted_phase, "未移位相位谱", "twilight"),
        (axes[1, 0], shifted_mag, "fftshift 后幅度谱", "magma"),
        (axes[1, 1], shifted_phase, "fftshift 后相位谱", "twilight"),
    ]
    for axis, data, title, cmap in plot_data:
        low, high = (-np.pi, np.pi) if "相位" in title else (0, float(np.max(data)))
        im = axis.imshow(data, cmap=cmap, vmin=low, vmax=high)
        axis.set_title(title)
        axis.set_xlabel("列频率索引")
        axis.set_ylabel("行频率索引")
        figure.colorbar(im, ax=axis, fraction=0.046, pad=0.03)
    axes[1, 2].axis("off")
    axes[1, 2].text(
        0.02,
        0.95,
        "说明\n\n"
        "未移位频谱的零频位于左上角。\n"
        "fftshift 将零频移到中心；\n"
        "ifftshift 还原后可直接逆变换。\n\n"
        f"手写 DFT 最大误差：{max_error:.3e}\n"
        f"逆变换重建最大误差：{reconstruction_error:.3e}",
        va="top",
        fontsize=11,
    )
    figure.savefig(results / "binary_fft_spectrum.png", dpi=180)
    plt.close(figure)
    save_gray(results / "binary_rectangle.png", image * 255.0)
    return {
        "manual_dft_max_abs_error": max_error,
        "inverse_reconstruction_max_abs_error": reconstruction_error,
    }


def save_spectrum_comparison(clean: np.ndarray, noisy: np.ndarray, results: Path) -> None:
    figure, axes = plt.subplots(2, 2, figsize=(10, 8), constrained_layout=True)
    axes[0, 0].imshow(clean, cmap="gray", vmin=0, vmax=255)
    axes[0, 0].set_title("原始 256×256 灰度图")
    axes[0, 1].imshow(noisy, cmap="gray", vmin=0, vmax=255)
    axes[0, 1].set_title(f"加入高斯噪声 σ={NOISE_SIGMA:g}")
    for axis, data, title in (
        (axes[1, 0], clean, "原图中心化幅度谱 log(1+|F|)"),
        (axes[1, 1], noisy, "含噪图中心化幅度谱 log(1+|F|)"),
    ):
        spectrum = log_spectrum(data)
        image_plot = axis.imshow(spectrum, cmap="magma")
        axis.set_title(title)
        figure.colorbar(image_plot, ax=axis, fraction=0.046, pad=0.03)
    for axis in axes.ravel():
        axis.axis("off")
    figure.suptitle("高斯噪声加入前后的频谱", fontsize=14)
    figure.savefig(results / "gaussian_noise_spectra.png", dpi=180)
    plt.close(figure)


def save_ideal_ringing_demo(scene: np.ndarray, results: Path) -> dict[str, int]:
    # Select a strong edge in the central scene region, then compare a crop and
    # its cross-section under the same cutoff radius.
    region = np.abs(np.diff(scene[80:175, 30:160], axis=1))
    relative_row, relative_column = np.unravel_index(np.argmax(region), region.shape)
    row = int(relative_row + 80)
    edge_column = int(relative_column + 31)
    d0 = 16.0
    ideal = apply_frequency_filter(scene, radial_filter(scene.shape, d0, "ideal_lp"))
    gaussian = apply_frequency_filter(scene, radial_filter(scene.shape, d0, "gaussian_lp"))

    row0, row1 = max(0, row - 10), min(scene.shape[0], row + 11)
    col0, col1 = max(0, edge_column - 22), min(scene.shape[1], edge_column + 23)
    crop = (slice(row0, row1), slice(col0, col1))
    x_values = np.arange(col0, col1)
    figure, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    for axis, image, title in (
        (axes[0, 0], scene, "原始场景（局部边缘位置）"),
        (axes[0, 1], ideal, f"理想低通 D0={d0:g}（裁剪）"),
        (axes[1, 0], gaussian, f"高斯低通 D0={d0:g}（裁剪）"),
    ):
        axis.imshow(image[crop], cmap="gray", vmin=0, vmax=255)
        axis.axvline(edge_column - col0, color="#d62728", linewidth=1, linestyle="--")
        axis.set_title(title)
        axis.axis("off")
    axes[1, 1].plot(x_values, scene[row, col0:col1], label="原图", color="#444444")
    axes[1, 1].plot(x_values, ideal[row, col0:col1], label="理想低通", color="#c44e52")
    axes[1, 1].plot(x_values, gaussian[row, col0:col1], label="高斯低通", color="#1c6e8c")
    axes[1, 1].axvline(edge_column, color="#777777", linestyle="--", linewidth=1)
    axes[1, 1].set_title(f"第 {row} 行边缘剖面（红线为强边缘）")
    axes[1, 1].set_xlabel("列坐标")
    axes[1, 1].set_ylabel("灰度")
    axes[1, 1].grid(alpha=0.25)
    axes[1, 1].legend(frameon=False)
    figure.savefig(results / "ideal_lowpass_ringing.png", dpi=180)
    plt.close(figure)
    return {"edge_row": row, "edge_column": edge_column, "D0_bins": int(d0)}


def run_gaussian_noise(results: Path) -> tuple[list[dict[str, object]], np.ndarray, np.ndarray]:
    clean = load_gray(SOURCE_DIR / "cameraman.tif")
    if clean.shape != (256, 256):
        raise ValueError(f"cameraman.tif must be 256x256; got {clean.shape}")
    rng = np.random.default_rng(NOISE_SEED)
    noisy = np.clip(clean + rng.normal(0.0, NOISE_SIGMA, clean.shape), 0.0, 255.0)
    save_gray(results / "cameraman_gaussian_noisy.png", noisy)
    save_spectrum_comparison(clean, noisy, results)
    ringing_location = save_ideal_ringing_demo(clean, results)

    rows: list[dict[str, object]] = []
    filtered_images: dict[tuple[str, float], np.ndarray] = {}
    for family in FILTERS:
        for cutoff in CUTOFFS:
            mask = radial_filter(clean.shape, cutoff, family + "_lp", order=2)
            start = time.perf_counter()
            filtered = apply_frequency_filter(noisy, mask)
            elapsed = time.perf_counter() - start
            score = psnr(clean, filtered)
            filtered_images[(family, cutoff)] = filtered
            save_gray(results / "lowpass" / f"{family}_D0_{cutoff:g}.png", filtered)
            rows.append(
                {
                    "filter": family,
                    "D0_bins": cutoff,
                    "order": 2 if family == "butterworth" else "n/a",
                    "PSNR_dB": score,
                    "MSE": float(np.mean((clean - filtered) ** 2)),
                    "runtime_seconds": elapsed,
                    "reference": "cameraman.tif before added Gaussian noise",
                }
            )

    with (results / "gaussian_lowpass_metrics.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    noisy_psnr = psnr(clean, noisy)
    figure, axes = plt.subplots(3, 4, figsize=(14, 10), constrained_layout=True)
    for row_index, family in enumerate(FILTERS):
        for column_index, cutoff in enumerate(CUTOFFS):
            output = filtered_images[(family, cutoff)]
            score = psnr(clean, output)
            axis = axes[row_index, column_index]
            axis.imshow(output, cmap="gray", vmin=0, vmax=255)
            axis.set_title(f"{family.title()} LP · D0={cutoff:g}\nPSNR={score:.2f} dB")
            axis.axis("off")
    figure.suptitle(
        f"高斯噪声低通结果（σ={NOISE_SIGMA:g}，seed={NOISE_SEED}；含噪 PSNR={noisy_psnr:.2f} dB）",
        fontsize=14,
    )
    figure.savefig(results / "gaussian_lowpass_grid.png", dpi=180)
    plt.close(figure)

    summary = {
        "reference": "cameraman.tif before added Gaussian noise",
        "noise_model": "independent zero-mean Gaussian, then clipped to [0,255]",
        "sigma": NOISE_SIGMA,
        "seed": NOISE_SEED,
        "noisy_psnr_db": noisy_psnr,
        "ideal_lowpass_ringing_edge": ringing_location,
    }
    (results / "gaussian_noise_metadata.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return rows, clean, noisy


def run_highpass(results: Path, scene: np.ndarray) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    filtered_images: dict[tuple[str, float], np.ndarray] = {}
    for family in FILTERS:
        for cutoff in CUTOFFS:
            mask = radial_filter(scene.shape, cutoff, family + "_hp", order=2)
            response = apply_frequency_filter(scene, mask)
            filtered_images[(family, cutoff)] = response
            save_gray(results / "highpass" / f"{family}_D0_{cutoff:g}_stretched.png", display_response(response) * 255.0)
            rows.append(
                {
                    "filter": family,
                    "D0_bins": cutoff,
                    "order": 2 if family == "butterworth" else "n/a",
                    "response_min": float(response.min()),
                    "response_max": float(response.max()),
                    "display_mapping": "1st-99th percentile linear stretch for PNG; CSV stores only raw response min/max",
                }
            )

    with (results / "highpass_parameters.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    figure, axes = plt.subplots(3, 4, figsize=(14, 10), constrained_layout=True)
    for row_index, family in enumerate(FILTERS):
        for column_index, cutoff in enumerate(CUTOFFS):
            axis = axes[row_index, column_index]
            axis.imshow(display_response(filtered_images[(family, cutoff)]), cmap="gray", vmin=0, vmax=1)
            axis.set_title(f"{family.title()} HP · D0={cutoff:g}")
            axis.axis("off")
    figure.suptitle("自然场景高通响应（每幅响应单独做 1%–99% 显示拉伸）", fontsize=14)
    figure.savefig(results / "highpass_grid.png", dpi=180)
    plt.close(figure)

    # HFE retains a low-frequency baseline while strengthening high-frequency detail.
    hfe_mask = high_frequency_emphasis(
        scene.shape, d0=24.0, a=0.6, b=1.4, family="butterworth", order=2
    )
    enhanced = apply_frequency_filter(scene, hfe_mask)
    save_gray(results / "high_frequency_emphasis.png", enhanced)
    figure, axes = plt.subplots(1, 3, figsize=(13, 4.5), constrained_layout=True)
    axes[0].imshow(scene, cmap="gray", vmin=0, vmax=255)
    axes[0].set_title("原始 cameraman.tif")
    axes[1].imshow(apply_frequency_filter(scene, radial_filter(scene.shape, 24.0, "butterworth_hp", 2)), cmap="gray")
    axes[1].set_title("巴特沃斯高通响应（自动显示范围）")
    axes[2].imshow(enhanced, cmap="gray", vmin=0, vmax=255)
    axes[2].set_title("高频强调：a=0.6, b=1.4, D0=24, n=2")
    for axis in axes:
        axis.axis("off")
    figure.savefig(results / "high_frequency_emphasis_comparison.png", dpi=180)
    plt.close(figure)
    return rows


def synthetic_modulated_noise(
    shape: tuple[int, int], center: tuple[int, int], side_band: int, amplitude: float = 18.0
) -> np.ndarray:
    """Known sinusoidal interference with two nearby modulation sidebands."""
    height, width = shape
    v, u = center
    rows, columns = np.mgrid[0:height, 0:width]
    carrier_phase = 2.0 * np.pi * (u * columns / width + v * rows / height)
    modulation = np.cos(2.0 * np.pi * side_band * columns / width)
    return amplitude * np.cos(carrier_phase) * (1.0 + 0.5 * modulation)


def plot_peaks(
    image: np.ndarray,
    selected_centers: list[tuple[int, int]],
    title: str,
    path: Path,
) -> None:
    spectrum = log_spectrum(image)
    height, width = image.shape
    figure, axis = plt.subplots(figsize=(8.5, 6.0), constrained_layout=True)
    extent = (-(width // 2) - 0.5, (width - 1 - width // 2) + 0.5,
              -(height // 2) - 0.5, (height - 1 - height // 2) + 0.5)
    image_plot = axis.imshow(spectrum, origin="lower", extent=extent, cmap="magma")
    for index, (v, u) in enumerate(selected_centers, start=1):
        axis.scatter([u, -u], [v, -v], marker="o", s=46, facecolors="none", edgecolors="cyan", linewidths=1.3)
        axis.annotate(str(index), (u, v), xytext=(4, 4), textcoords="offset points", color="white", fontsize=9)
    axis.set_title(title)
    axis.set_xlabel("水平频率 u（bin）")
    axis.set_ylabel("垂直频率 v（bin）")
    figure.colorbar(image_plot, ax=axis, label="log(1 + |F|)")
    figure.savefig(path, dpi=180)
    plt.close(figure)


def run_notch_challenge(results: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    challenge_files = ("7.PNG", "10.jpg", "11.jpg", "16.jpg")
    peak_rows: list[dict[str, object]] = []
    synthetic_rows: list[dict[str, object]] = []
    actual_rows: list[dict[str, object]] = []
    notch_outputs: list[tuple[str, np.ndarray, np.ndarray, np.ndarray, float]] = []

    for image_index, filename in enumerate(challenge_files):
        original = load_gray(SOURCE_DIR / filename)
        height, width = original.shape
        peaks = dominant_peak_pairs(original, count=16, min_radius=6.0)
        for rank, (v, u, magnitude) in enumerate(peaks, start=1):
            peak_rows.append(
                {
                    "image": filename,
                    "height": height,
                    "width": width,
                    "rank": rank,
                    "row_frequency_v": v,
                    "column_frequency_u": u,
                    "fft_magnitude": magnitude,
                    "selected_for_notch": (v, u) in REAL_NOTCH_CONFIG[filename]["centers"],
                }
            )
        plot_peaks(
            original,
            REAL_NOTCH_CONFIG[filename]["centers"],
            f"{filename}：人工选取的频谱峰（青圈为陷波中心）",
            results / f"notch_spectrum_{Path(filename).stem}.png",
        )

        # PSNR sweep uses an exact, known pre-injection reference. It measures
        # radius choice for this controlled sinusoidal corruption only.
        center = (max(9, int(round(height * 0.13))), max(11, int(round(width * 0.11))))
        if image_index % 2:
            center = (center[0], -center[1])
        controlled_noise = synthetic_modulated_noise(
            original.shape, center, SYNTHETIC_SIDE_BAND, amplitude=18.0
        )
        controlled_noisy = original + controlled_noise
        for d0 in NOTCH_SWEEP:
            transfer = gaussian_notch_reject(original.shape, [center], d0)
            restored = apply_frequency_filter(controlled_noisy, transfer)
            synthetic_rows.append(
                {
                    "image": filename,
                    "D0_bins": d0,
                    "carrier_v": center[0],
                    "carrier_u": center[1],
                    "sideband_bins": SYNTHETIC_SIDE_BAND,
                    "amplitude": 18.0,
                    "PSNR_dB": psnr(original, restored),
                    "MSE": float(np.mean((original - restored) ** 2)),
                    "reference": "provided input image before synthetic noise injection",
                }
            )

        config = REAL_NOTCH_CONFIG[filename]
        real_transfer = gaussian_notch_reject(original.shape, config["centers"], config["d0"])
        filtered = apply_frequency_filter(original, real_transfer)
        save_gray(results / "notch_filtered" / f"{Path(filename).stem}_notch.png", filtered)
        residual_spectrum = log_spectrum(filtered)
        figure, axes = plt.subplots(1, 3, figsize=(14, 4.5), constrained_layout=True)
        axes[0].imshow(original, cmap="gray", vmin=0, vmax=255)
        axes[0].set_title(f"输入：{filename}")
        axes[1].imshow(filtered, cmap="gray", vmin=0, vmax=255)
        axes[1].set_title(f"陷波结果：D0={config['d0']:g} bin")
        axes[2].imshow(residual_spectrum, cmap="magma")
        axes[2].set_title("滤波后 log(1+|F|)")
        for axis in axes:
            axis.axis("off")
        figure.savefig(results / f"notch_result_{Path(filename).stem}.png", dpi=180)
        plt.close(figure)

        actual_rows.append(
            {
                "image": filename,
                "height": height,
                "width": width,
                "selected_peak_pairs_v_u": json.dumps(config["centers"]),
                "D0_bins": config["d0"],
                "filter": "Gaussian notch reject",
                "assessment": "visual/spectral only; no clean reference supplied",
                "source_min": float(original.min()),
                "source_max": float(original.max()),
                "filtered_min_before_clip": float(filtered.min()),
                "filtered_max_before_clip": float(filtered.max()),
            }
        )
        notch_outputs.append((filename, original, filtered, real_transfer, config["d0"]))

    with (results / "notch_peak_candidates.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(peak_rows[0]))
        writer.writeheader()
        writer.writerows(peak_rows)
    with (results / "notch_psnr_sweep.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(synthetic_rows[0]))
        writer.writeheader()
        writer.writerows(synthetic_rows)
    with (results / "notch_real_image_parameters.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(actual_rows[0]))
        writer.writeheader()
        writer.writerows(actual_rows)

    best_rows = []
    for filename in challenge_files:
        subset = [row for row in synthetic_rows if row["image"] == filename]
        best = max(subset, key=lambda row: float(row["PSNR_dB"]))
        for row in subset:
            row["is_best"] = row is best
        best_rows.append(best)

    figure, axes = plt.subplots(2, 2, figsize=(11, 8), constrained_layout=True)
    for axis, filename in zip(axes.ravel(), challenge_files):
        subset = [row for row in synthetic_rows if row["image"] == filename]
        x = [float(row["D0_bins"]) for row in subset]
        y = [float(row["PSNR_dB"]) for row in subset]
        best = max(subset, key=lambda row: float(row["PSNR_dB"]))
        axis.plot(x, y, marker="o", color="#1c6e8c")
        axis.axvline(float(best["D0_bins"]), color="#c44e52", linestyle="--", linewidth=1)
        axis.set_title(f"{filename} · best D0={float(best['D0_bins']):g} bin")
        axis.set_xlabel("D0（频率 bin）")
        axis.set_ylabel("PSNR（dB）")
        axis.grid(alpha=0.25)
    figure.suptitle("已知调幅周期噪声上的陷波半径 PSNR 搜索", fontsize=14)
    figure.savefig(results / "notch_psnr_sweep.png", dpi=180)
    plt.close(figure)

    best_summary = [
        {
            "image": row["image"],
            "best_D0_bins": row["D0_bins"],
            "best_PSNR_dB": row["PSNR_dB"],
            "reference": row["reference"],
        }
        for row in best_rows
    ]
    (results / "notch_psnr_best.json").write_text(
        json.dumps(best_summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Display all four real-image outputs together, preserving each source's
    # aspect ratio and dimensions.
    figure, axes = plt.subplots(4, 3, figsize=(13, 13), constrained_layout=True)
    for row_index, (filename, original, filtered, transfer, d0) in enumerate(notch_outputs):
        axes[row_index, 0].imshow(original, cmap="gray", vmin=0, vmax=255)
        axes[row_index, 0].set_title(f"{filename} 原图")
        axes[row_index, 1].imshow(to_uint8(filtered), cmap="gray", vmin=0, vmax=255)
        axes[row_index, 1].set_title(f"Gaussian notch，D0={d0:g}")
        axes[row_index, 2].imshow(1.0 - transfer, cmap="magma", vmin=0, vmax=1)
        axes[row_index, 2].set_title("陷波衰减量 1−H")
        for axis in axes[row_index]:
            axis.axis("off")
    figure.suptitle("四张周期噪声图的实际陷波结果", fontsize=14)
    figure.savefig(results / "notch_all_four.png", dpi=180)
    plt.close(figure)

    return actual_rows, synthetic_rows


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "lowpass").mkdir(exist_ok=True)
    (RESULTS_DIR / "highpass").mkdir(exist_ok=True)
    (RESULTS_DIR / "notch_filtered").mkdir(exist_ok=True)

    fft_metrics = save_binary_spectrum(RESULTS_DIR)
    lowpass_rows, clean, noisy = run_gaussian_noise(RESULTS_DIR)
    highpass_rows = run_highpass(RESULTS_DIR, clean)
    notch_rows, notch_sweep_rows = run_notch_challenge(RESULTS_DIR)

    metadata = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pillow": Image.__version__ if hasattr(Image, "__version__") else __import__("PIL").__version__,
        "matplotlib": matplotlib.__version__,
        "random_seed": NOISE_SEED,
        "gaussian_sigma": NOISE_SIGMA,
        "cutoff_bins": list(CUTOFFS),
        "butterworth_order": 2,
        "binary_fft": fft_metrics,
        "gaussian_noisy_psnr_db": psnr(clean, noisy),
        "gaussian_lowpass_rows": len(lowpass_rows),
        "highpass_rows": len(highpass_rows),
        "notch_real_images": len(notch_rows),
        "notch_synthetic_psnr_rows": len(notch_sweep_rows),
        "real_periodic_images_psnr": "not computed: clean reference images were not supplied",
        "synthetic_notch_psnr_reference": "each supplied image before the controlled modulated sinusoidal noise was added",
        "hfe_parameters": {"family": "butterworth", "order": 2, "D0_bins": 24.0, "a": 0.6, "b": 1.4},
        "actual_notch_parameters": REAL_NOTCH_CONFIG,
    }
    (RESULTS_DIR / "run_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
