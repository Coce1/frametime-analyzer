"""frametime_lite: small frame-time analyser (single file).

Usage:
    python frametime_lite.py capture.csv
    python frametime_lite.py capture.csv --column MyColumn
    python frametime_lite.py before.csv --compare after.csv

Input: CSV with a header and one frame time (in ms) per row.
"""

import argparse
import csv
import sys

import numpy as np

# Column names tried in order when --column is not given (check your own files!).
COMMON_NAMES = ["MsBetweenPresents", "FrameTime", "frametime"]


def load_frame_times(path, column=None):
    """Read a CSV and return the frame times (ms) as a numpy array."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"{path}: file is empty")
        if column is None:
            column = next((n for n in COMMON_NAMES if n in reader.fieldnames), None)
            if column is None:
                raise ValueError(f"No frame-time column found. Columns: {reader.fieldnames}. Use --column.")
        elif column not in reader.fieldnames:
            raise ValueError(f"Column {column!r} not found. Columns: {reader.fieldnames}")
        values = []
        for row in reader:
            try:
                v = float(row[column])
            except (TypeError, ValueError):
                continue  # skip bad rows
            if v > 0:
                values.append(v)
    if not values:
        raise ValueError(f"{path}: no valid frame times in column {column!r}")
    return np.array(values)


def low_fps(ft, fraction):
    """FPS of the average of the slowest `fraction` of frames (e.g. 0.01 = 1% low)."""
    k = max(1, int(np.ceil(len(ft) * fraction - 1e-9)))
    slowest = np.sort(ft)[-k:]
    return 1000.0 / slowest.mean()


def compute_stats(ft):
    """Return a dict of summary metrics."""
    return {
        "frames": len(ft),
        "duration_s": ft.sum() / 1000.0,
        "avg_fps": len(ft) * 1000.0 / ft.sum(),
        "mean_ms": ft.mean(),
        "median_ms": np.median(ft),
        "p95_ms": np.percentile(ft, 95),
        "p99_ms": np.percentile(ft, 99),
        "p999_ms": np.percentile(ft, 99.9),
        "low1_fps": low_fps(ft, 0.01),
        "low01_fps": low_fps(ft, 0.001),
    }


def find_stutters(ft, factor=2.0, window=61, min_excess_ms=5.0):
    """Frames slower than `factor` x the local (rolling) median, and at least
    `min_excess_ms` above it. Returns a list of (frame_index, time_s, frame_ms)."""
    half = window // 2
    start_times = (np.cumsum(ft) - ft) / 1000.0
    found = []
    for i in range(len(ft)):
        local = np.median(ft[max(0, i - half): i + half + 1])
        if ft[i] > factor * local and ft[i] - local >= min_excess_ms:
            found.append((i, start_times[i], ft[i]))
    return found


def print_report(stats, stutters):
    print(f"Frames: {stats['frames']}   Duration: {stats['duration_s']:.1f} s")
    print(f"Average FPS: {stats['avg_fps']:.1f}")
    print(f"Frame time (ms): mean {stats['mean_ms']:.2f}, median {stats['median_ms']:.2f}")
    print(f"Percentiles (ms): p95 {stats['p95_ms']:.2f}, p99 {stats['p99_ms']:.2f}, p99.9 {stats['p999_ms']:.2f}")
    print(f"1% low: {stats['low1_fps']:.1f} FPS   0.1% low: {stats['low01_fps']:.1f} FPS")
    print(f"Stutters: {len(stutters)}")
    for i, t, ms in stutters[:20]:
        print(f"  frame {i} at {t:.2f} s: {ms:.1f} ms")
    if len(stutters) > 20:
        print(f"  ... and {len(stutters) - 20} more")


def compare(base, cand, threshold_pct=5.0):
    """Print a before/after table. Returns True if any metric regressed."""
    higher_is_better = {"avg_fps", "low1_fps", "low01_fps"}
    keys = ["avg_fps", "median_ms", "p95_ms", "p99_ms", "p999_ms", "low1_fps", "low01_fps"]
    regressed = False
    for k in keys:
        change = (cand[k] - base[k]) / base[k] * 100
        worse = -change if k in higher_is_better else change
        flag = ""
        if worse > threshold_pct:
            flag = "  <-- REGRESSION"
            regressed = True
        print(f"{k:10s} {base[k]:9.2f} -> {cand[k]:9.2f}  ({change:+.1f}%){flag}")
    return regressed


def save_plot(ft, stutters, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    t = (np.cumsum(ft) - ft) / 1000.0
    plt.figure(figsize=(10, 4))
    plt.plot(t, ft, linewidth=0.6)
    if stutters:
        plt.scatter([s[1] for s in stutters], [s[2] for s in stutters], color="red", s=12, label="stutters")
        plt.legend()
    plt.xlabel("Time (s)")
    plt.ylabel("Frame time (ms)")
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()


def main():
    parser = argparse.ArgumentParser(description="Analyse frame-time captures.")
    parser.add_argument("csv")
    parser.add_argument("--column")
    parser.add_argument("--compare", help="second capture to compare against (candidate)")
    parser.add_argument("--threshold", type=float, default=5.0, help="regression threshold in %%")
    parser.add_argument("--plot", default="frametimes.png")
    args = parser.parse_args()

    try:
        ft = load_frame_times(args.csv, args.column)
        stats = compute_stats(ft)
        stutters = find_stutters(ft)
        print_report(stats, stutters)
        save_plot(ft, stutters, args.plot)
        print(f"Plot saved to {args.plot}")
        if args.compare:
            ft2 = load_frame_times(args.compare, args.column)
            print("\nComparison (baseline -> candidate):")
            if compare(stats, compute_stats(ft2), args.threshold):
                return 1
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())