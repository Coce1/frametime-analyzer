"""Tests. All data below is SYNTHETIC (generated here, not from a real game)."""

import numpy as np
import pytest

import frametime_lite as fl


def synthetic(n=3000, base=16.7, seed=0):
    """SYNTHETIC frame times: noise around `base` ms."""
    return np.random.default_rng(seed).normal(base, 0.5, n)


def write(path, header, values):
    path.write_text(header + "\n" + "\n".join(str(v) for v in values) + "\n")


def test_stats_constant():
    s = fl.compute_stats(np.full(1000, 10.0))
    assert s["avg_fps"] == pytest.approx(100.0)
    assert s["low1_fps"] == pytest.approx(100.0)


def test_avg_fps_is_frames_over_duration():
    assert fl.compute_stats(np.array([10.0, 90.0]))["avg_fps"] == pytest.approx(20.0)


def test_stutter_found_at_right_place():
    ft = synthetic()
    ft[1000] = 90.0
    assert [s[0] for s in fl.find_stutters(ft)] == [1000]


def test_no_stutter_in_clean_data():
    assert fl.find_stutters(synthetic()) == []


def test_outlier_in_csv(tmp_path):
    p = tmp_path / "c.csv"
    write(p, "FrameTime", [16.0, 17.0, 5000.0])
    assert fl.load_frame_times(str(p)).max() == 5000.0


def test_empty_file(tmp_path):
    p = tmp_path / "e.csv"
    p.write_text("")
    with pytest.raises(ValueError):
        fl.load_frame_times(str(p))


def test_missing_column(tmp_path):
    p = tmp_path / "m.csv"
    write(p, "A", [1, 2])
    with pytest.raises(ValueError):
        fl.load_frame_times(str(p))


def test_regression_detected():
    base = fl.compute_stats(synthetic())
    slower = fl.compute_stats(synthetic() * 1.2)
    assert fl.compare(base, slower) is True
    assert fl.compare(base, base) is False