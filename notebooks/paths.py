"""Central path configuration file for the Scientific Programming project.

To specify the desired paths, the following imports can be specified in any notebook:
    from paths import PROJECT_ROOT, ALLEN_DIR, EXTRACTED_DIR, RESULTS_DIR, MANIFEST

Paths are anchored to this paths-py file's location (via __file__).
Ergo nothing is there is free choice of machine or working directory:
The project folder can me moved/renamed, ran from a different cwd and
it will be automatically handled.
"""

from pathlib import Path

# The project root is two directory levels up from <project>/notebooks/
PROJECT_ROOT     = Path(__file__).resolve().parent.parent

ALLEN_DIR        = PROJECT_ROOT / "allen_ecephys"       # AllenSDK cache + templates  (a.k.a. DATA_ROOT / DATA_DIR)
EXTRACTED_DIR    = ALLEN_DIR / "extracted"              # per-session .npz tensors
RESULTS_DIR      = PROJECT_ROOT / "decoder_results"     # decoder figures + CSVs
STIM_OUT_DIR     = PROJECT_ROOT / "stim_vs_neural"       # Analysis_Stimulus_vs_Neural figures / CSVs / neural-curve cache
MANIFEST         = ALLEN_DIR / "manifest.json"          # EcephysProjectCache manifest

# creates output directories if they are missing (doesn't execute if they already exist)
RESULTS_DIR.mkdir(exist_ok=True)
STIM_OUT_DIR.mkdir(exist_ok=True)
