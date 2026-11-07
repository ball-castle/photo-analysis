"""Interactive Gaussian notch editor for the four periodic-noise images."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

if matplotlib.get_backend().lower() in {"agg", "pdf", "svg", "ps", "template"}:
    try:
        matplotlib.use("TkAgg")
    except ImportError as exc:  # pragma: no cover - depends on workstation GUI
        raise RuntimeError("An interactive Matplotlib backend is required (TkAgg recommended)") from exc

matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button, Slider
from PIL import Image

from .frequency_filters import (
    apply_frequency_filter,
    dominant_peak_pairs,
    gaussian_notch_reject,
    to_uint8,
)


def load_gray(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("L"), dtype=np.float64)


def image_extent(shape: tuple[int, int]) -> tuple[float, float, float, float]:
    height, width = shape
    left = -(width // 2) - 0.5
    right = (width - 1 - width // 2) + 0.5
    bottom = -(height // 2) - 0.5
    top = (height - 1 - height // 2) + 0.5
    return left, right, bottom, top


def show_editor(image_path: Path, output_path: Path, initial_d0: float = 3.0) -> None:
    original = load_gray(image_path)
    height, width = original.shape
    spectrum = np.log1p(np.abs(np.fft.fftshift(np.fft.fft2(original - original.mean()))))
    suggestions = dominant_peak_pairs(original, count=10, min_radius=6.0)
    centers: list[tuple[int, int]] = []

    figure, axes = plt.subplots(1, 3, figsize=(15, 6))
    figure.subplots_adjust(bottom=0.23, wspace=0.18, left=0.05, right=0.97)
    axes[0].imshow(original, cmap="gray", vmin=0, vmax=255)
    axes[0].set_title(f"输入：{image_path.name}")
    axes[0].axis("off")

    extent = image_extent(original.shape)
    spectrum_artist = axes[1].imshow(
        spectrum, origin="lower", extent=extent, cmap="magma"
    )
    axes[1].set_title("点击频谱峰添加陷波中心；右键删除最近一组")
    axes[1].set_xlabel("水平频率 u（bin）")
    axes[1].set_ylabel("垂直频率 v（bin）")
    figure.colorbar(spectrum_artist, ax=axes[1], fraction=0.046, pad=0.03)

    initial_output = original.copy()
    result_artist = axes[2].imshow(initial_output, cmap="gray", vmin=0, vmax=255)
    axes[2].set_title("滤波结果")
    axes[2].axis("off")
    marks = []
    instructions = (
        "建议峰值（按强度）：\n"
        + ", ".join(f"({v},{u})" for v, u, _ in suggestions[:6])
        + "\n左键在频谱中选峰；单侧选择会自动加入共轭点。"
    )
    figure.text(0.34, 0.04, instructions, ha="center", va="bottom", fontsize=9)

    slider_axis = figure.add_axes([0.13, 0.15, 0.53, 0.035])
    radius_slider = Slider(slider_axis, "D0 (bin)", 0.5, 20.0, valinit=initial_d0, valstep=0.5)
    save_axis = figure.add_axes([0.73, 0.12, 0.1, 0.07])
    save_button = Button(save_axis, "保存结果")
    clear_axis = figure.add_axes([0.85, 0.12, 0.1, 0.07])
    clear_button = Button(clear_axis, "清空陷波")
    status = figure.text(0.72, 0.21, "陷波中心：无", ha="center", fontsize=9)

    def draw_centers() -> None:
        nonlocal marks
        for mark in marks:
            mark.remove()
        marks = []
        for v, u in centers:
            marks.append(
                axes[1].scatter(
                    [u, -u], [v, -v], marker="o", s=70,
                    facecolors="none", edgecolors="#41f2d5", linewidths=1.7,
                )
            )
        status.set_text("陷波中心：(v,u) " + (", ".join(map(str, centers)) if centers else "无"))

    def recompute(_value: object = None) -> None:
        d0 = float(radius_slider.val)
        if centers:
            transfer = gaussian_notch_reject(original.shape, centers, d0)
            filtered = apply_frequency_filter(original, transfer)
        else:
            filtered = original
        result_artist.set_data(to_uint8(filtered))
        axes[2].set_title(f"Gaussian notch · D0={d0:g} bin · {len(centers)} 组频率")
        figure.canvas.draw_idle()

    def on_click(event: object) -> None:
        if event.inaxes is not axes[1] or event.xdata is None or event.ydata is None:
            return
        u, v = int(round(event.xdata)), int(round(event.ydata))
        if np.hypot(v, u) < 5:
            status.set_text("中心低频区已忽略；请点选远离原点的亮峰。")
            figure.canvas.draw_idle()
            return
        canonical = min((v, u), (-v, -u))
        if event.button == 1:
            if not any(min(center, (-center[0], -center[1])) == canonical for center in centers):
                centers.append((v, u))
                draw_centers()
                recompute()
        elif event.button == 3 and centers:
            distances = [min(np.hypot(v - cv, u - cu), np.hypot(v + cv, u + cu)) for cv, cu in centers]
            closest = int(np.argmin(distances))
            if distances[closest] <= 8.0:
                centers.pop(closest)
                draw_centers()
                recompute()

    def save_result(_event: object) -> None:
        d0 = float(radius_slider.val)
        transfer = gaussian_notch_reject(original.shape, centers, d0)
        filtered = apply_frequency_filter(original, transfer)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(to_uint8(filtered), mode="L").save(output_path)
        parameter_path = output_path.with_suffix(".json")
        parameter_path.write_text(
            json.dumps(
                {
                    "input": str(image_path),
                    "output": str(output_path),
                    "image_shape": list(original.shape),
                    "centers_v_u": centers,
                    "D0_bins": d0,
                    "filter": "Gaussian notch reject",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        status.set_text(f"已保存：{output_path.name}")
        figure.canvas.draw_idle()

    def clear_centers(_event: object) -> None:
        centers.clear()
        draw_centers()
        recompute()

    radius_slider.on_changed(recompute)
    figure.canvas.mpl_connect("button_press_event", on_click)
    save_button.on_clicked(save_result)
    clear_button.on_clicked(clear_centers)
    plt.show()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, type=Path, help="input grayscale image")
    parser.add_argument("--output", type=Path, default=Path("notch_filtered.png"))
    parser.add_argument("--d0", type=float, default=3.0, help="initial notch radius in FFT bins")
    args = parser.parse_args()
    show_editor(args.image, args.output, initial_d0=args.d0)


if __name__ == "__main__":
    main()
