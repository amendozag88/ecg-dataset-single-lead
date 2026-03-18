# ECG Dataset Single-Lead Notebook Guide

This workspace contains two notebooks:

1. `S26_mitbih_to_csv-final.ipynb`
2. `preprocessing_for_rpeak.ipynb`

---

## 1) `S26_mitbih_to_csv-final.ipynb`

Purpose:
- Builds the MIT-BIH single-lead dataset artifacts used by downstream evaluation.
- Converts signals to **125 Hz** and exports precomputed signal CSVs.
- Builds annotation CSVs aligned to 125 Hz.
- Includes normalization/export flows and comparison utilities.

Key outputs (under `mit-bih/`):
- `signals/online_robust/*_mlii_125hz_online.csv`
- `signals/record_minmax/*_mlii_125hz_record.csv`
- `annotations/*_annotations_125hz.csv`
- manifest/failure CSV summaries for batch runs.

Classes used for beat labeling (MIT-BIH symbols):
- `N` → Normal beat
- `L` → Left bundle branch block beat
- `R` → Right bundle branch block beat
- `V` → Premature ventricular contraction
- `F` → Fusion of ventricular and normal beat
- `/` → Paced beat
- `A` → Atrial premature beat
- Any other beat symbol is kept and mapped as `OTHER` in the annotation CSV.

Rhythm annotations:
- Rhythm-related annotations are also present in the annotation CSVs.
- Rhythm marker rows (e.g., `+`) are retained for rhythm context.
- The rhythm text is stored in the `rhythm` field when provided by MIT-BIH annotations.


---

## 2) `preprocessing_for_rpeak.ipynb`

Purpose:
- Evaluates R-peak detection on precomputed 125 Hz signals.
- Supports embedded-style stream evaluation over 2-second windows.
- Computes matching/metrics against annotation-derived ground truth.
- Provides FP/FN visualization utilities.
- Supports detector benchmarking and all-record batch evaluation.

Current flow highlights:
- Loads one selected record (or all records) from local MIT-BIH IDs.
- Loads precomputed signal CSV from either:
  - `signals/online_robust`
  - `signals/record_minmax`  
- Loads GT peaks from annotations and excludes rhythm marker `+` from peak GT.
- Runs detector through `evaluate_rpeak_detector_stream(...)` using embedded behavior:
  - first window starts at sample `0`
  - next window starts at `(detected_r_peak - 20)`
  - first evaluated beat uses the first detected peak
  - subsequent windows evaluate only the second detected peak (carry-over first peak is ignored)
- Optional switch: `apply_causal_filter=True/False` before detector input.

Detectors currently available:
- `peak_detector(...)`: NeuroKit2-based detector.
- `pan_tompkins_peak_detector(...)`: canonical Pan-Tompkins-style detector.

Batch/all-record utilities:
- `evaluate_all_records(...)` iterates through all local records, summarizes per-record metrics in a DataFrame, and saves CSV output.
- Confusion matrix plotting is available through `plot_detection_confusion_matrix(...)`.
- The notebook includes a side-by-side benchmark cell for NeuroKit2 vs Pan-Tompkins.

Evaluation output files:
- `mit-bih/evaluation/all_records_results.csv` (latest run output path used by default all-record run)
- `mit-bih/evaluation/all_records_results_neurokit.csv` (detector-specific benchmark output)
- `mit-bih/evaluation/all_records_results_pan_tompkins.csv` (detector-specific benchmark output)

---

## 3) Detector Benchmarking

A benchmark comparing NeuroKit2 and Pan-Tompkins detectors across all records in MIT-BIH is included

### Benchmark Results (All Records Aggregate)

Key findings from the latest benchmark run:

| Metric | NeuroKit2 | Pan-Tompkins |
|--------|-----------|--------------|
| **Recall** | 0.419 | 0.949 | 
| **Precision** | 0.983 | 0.999 | 
| **F1 Score** | 0.588 | 0.973 |
| **True Positives** | 44,826 | 101,438 | 
| **False Positives** | 771 | 88 | 
| **False Negatives** | 61,651 | 5,303 |
| **Detection Error Rate** | 0.588 | 0.052 |
| **Ground Truth Beats** | 106,477 | 106,477 |

### Output Files

Detector-specific results are saved to:
- `mit-bih/evaluation/all_records_results_neurokit.csv` – NeuroKit2 per-record results
- `mit-bih/evaluation/all_records_results_pan_tompkins.csv` – Pan-Tompkins per-record results

Each CSV contains per-record and aggregate metrics, allowing detailed per-record comparison and delta analysis.


---
- Cindy> You can add your detector function and pass it as `detector_fn=peak_detector`
  - Your function should accept:
    - Input: one 2-second ECG window
    - Output: sample indices (relative to the window) where R-peaks are detected
```python
def peak_detector(window_2s, fs=125):
    # window_2s: 1D array (typically 250 samples at 125 Hz)
    # return: list of integer indices relative to window start
    return [ ... ]
```
---

## Suggested Execution Order
0. Download MIT-BIH and add your path to the path variable
1. Run all cells in `S26_mitbih_to_csv-final.ipynb` to ensure signals/annotations are generated.
2. Run setup + function-definition cells in `preprocessing_for_rpeak.ipynb` (Cells 1–7).
3. Choose a single-record evaluation or jump to all-records evaluation:
   - **Single-record**: Run Cell 9 and adjust `signal_mode_eval`, `apply_causal_filter_eval`, and `detector_fn_eval` as desired.
   - **All-records**: Run Cell 12 to evaluate all records with selected detector.
4. For FP/FN visualization, run Cell 10 (`plot_fp_fn_examples()`).

---
