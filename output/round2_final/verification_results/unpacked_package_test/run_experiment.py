"""Run the reproducible Digital Image Processing Experiment 1 pipeline.

Run from any directory with:
    python output/run_experiment.py --seed 20261008

All enhancement and filtering kernels are implemented in dip_lab with NumPy.
scikit-image is used only for PSNR/SSIM metrics.
"""

import argparse
import csv
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import PIL
import skimage

from dip_lab.advanced import bilateral_filter, guided_filter, non_local_means
from dip_lab.histogram import equalize_histogram, gray_histogram, make_bimodal_target, match_histogram
from dip_lab.image_io import load_gray_square
from dip_lab.metrics import compare
from dip_lab.noise import add_gaussian_noise, add_mixed_noise, add_salt_pepper_noise
from dip_lab.spatial import (
    edge_sharpen,
    gaussian_filter,
    laplacian_response,
    laplacian_variants,
    mean_filter,
    median_filter,
    prewitt_response,
    roberts_response,
    sobel_response,
)


ROOT = Path(__file__).resolve().parent
SOURCE_DIR = ROOT / "data" / "source"
PROCESSED_DIR = ROOT / "data" / "processed"
RESULTS_DIR = ROOT / "results"
SEED_DEFAULT = 20261008

try:
    plt.rcParams["font.family"] = "Microsoft YaHei"
except Exception:
    plt.rcParams["font.sans-serif"] = ["SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def _u8(image):
    return np.clip(np.rint(np.asarray(image, dtype=np.float64)), 0, 255).astype(np.uint8)


def _save_image(path, image):
    from PIL import Image

    Image.fromarray(_u8(image), mode="L").save(path)


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _histogram_summary(image):
    values = np.asarray(image, dtype=np.uint8)
    counts = gray_histogram(values).astype(np.float64)
    probability = counts[counts > 0] / values.size
    entropy = float(-(probability * np.log2(probability)).sum())
    return {
        "mean_gray": float(values.mean()),
        "std_gray": float(values.std()),
        "p01_gray": float(np.percentile(values, 1)),
        "p99_gray": float(np.percentile(values, 99)),
        "entropy_bits": entropy,
        "fraction_at_0": float(np.mean(values == 0)),
        "fraction_at_255": float(np.mean(values == 255)),
    }


def _save_rows(path, rows, fieldnames=None):
    if not rows:
        return
    fieldnames = fieldnames or list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _title(ax, text):
    ax.set_title(text, fontsize=10)
    ax.set_xticks([])
    ax.set_yticks([])


def _show_gray(ax, image, title, vmin=0, vmax=255):
    ax.imshow(image, cmap="gray", vmin=vmin, vmax=vmax)
    _title(ax, title)


def _histogram_experiment(dark_face):
    equalized = equalize_histogram(dark_face)
    target = make_bimodal_target(peak1=65, peak2=185, sigma=13, weight1=0.52)
    specified = match_histogram(dark_face, target)
    _save_image(PROCESSED_DIR / "dark_face_512.png", dark_face)
    _save_image(RESULTS_DIR / "histogram_equalized.png", equalized)
    _save_image(RESULTS_DIR / "histogram_specified.png", specified)

    figure, axes = plt.subplots(2, 3, figsize=(13, 7.2), constrained_layout=True)
    for axis, image, title in zip(
        axes[0],
        (dark_face, equalized, specified),
        ("暗调原图（512×512）", "手写直方图均衡化", "手写双峰直方图规定化"),
    ):
        _show_gray(axis, image, title)
    levels = np.arange(256)
    for axis, image, title in zip(
        axes[1],
        (dark_face, equalized, specified),
        ("原图灰度直方图", "均衡化后直方图", "规定化结果与目标分布"),
    ):
        counts = gray_histogram(image).astype(np.float64)
        axis.plot(levels, counts / counts.sum(), color="#245b8f", linewidth=1.2, label="图像")
        if title.startswith("规定化"):
            axis.plot(levels, target, color="#c23b22", linestyle="--", linewidth=1.2, label="目标")
            axis.legend(fontsize=8)
        axis.set_title(title, fontsize=10)
        axis.set_xlim(0, 255)
        axis.grid(alpha=0.18)
        axis.set_xlabel("灰度级")
        axis.set_ylabel("相对频率")
    figure.savefig(RESULTS_DIR / "histogram_comparison.png", dpi=170)
    plt.close(figure)

    rows = []
    for label, image in (("暗调原图", dark_face), ("均衡化", equalized), ("规定化", specified)):
        rows.append({"image": label, **_histogram_summary(image)})
    _save_rows(RESULTS_DIR / "histogram_statistics.csv", rows)
    return equalized, specified, target, rows


def _matlab_comparison_if_present(dark_face, python_equalized):
    matlab_path = RESULTS_DIR / "matlab_histeq.png"
    if not matlab_path.is_file():
        return None
    from PIL import Image

    with Image.open(matlab_path) as opened:
        matlab_equalized = np.asarray(opened.convert("L"), dtype=np.uint8)
    if matlab_equalized.shape != dark_face.shape:
        raise ValueError("MATLAB histeq output does not match the 512x512 input")
    difference = np.abs(matlab_equalized.astype(np.int16) - python_equalized.astype(np.int16))
    comparison = {
        "function": "histeq (MATLAB R2023b Image Processing Toolbox)",
        "available": True,
        "mean_absolute_difference_vs_python": float(difference.mean()),
        "maximum_absolute_difference_vs_python": int(difference.max()),
    }
    figure, axes = plt.subplots(2, 3, figsize=(13, 7.2), constrained_layout=True)
    for axis, image, title in zip(
        axes[0],
        (dark_face, python_equalized, matlab_equalized),
        ("原图", "手写 Python 均衡化", "MATLAB histeq"),
    ):
        _show_gray(axis, image, title)
    for axis, image, title in zip(
        axes[1],
        (dark_face, python_equalized, matlab_equalized),
        ("原图直方图", "Python 结果直方图", "MATLAB 结果直方图"),
    ):
        counts = gray_histogram(image).astype(np.float64)
        axis.plot(np.arange(256), counts / counts.sum(), color="#245b8f", linewidth=1.2)
        axis.set_title(title + "\n" + ("" if image is dark_face else "MAE 差异=" + format(comparison["mean_absolute_difference_vs_python"], ".2f")), fontsize=9)
        axis.set_xlim(0, 255)
        axis.grid(alpha=0.18)
        axis.set_xlabel("灰度级")
        axis.set_ylabel("相对频率")
    figure.savefig(RESULTS_DIR / "matlab_histeq_comparison.png", dpi=170)
    plt.close(figure)
    (RESULTS_DIR / "matlab_histeq_comparison.json").write_text(
        json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return comparison


def _edge_experiment(face):
    edge_jobs = {
        "Roberts": roberts_response,
        "Sobel": sobel_response,
        "Prewitt": prewitt_response,
        "Laplacian": laplacian_response,
    }
    responses, edge_rows = {}, []
    for name, operation in edge_jobs.items():
        response, elapsed = _run_timed(operation, face)
        responses[name] = response
        absolute = np.abs(response)
        edge_rows.append(
            {
                "operator": name,
                "runtime_seconds": elapsed,
                "response_min": float(response.min()),
                "response_max": float(response.max()),
                "absolute_p99_8": float(np.percentile(absolute, 99.8)),
                "absolute_mean": float(absolute.mean()),
            }
        )
    _save_rows(RESULTS_DIR / "edge_operator_statistics.csv", edge_rows)
    # One robust upper bound is shared by every display; outliers do not
    # make the other operators appear almost black.
    response_max = max(float(np.percentile(np.abs(value), 99.8)) for value in responses.values())
    response_display = {
        name: np.clip(np.abs(value) * (255.0 / max(response_max, 1e-12)), 0, 255)
        for name, value in responses.items()
    }
    sharpened = {
        name: edge_sharpen(face, name.lower(), amount=0.2)
        for name in ("Roberts", "Sobel", "Prewitt")
    }
    lap = laplacian_variants(face)
    _save_image(RESULTS_DIR / "laplacian_absolute.png", lap["absolute"])
    _save_image(RESULTS_DIR / "laplacian_stretched.png", lap["stretched"])
    _save_image(RESULTS_DIR / "laplacian_overlay.png", lap["overlay"])

    figure, axes = plt.subplots(2, 3, figsize=(12, 7.5), constrained_layout=True)
    _show_gray(axes[0, 0], face, "原始人脸")
    for axis, key in zip(axes[0, 1:], ("Roberts", "Sobel")):
        _show_gray(axis, response_display[key], key + " 边缘响应", 0, 255)
    for axis, key in zip(axes[1, :2], ("Prewitt", "Laplacian")):
        _show_gray(axis, response_display[key], key + " 响应（共同比例）", 0, 255)
    _show_gray(axes[1, 2], lap["overlay"], "Laplacian 原图叠加锐化")
    figure.savefig(RESULTS_DIR / "edge_responses.png", dpi=170)
    plt.close(figure)

    figure, axes = plt.subplots(2, 3, figsize=(12, 7.5), constrained_layout=True)
    _show_gray(axes[0, 0], face, "原图")
    for axis, name in zip(axes[0, 1:], ("Roberts", "Sobel")):
        _show_gray(axis, sharpened[name], name + " 边缘掩膜锐化")
    _show_gray(axes[1, 0], sharpened["Prewitt"], "Prewitt 边缘掩膜锐化")
    _show_gray(axes[1, 1], lap["overlay"], "Laplacian: 原图 + 有符号响应")
    _show_gray(axes[1, 2], lap["stretched"], "Laplacian: 响应线性拉伸")
    figure.savefig(RESULTS_DIR / "edge_sharpening.png", dpi=170)
    plt.close(figure)

    figure, axes = plt.subplots(1, 4, figsize=(14, 4), constrained_layout=True)
    _show_gray(axes[0], face, "原图")
    _show_gray(axes[1], lap["absolute"], "|Laplacian| 绝对值")
    _show_gray(axes[2], lap["stretched"], "有符号响应线性拉伸")
    _show_gray(axes[3], lap["overlay"], "原图叠加并截断")
    figure.savefig(RESULTS_DIR / "laplacian_negative_handling.png", dpi=170)
    plt.close(figure)
    return responses, sharpened, lap


def _noise_experiment(face, seed):
    gaussian = add_gaussian_noise(face, sigma=18.0, seed=seed)
    impulse = add_salt_pepper_noise(face, density=0.04, seed=seed + 1)
    mixed = add_mixed_noise(face, gaussian_sigma=12.0, salt_pepper_density=0.02, seed=seed + 2)
    for name, image in (("noise_gaussian.png", gaussian), ("noise_salt_pepper.png", impulse), ("noise_mixed.png", mixed)):
        _save_image(RESULTS_DIR / name, image)

    figure, axes = plt.subplots(1, 4, figsize=(14, 4), constrained_layout=True)
    for axis, image, label in zip(
        axes,
        (face, gaussian, impulse, mixed),
        ("無噪聲參考圖", "高斯噪聲 σ=18", "椒鹽噪聲密度=0.04", "混合噪聲 σ=12、密度=0.02"),
    ):
        _show_gray(axis, image, label)
    figure.savefig(RESULTS_DIR / "noise_models.png", dpi=170)
    plt.close(figure)
    return {"gaussian": gaussian, "salt_pepper": impulse, "mixed": mixed}


def _run_timed(function, *args, **kwargs):
    start = time.perf_counter()
    result = function(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return result, elapsed


def _classical_sensitivity(clean, noisy):
    jobs = [
        ("均值", "窗口3×3", lambda: mean_filter(noisy, 3)),
        ("均值", "窗口5×5", lambda: mean_filter(noisy, 5)),
        ("均值", "窗口7×7", lambda: mean_filter(noisy, 7)),
        (
            "加权均值",
            "窗口3×3 权重1/2/1",
            lambda: mean_filter(noisy, 3, np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]], dtype=np.float64)),
        ),
        ("中值", "窗口3×3", lambda: median_filter(noisy, 3)),
        ("中值", "窗口5×5", lambda: median_filter(noisy, 5)),
        ("中值", "窗口7×7", lambda: median_filter(noisy, 7)),
        ("高斯", "窗口3 σ=0.8", lambda: gaussian_filter(noisy, 3, 0.8)),
        ("高斯", "窗口5 σ=1.2", lambda: gaussian_filter(noisy, 5, 1.2)),
        ("高斯", "窗口7 σ=1.6", lambda: gaussian_filter(noisy, 7, 1.6)),
    ]
    rows, outputs = [], {}
    for method, parameters, operation in jobs:
        output, elapsed = _run_timed(operation)
        key = method + "_" + parameters
        outputs[key] = output
        rows.append(
            {
                "method": method,
                "parameters": parameters,
                "runtime_seconds": elapsed,
                **compare(clean, output),
            }
        )
    _save_rows(RESULTS_DIR / "classical_sensitivity.csv", rows)
    figure, axes = plt.subplots(2, 5, figsize=(16, 7), constrained_layout=True)
    for axis, row in zip(axes.ravel(), rows):
        key = row["method"] + "_" + row["parameters"]
        _show_gray(axis, outputs[key], row["method"] + " " + row["parameters"])
    figure.savefig(RESULTS_DIR / "classical_sensitivity.png", dpi=170)
    plt.close(figure)
    return rows, outputs


def _six_filter_comparison(clean, noisy):
    jobs = [
        ("均值", "5×5", lambda: mean_filter(noisy, 5), "O(N) integral box filter"),
        ("中值", "5×5", lambda: median_filter(noisy, 5), "O(N k²) neighborhood selection"),
        ("高斯", "7×7, σ=1.6", lambda: gaussian_filter(noisy, 7, 1.6), "O(N k) separable"),
        (
            "双边",
            "r=3, σs=2, σr=40",
            lambda: bilateral_filter(noisy, radius=3, sigma_space=2.0, sigma_range=40.0),
            "O(N k²)",
        ),
        (
            "引导",
            "r=3, ε=1600",
            lambda: guided_filter(noisy, noisy, radius=3, epsilon=1600.0),
            "O(N) integral box filters",
        ),
        (
            "NLM",
            "patch=5×5, search=7×7, h=30",
            lambda: non_local_means(noisy, patch_radius=2, search_radius=3, h=30.0, noise_sigma=12.0),
            "O(N s²) search displacements",
        ),
    ]
    rows, outputs = [], {}
    for method, parameters, operation, complexity in jobs:
        output, elapsed = _run_timed(operation)
        outputs[method] = output
        rows.append(
            {
                "method": method,
                "parameters": parameters,
                "runtime_seconds": elapsed,
                **compare(clean, output),
                "complexity": complexity,
                "metric_reference": "同一输入图加噪前的512×512人像",
            }
        )
        _save_image(RESULTS_DIR / ("filter_" + method + ".png"), output)
    _save_rows(RESULTS_DIR / "six_filter_comparison.csv", rows)

    figure, axes = plt.subplots(2, 4, figsize=(15, 8), constrained_layout=True)
    panels = [("参考原图", clean), ("混合噪声输入", noisy)] + [(row["method"], outputs[row["method"]]) for row in rows]
    for axis, (label, image) in zip(axes.ravel(), panels):
        _show_gray(axis, image, label)
    axes.ravel()[-1].axis("off")
    figure.savefig(RESULTS_DIR / "six_filter_visual_comparison.png", dpi=170)
    plt.close(figure)

    # Fixed, corresponding 128x128 face-detail region for close inspection.
    top, left, side = 160, 160, 128
    detail_panels = [("原图", clean), ("混合噪声", noisy)] + [(row["method"], outputs[row["method"]]) for row in rows]
    figure, axes = plt.subplots(2, 4, figsize=(14, 8), constrained_layout=True)
    for axis, (label, image) in zip(axes.ravel(), detail_panels):
        _show_gray(axis, image[top : top + side, left : left + side], label + "（局部放大）")
    axes.ravel()[-1].axis("off")
    figure.savefig(RESULTS_DIR / "face_detail_comparison.png", dpi=180)
    plt.close(figure)
    return rows, outputs


def _advanced_sensitivity(clean, noisy):
    jobs = [
        ("双边", "σr=15", lambda: bilateral_filter(noisy, 3, 2.0, 15.0)),
        ("双边", "σr=25", lambda: bilateral_filter(noisy, 3, 2.0, 25.0)),
        ("双边", "σr=40", lambda: bilateral_filter(noisy, 3, 2.0, 40.0)),
        ("引导", "ε=256", lambda: guided_filter(noisy, noisy, 3, 256.0)),
        ("引导", "ε=900", lambda: guided_filter(noisy, noisy, 3, 900.0)),
        ("引导", "ε=1600", lambda: guided_filter(noisy, noisy, 3, 1600.0)),
        ("NLM", "h=14, search=7×7", lambda: non_local_means(noisy, 2, 3, 14.0, 12.0)),
        ("NLM", "h=22, search=7×7", lambda: non_local_means(noisy, 2, 3, 22.0, 12.0)),
        ("NLM", "h=30, search=7×7", lambda: non_local_means(noisy, 2, 3, 30.0, 12.0)),
        ("NLM", "h=22, search=5×5", lambda: non_local_means(noisy, 2, 2, 22.0, 12.0)),
        ("NLM", "h=22, search=11×11", lambda: non_local_means(noisy, 2, 5, 22.0, 12.0)),
    ]
    rows = []
    for method, parameters, operation in jobs:
        output, elapsed = _run_timed(operation)
        rows.append(
            {
                "method": method,
                "parameters": parameters,
                "runtime_seconds": elapsed,
                **compare(clean, output),
            }
        )
    _save_rows(RESULTS_DIR / "advanced_sensitivity.csv", rows)

    figure, axes = plt.subplots(1, 3, figsize=(14, 4.5), constrained_layout=True)
    for axis, method in zip(axes, ("双边", "引导", "NLM")):
        subset = [row for row in rows if row["method"] == method]
        labels = [row["parameters"] for row in subset]
        axis.plot(labels, [row["psnr_db"] for row in subset], marker="o", label="PSNR / dB")
        axis.set_ylabel("PSNR / dB")
        axis.grid(alpha=0.25)
        axis.tick_params(axis="x", labelrotation=25)
        axis.set_title(method + " 参数敏感性")
        second = axis.twinx()
        second.plot(labels, [row["ssim"] for row in subset], marker="s", color="#c23b22", label="SSIM")
        second.set_ylabel("SSIM")
    figure.savefig(RESULTS_DIR / "advanced_sensitivity.png", dpi=170)
    plt.close(figure)
    return rows


def _facial_smoothing(face):
    jobs = [
        ("均值", lambda: mean_filter(face, 5)),
        ("中值", lambda: median_filter(face, 5)),
        ("高斯", lambda: gaussian_filter(face, 7, 1.6)),
        ("双边", lambda: bilateral_filter(face, 3, 2.0, 40.0)),
        ("引导", lambda: guided_filter(face, face, 3, 1600.0)),
        ("NLM", lambda: non_local_means(face, 2, 3, 30.0, 0.0)),
    ]
    rows = []
    figure, axes = plt.subplots(2, 4, figsize=(15, 8), constrained_layout=True)
    _show_gray(axes.ravel()[0], face, "带雀斑真实人像原图")
    for axis, (method, operation) in zip(axes.ravel()[1:], jobs):
        output, elapsed = _run_timed(operation)
        _save_image(RESULTS_DIR / ("face_smooth_" + method + ".png"), output)
        _show_gray(axis, output, method + " 平滑")
        rows.append(
            {
                "method": method,
                "runtime_seconds": elapsed,
                "psnr_db": "N/A",
                "ssim": "N/A",
                "reason": "原图本身含有雀斑/皱纹，没有无瑕疵真值",
            }
        )
    axes.ravel()[-1].axis("off")
    figure.savefig(RESULTS_DIR / "facial_smoothing_no_reference.png", dpi=170)
    plt.close(figure)
    _save_rows(RESULTS_DIR / "facial_smoothing_no_reference.csv", rows)
    return rows


def run(seed=SEED_DEFAULT):
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    dark_path = SOURCE_DIR / "older_woman_wrinkles.jpg"
    freckle_path = SOURCE_DIR / "freckled_woman.jpg"
    if not dark_path.is_file() or not freckle_path.is_file():
        raise FileNotFoundError("Place both credited source photos in data/source before running")

    dark_face = load_gray_square(dark_path, 512)
    face = load_gray_square(freckle_path, 512)
    _save_image(PROCESSED_DIR / "freckled_face_512.png", face)
    print("[1/6] Histogram equalization and specification...", flush=True)
    equalized, _, _, _ = _histogram_experiment(dark_face)
    matlab_comparison = _matlab_comparison_if_present(dark_face, equalized)
    print("[2/6] Roberts, Sobel, Prewitt, and Laplacian...", flush=True)
    _edge_experiment(face)
    print("[3/6] Reproducible noise generation...", flush=True)
    noise = _noise_experiment(face, seed)
    print("[4/6] Mean, median, and Gaussian parameter study...", flush=True)
    classical_rows, _ = _classical_sensitivity(face, noise["mixed"])
    print("[5/6] Six-filter metrics and advanced-filter sensitivity...", flush=True)
    six_rows, _ = _six_filter_comparison(face, noise["mixed"])
    advanced_rows = _advanced_sensitivity(face, noise["mixed"])
    print("[6/6] Face-detail smoothing without a blemish-free reference...", flush=True)
    beauty_rows = _facial_smoothing(face)

    metadata = {
        "experiment": "Experiment 1: Spatial-domain image enhancement",
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pillow": PIL.__version__,
        "scikit_image_metrics": skimage.__version__,
        "matplotlib": matplotlib.__version__,
        "seed": int(seed),
        "image_size": [512, 512],
        "input_images": {
            "dark_wrinkled_face": {
                "path": "data/source/older_woman_wrinkles.jpg",
                "sha256": _sha256(dark_path),
                "source_dimensions": [3000, 3000],
                "prepared_summary": _histogram_summary(dark_face),
            },
            "freckled_face": {
                "path": "data/source/freckled_woman.jpg",
                "sha256": _sha256(freckle_path),
                "source_dimensions": [3000, 2000],
                "preparation": "center-cropped to square then resized with Lanczos; aspect ratio preserved",
                "prepared_summary": _histogram_summary(face),
            },
        },
        "matlab_comparison": matlab_comparison or "not available; no MATLAB output file was supplied",
        "six_filter_comparison_count": len(six_rows),
        "classical_sensitivity_count": len(classical_rows),
        "advanced_sensitivity_count": len(advanced_rows),
        "facial_smoothing_no_reference_count": len(beauty_rows),
    }
    (RESULTS_DIR / "run_metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Experiment run completed.")
    print("Image size: 512x512 grayscale; seed:", seed)
    print("Six-filter metrics:")
    for row in six_rows:
        print(
            "{method}: {runtime_seconds:.4f}s, PSNR={psnr_db:.3f} dB, SSIM={ssim:.5f}".format(**row)
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=SEED_DEFAULT)
    args = parser.parse_args()
    run(seed=args.seed)


if __name__ == "__main__":
    main()
