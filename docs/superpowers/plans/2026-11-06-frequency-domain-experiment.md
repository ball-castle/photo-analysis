# 频域图像增强实验实施计划

> **For agentic workers:** Follow the experiment tasks in order and keep each artifact reproducible from the submitted source package.

**Goal:** Complete the course experiment on Fourier spectra, ideal/Butterworth/Gaussian low-pass and high-pass filtering, high-frequency emphasis, and notch rejection on all four supplied periodic-noise images.

**Architecture:** Keep filter mathematics in a small NumPy module, the deterministic experiment and figure generation in one entry script, and the interactive notch editor in a separate Matplotlib program. Use MATLAB's installed `cameraman.tif` as the 256×256 natural reference for the Gaussian-noise and edge-enhancement sections. For PSNR radius sweeps, make paired controlled cases by adding known sinusoidal interference to each supplied image; do not present the corrupted supplied images as clean references.

**Tech Stack:** Python 3.9.7, NumPy, Pillow, Matplotlib; Microsoft Word COM for preserving the available course `.doc` template and exporting PDF.

**Spec:** `实验二    图像增强的频域方法.zip` (embedded experiment handout and four source images); the preceding workspace experiment in `output/` provides the existing template and delivery pattern.

## Global Constraints

- Use the task's four images `7.PNG`, `10.jpg`, `11.jpg`, and `16.jpg` for the notch-filter challenge.
- Demonstrate a centered 256×256 binary rectangle of 16×4 pixels, `fft2`, manually computed 2-D DFT, log magnitude, phase, `fftshift`, `ifftshift`, and inverse reconstruction.
- Run all three low-pass and all three high-pass filters at four cutoff radii.
- Use fixed random seed `20261106` for Gaussian-noise experiments.
- Make every PSNR reference explicit. Do not claim PSNR against clean ground truth for the four provided periodic-noise files because no clean pairs are supplied.
- Include source code and actual generated results in the course report and reproducible package; do not add unrequested test suites.
- Preserve the available Wuhan University of Technology Math Department course report template and leave grade/signature fields blank.

## Review Focus

- FFT centering and image-axis convention: manually computed DFT must agree numerically with NumPy `fft2`; inverse reconstruction must restore the input.
- Filter symmetry and DC behavior: transfer functions must be real, nonnegative, conjugate symmetric, and high-pass response must be zero at DC.
- PSNR scope: synthetic known-noise pairs use the pre-noise source as reference; original challenge images receive no unsupported PSNR claim.
- Original image frequency coordinates: keep each image's original dimensions for notch detection and report per-image coordinates/radius in frequency-bin units.
- Visual scaling: distinguish raw high-pass response from display normalization and do not let display stretching change saved numeric outputs.

---

### Task 1: Fourier and frequency-filter primitives

**Files:**
- Create: `频域滤波实验/src/frequency_filters.py`
- Create: `频域滤波实验/data/source/cameraman.tif`
- Create: `频域滤波实验/data/source/README.md`

**Interfaces:**
- `manual_dft2(image: np.ndarray) -> np.ndarray`
- `radial_filter(shape: tuple[int, int], d0: float, kind: str, order: int = 2) -> np.ndarray`
- `gaussian_notch_reject(shape: tuple[int, int], centers: list[tuple[int, int]], d0: float) -> np.ndarray`
- `apply_frequency_filter(image: np.ndarray, transfer: np.ndarray) -> np.ndarray`

- [ ] Implement centered distance grids, ideal/Butterworth/Gaussian low-pass and high-pass masks, high-frequency emphasis, Gaussian notch reject, and inverse-FFT reconstruction.
- [ ] Copy `cameraman.tif` from the local MATLAB R2023b `imdata` directory and record that provenance in `data/source/README.md`.
- [ ] Manually compare the direct DFT result with `numpy.fft.fft2` on the required binary image and record maximum absolute error in the experiment metadata.

### Task 2: Deterministic experiment and results

**Files:**
- Create: `频域滤波实验/run_experiment.py`
- Create: `频域滤波实验/results/`
- Create: `频域滤波实验/requirements.txt`

**Interfaces:**
- Consume the filter functions from Task 1.
- Produce figures, CSV/JSON metrics, processed images, and run metadata under `results/`.

- [ ] Generate the binary rectangle spectrum and shifted/unshifted demonstrations.
- [ ] Add Gaussian noise to `cameraman.tif` using seed `20261106`; run three low-pass masks at `D0=[8,16,32,64]` and save PSNR against the uncorrupted source.
- [ ] Run three high-pass filters at the same four cutoffs on the natural scene and save a high-frequency-emphasis result with documented `a`, `b`, `D0`, and Butterworth order.
- [ ] For each supplied periodic-noise image, detect/record conjugate spectral peaks, create a known-frequency sinusoidal corruption with its original input as the exact pre-injection reference, sweep notch radii, and save PSNR results separately from the real-image visual results.
- [ ] Apply selected notch centers/radii to the four supplied images; save filtered images and before/after spectra while retaining each original image size.
- [ ] Record image dimensions, grayscale conversion, parameters, seed, dependency versions, and all metric references in `results/run_metadata.json`.

### Task 3: Interactive notch editor and reproducible package

**Files:**
- Create: `频域滤波实验/src/notch_editor.py`
- Create: `频域滤波实验/README.md`
- Create: `频域滤波实验/提交/`

- [ ] Add a Matplotlib GUI that loads an image, displays its centered log spectrum, lets the user click frequency peaks (adding conjugate centers), adjusts notch radius, and saves the filtered image.
- [ ] Document GUI and batch commands, frequency-coordinate convention, dependencies, and the PSNR reference boundary.
- [ ] Package source, input images, result tables/figures, run metadata, and the final report source/output into the submission archive.

### Task 4: Course report and audits

**Files:**
- Create: `频域滤波实验/build_report.ps1`
- Create: `频域滤波实验/实验二_图像增强的频域方法_实验报告.doc`
- Create: `频域滤波实验/实验二_图像增强的频域方法_实验报告.pdf`
- Create: `频域滤波实验/对抗性审计记录.md`

- [ ] Fill a copy of the existing course template; preserve its original table geometry and leave grade and signature fields empty.
- [ ] Write the report around measured filter behavior, cutoff selection, ideal-filter ringing, and the PSNR-reference distinction; include code and actual figures.
- [ ] Run independent technical, AI-style, and defensive-language audits; apply evidence-based fixes and save the findings.
- [ ] Export the Word report to PDF and visually inspect rendered pages before final packaging.
