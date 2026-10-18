# Task-Specific Temporal Integration in the Mouse Visual Cortex

**Maastricht University**
**Scientific Programming (Course MSB1015)**

Core Question: How long does it take for the performance of a movie-decoder that is trying to discern which segment of a natural movie is playing to saturate?<br>
This analysis yields a (visual) area's *integration window*. Its analysis runs on the [Allen Institute Visual Coding – Neuropixels](https://allensdk.readthedocs.io/en/latest/visual_coding_neuropixels.html)
dataset, and the prediction is that integration windows lengthen going up the cortical hierarchy.<br>
**Cortical Hierarchy**: VISp → VISl → VISrl → VISal → VISpm → VISam


A linear "pipeline" of Jupyter notebooks contains the project analyses. They can be found under [`notebooks/`](notebooks/):<br>
In short, raw sessions are quality-controlled and reduced to compact spike-count tensors, those tensors are then inspected and characterized, following that a decoder reads an integration window off each region, and a stimulus-only analysis provides a ceiling to compare the neural result against. All notebooks share one path configuration, which is given [`notebooks/paths.py`](notebooks/paths.py), so no file paths are hard-coded.

## Setup

Developed and tested on **Python 3.11** (3.11.9); Python 3.10+ should also work.
All package versions are pinned in [`requirements.txt`](requirements.txt), so after cloning the repo the environment used for the analysis can be reproduced exactly:

```bash
# from the repository root
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```


## Running

```bash
jupyter lab
```

---

## The `notebooks/`

The notebooks are meant to be run in the order given below, which is different from e.g., their alphabetical order on-disk. Notebook 2 has to be run before running notebooks 3-6, as it creates the `.npz` tensors that notebooks 3–6 read.

| # | Notebook | Role |
|---|----------|------|
| 1 | `Overview_Data.ipynb` | Dataset, stimulus and brain-area overview |
| 2 | `Data_Preparation_Selection.ipynb` | Quality control + streaming extraction → builds the dataset |
| 3 | `Data_Visualization.ipynb` | Unit counts per session/region and region-wise mean firing rate distribution across sessions|
| 4 | `Visualization_Preprocessing_Data_Structure.ipynb` | Cross-session structure: PCA / UMAP / PARAFAC |
| 5 | `Decoder_Analysis_Across_Regions.ipynb` | Neural Decoder Analysis→ Per-region integration windows (yields main results) |
| 6 | `Analysis_Stimulus_vs_Neural.ipynb` | Stimulus-only ceiling + neural-vs-stimulus comparison |

### 1. `Overview_Data.ipynb`: Dataset & Stimulus Overview

An orientation notebook that characterizes the dataset before any modeling. Pulls the Allen session table, breaking sessions down by type, summarizing the natural-movie stimulus (repeats, frames, ~33 ms frame duration), counts recorded units per brain area, and also renders a dorsal-view map of the six target visual areas on the Allen CCFv3 annotation volume. Reads from the Allen cache (and one session's stimulus table) but does not itself create extracted data.

### 2. `Data_Preparation_Selection.ipynb`: quality control & dataset creation

The only notebook that handles the raw Allen data. Runs a layered quality-control pass looking at session, probe, channel and unit levels. Combines Allen's published defaults with tightened custom thresholds. Plots the QC distributions and attrition so the thresholds can be justified.<br>
Custom thresholds include:
- ISI-violation limit dropped from 0.5 to 0.1
- Firing Rate Floor (dropping silent units)
- Signal-to-Noise Ratio Floor to discard noisy units

Its core is a streaming "extract-and-discard" driver that loops over the
`brain_observatory_1.1` (natural-movie) sessions one at a time, downloads the (~2 GB) NWB file and selects the passing units in the six visual-cortex areas. Following that, it builds a population spike-count tensor aligned to the `natural_movie_one` stimulus, writes a small compressed `.npz` with the extracted data, and deletes the large NWB file before moving on, thus limiting peak disk usage to a single session.

**Produces:**
- one `allen_ecephys/extracted/session_<id>.npz` per session, each holding `counts [repeat × bin × unit]` (spikes per 10 ms bin), `unit_ids`, `regions`, `bin_starts`, `bin_size`, `onsets`, `session_id`, and `movie`

### 3. `Data_Visualization.ipynb`: Unit-Counts & Firing Rate Distributions
Loads the extracted `.npz` tensors and confirms the extraction is sound: a dataset overview table (repeats, bins, units, duration per session).
**Produces:**
- **units-kept-per-region per-session stacked barplot**
- **per-unit mean firing-rate-by-region violin plot**: pooled across all sessions

### 4. `Visualization_Preprocessing_Data_Structure.ipynb`: Visualizes Cross-Session Structure

All data is pooled onto the axes the sessions share: **movie time** and **region label**.<br>
**Produces**:
- **sampling-coverage heatmap**: visualizes the units per region per session
- **per-region population PSTHs overlaid across sessions**
- **a unit-PSTH PCA + UMAP embedding**: one point per neuron, pooled across mice, colored by region and by session to separate tuning structure from batch effects
- **PARAFAC**: tensor decomposition with a shared temporal factor,  both per-session and a coupled version across sessions. Captures low-rank structure consistent across mice. <br>
Note: (The UMAP and PARAFAC cells require `umap-learn` and `tensorly`; they are skipped if those packages are not installed.)

### 5. `Decoder_Analysis_Across_Regions.ipynb`: integration windows (main analysis)

Yields the **MAIN RESULT**.<br><br>
Cuts the movie into `K` equal segments (the decoding classes) for every **(mouse, region)** pair. The features are then built by accumulating spike counts over a window `Δ` from each segment's onset. Segment identity is then decoded using a cross-validated classifier.<br>
Cross-validation uses **`GroupKFold` grouped by movie repeat** (5 folds), so the decoder is always tested on whole repeats it hasn't previously seen (trained on). Sweeping `Δ` gives an accuracy-vs-window curve, to which a saturating exponential `acc(Δ) = a∞ − (a∞ − a₀)·e^(−Δ/τ)` is fitted; the integration window can be read off this as **Δ95 = 3τ**, representing the window reaching ~95 % of its total accuracy gain.<br>

Results are aggregated per region across mice (mice are the replication unit, meaning units can never be pooled across animals), and a **Spearman correlation** between hierarchy rank and Δ95 tests the cortical hierarchy. The per-session decode is **parallelized**. The classifier is chosen specifying a single `CLF` switch (`lda`,`logreg`, `rf`, `svm-rbf`, `hgb`, `knn`, `mlp`), and figures as well as a results CSV are written to the folder `decoder_results/`.<br>

**Produces** (in `decoder_results/`, with the classifier name in each filename):
- `integration_windows_across_regions_<CLF>.png` + `.svg`: accuracy-vs-Δ curves per area (with mean Δ95 cutoffs) + Δ95-by-area with the Spearman hierarchy test
- `integration_windows_box_violin_<CLF>.png` + `.svg`: box + violin of Δ95 per area across mice
- `integration_windows_d_95_ms_<CLF>.csv`: per-session Δ95 (ms) for each area (the main results table)
- **per-region summary (printed)**: n mice, median τ, mean Δ95 ± SEM, and Spearman ρ(rank, Δ95) with p-value

### 6. `Analysis_Stimulus_vs_Neural.ipynb`: Stimulus-only ceiling + neural-vs-stimulus comparison

Builds a stimulus-only ideal-observer decoder: classifies segment identity from the movie frames themselves; first `round(Δ·fps)` frames per segment, matched to the neural Δ grid; represents the information ceiling the neural curve can be compared against;<br>
Also characterizes the stimulus directly via its
- **motion energy**: frame-to-frame change
- **temporal autocorrelation**: yields the **1/e decorrelation time**
- **PCA**: of the decoder-fed frames, including silhouette scores
<br> 
A final overlay figure compares the neural and stimulus accuracy-vs-Δ curves and their Δ95 values, showing where a region keeps integrating after the stimulus information has saturated. Neural curves are cached, and outputs are written to `stim_vs_neural/`.

**Produces** (in `stim_vs_neural/`):
- `stimulus_change_signals.png`: motion energy + temporal autocorrelation (with the 1/e decorrelation time)
- `stimulus_vs_neural_<CLF>.png`: neural-vs-stimulus overlay (raw acc(Δ) and normalized-gain panels, with Δ95 markers)
- `stimulus_vs_neural_d95_<CLF>.csv`: per-region Δ95_neural, Δ95_stim, their gap, and the stimulus decorrelation time
- `neural_curves_<CLF>.npz`: cached per-region neural accuracy curves (so re-runs are instant)
- the PCA-of-decoder-fed-frames scatter + silhouette snapshots (displayed only, not saved)

---

## Path configuration (`notebooks/paths.py`)

All notebooks get their paths from one module (no hard-coding):

```python
from paths import EXTRACTED_DIR, RESULTS_DIR, STIM_OUT_DIR, MANIFEST   # only the desired/required imports are specified in each notebook
```

`paths.py` anchors every path to its own location on disk (via `__file__`), so the project folder can be moved, renamed, or run from any working directory without editing a single notebook. Creates the output folders on import.
CONTAINS:
- `PROJECT_ROOT`
- `ALLEN_DIR`
- `EXTRACTED_DIR`
- `RESULTS_DIR`
- `STIM_OUT_DIR`
- `MANIFEST`<br>

---

## Repository layout

```
Scientific_Programming_Project/
├── notebooks/
│   ├── paths.py                                          # central path config
│   ├── Data_Preparation_Selection.ipynb                  # 2. QC + extraction  -> .npz
│   ├── Overview_Data.ipynb                               # 1. dataset / stimulus / area overview
│   ├── Data_Visualization.ipynb                          # 3. extracted-data sanity views
│   ├── Visualization_Preprocessing_Data_Structure.ipynb  # 4. cross-session structure (PCA/UMAP/PARAFAC)
│   ├── Decoder_Analysis_Across_Regions.ipynb             # 5. integration windows (main analysis)
│   └── Analysis_Stimulus_vs_Neural.ipynb                 # 6. stimulus ceiling + comparison
├── allen_ecephys/        # AllenSDK cache + extracted/ (.npz tensors) — data folder
├── decoder_results/      # decoder figures (.png/.svg) and CSVs — written by notebook 5
├── stim_vs_neural/        # figures, CSVs and cached neural curves — written by notebook 6
```

## Data source

The data comes from the Allen Institute **Visual Coding – Neuropixels** dataset, accessed through the AllenSDK `EcephysProjectCache` (`from_warehouse`). Notebook 2 downloads and caches sessions on demand so the large raw NWB files are discarded after extraction. Thus, only the compact `.npz` tensors need to be kept.

## Reproducibility

All stochastic steps use a fixed seed (`RANDOM_SEED = 0`) and the decoder's
cross-validation folds are deterministic (`GroupKFold`, no shuffling), so results are reproducible across serial and parallel runs. The decoder's classifier is selected with a single `CLF` switch, so the whole analysis can be re-run across models for comparison.
