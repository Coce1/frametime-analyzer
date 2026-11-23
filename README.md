# frametime-analyzer

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Coce1/frametime-analyzer/blob/main/notebooks/frametime_colab.ipynb)

A small Python tool that analyses **frame-time captures** (CSV files with one frame time per row) from a game or a 3D demo: average FPS, percentiles, 1% / 0.1% lows, stutter detection, charts, and a before/after comparison that flags regressions.

It is a personal learning project about GPU / graphics performance measurement, built with the help of an AI assistant (Claude), then reviewed and tested. It is a simple statistics tool, not a profiler: it tells you *that* frame pacing got worse, not *why*.

> **About the data in this repository.** All numbers produced by the tests and by the demo cell come from **synthetic data** (random numbers with known properties). They are not measurements of any real game or GPU. Real results, if any, go in the section [Results on real captures](#results-on-real-captures).

## Two ways to run it

### Option 1: Google Colab (nothing to install)

1. Click the **Open in Colab** badge above (or open `notebooks/frametime_colab.ipynb` in Colab with *File > Upload notebook*).
2. Run cell 1, then cell 2 (one capture) and/or cell 3 (two captures), or cell 4 for a demo that needs no file.

Nothing is saved to your Google Drive: uploaded files stay in memory for the session.

### Option 2: on your own machine (Python 3.9+)

```bash
git clone https://github.com/Coce1/frametime-analyzer.git
cd frametime-analyzer

# create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows (PowerShell): .venv\Scripts\Activate.ps1

pip install -r requirements.txt

# try it
python frametime_lite.py capture.csv
python frametime_lite.py capture.csv --column MyColumn
python frametime_lite.py before.csv --compare after.csv --threshold 5
pytest
```

Output: numbers in the terminal and a chart saved as `frametimes.png` (use `--plot name.png` to change it). Exit code: `0` OK, `1` regression detected, `2` input error.

## Input format

- A CSV file **with a header row**, one frame per row, with one column holding the **frame time in milliseconds**.
- The column is auto-detected among `MsBetweenPresents`, `FrameTime`, `frametime`. This list is my guess of common names and is **not verified against every capture tool or version**. If your file uses another name, pass `--column` (command line) or set `COLUMN` (notebook). If nothing matches, the error message lists the columns found.
- Rows that are non-numeric or `<= 0` are skipped silently. Very large values are kept (they are real stutters).
- Captures can be made with tools such as PresentMon or NVIDIA FrameView. Check which column of your own file holds the time between frames, and its unit.

## Definitions

- **Average FPS** = number of frames / total duration (not the mean of per-frame FPS, which over-weights fast frames).
- **Percentiles** (95, 99, 99.9) of the frame times, with numpy's default linear interpolation.
- **1% low** = FPS equivalent of the mean frame time of the slowest 1% of frames (at least one frame). **0.1% low** is the same with 0.1%. "1% low" has several definitions in other tools, so numbers are only comparable if the definition is the same.
- **Stutter** = a frame slower than `2 x` the rolling median (centred window of 61 frames) **and** at least `5 ms` above that median. These defaults are my own heuristic, not an industry standard and not validated against perception studies.
- **Regression** (comparison) = a metric that is worse than the baseline by more than the threshold (default 5%): lower FPS, or higher frame time.

## Limits

- One capture per build proves nothing: run-to-run variance is not handled and there is no statistical test. Capture each build several times.
- It only sees the frame-time column: it knows nothing about the GPU, driver, settings or scene. Comparing captures of different scenes is meaningless.
- Stutter detection is a heuristic. Slowdowns longer than about half the window are absorbed into the baseline and not flagged (they still appear in the averages and percentiles). The detection loop is plain Python, so it is slow on very long captures.
- Skipped rows are not counted or reported.
- Tests use synthetic data only.

## Results on real captures

*Intentionally empty: no real measurement is included yet.*

- Application: `[game or demo]`
- Machine: `[GPU, CPU, RAM, driver, OS]`
- Settings / scene / capture tool: `[resolution, preset, how the capture was made]`
- Runs per build: `[N]`

| Capture | Frames | Avg FPS | 1% low | 0.1% low | p99 (ms) | Stutters |
|---|---:|---:|---:|---:|---:|---:|
| `[file 1]` | | | | | | |
| `[file 2]` | | | | | | |

## Repository layout

```text
frametime-analyzer/
├── README.md
├── requirements.txt
├── .gitignore
├── frametime_lite.py          # command-line tool (single file)
├── test_frametime_lite.py     # pytest tests (synthetic data)
└── notebooks/
    └── frametime_colab.ipynb  # same code for Google Colab
```