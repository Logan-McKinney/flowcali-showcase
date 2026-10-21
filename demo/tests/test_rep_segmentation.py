from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rep_segmentation import (  # noqa: E402
    NoRepsDetectedError,
    assign_phases,
    detect_reps,
    segment,
    smooth_signal,
)
from synthetic import make_set  # noqa: E402


@pytest.mark.parametrize("seed", range(10))
@pytest.mark.parametrize("n_reps", [1, 4, 8])
def test_counts_every_rep_and_ignores_setup_wiggle(seed, n_reps):
    data = make_set(n_reps=n_reps, seed=seed)
    _, reps = segment(data.angle, data.fps)
    assert len(reps) == n_reps
    assert all(abs(r.bottom - data.wiggle_frame) > data.fps for r in reps)


def test_detected_bottoms_are_close_to_ground_truth():
    data = make_set(n_reps=6, seed=1)
    _, reps = segment(data.angle, data.fps)
    tolerance = int(0.2 * data.fps)
    for rep, truth in zip(reps, data.true_bottoms):
        assert abs(rep.bottom - truth) <= tolerance


def test_edge_reps_exclude_lead_in_and_walk_off():
    data = make_set(n_reps=3, seed=2)
    _, reps = segment(data.angle, data.fps)
    # The first rep should begin near the true descent, not at frame 0.
    assert abs(reps[0].start - data.true_starts[0]) <= int(0.3 * data.fps)
    # The last rep should end well before the 1.5 s walk-off finishes.
    assert reps[-1].end < len(data.angle) - int(1.0 * data.fps)


@pytest.mark.parametrize("seed", range(10))
def test_phases_follow_movement_order(seed):
    data = make_set(n_reps=5, seed=seed)
    _, reps = segment(data.angle, data.fps)
    for rep in reps:
        names = [p.name for p in rep.phases]
        assert names[:4] == ["top", "descent", "bottom", "ascent"]
        # Phases tile the rep with no gaps or overlaps.
        for a, b in zip(rep.phases, rep.phases[1:]):
            assert a.end == b.start
        bottom_phase = next(p for p in rep.phases if p.name == "bottom")
        assert bottom_phase.start <= rep.bottom < bottom_phase.end


def test_short_gaps_filled_long_gaps_left_missing():
    data = make_set(n_reps=3, seed=5, dropout_gaps=((0.3, 0.2),), long_gap=(0.7, 1.0))
    smoothed = smooth_signal(data.angle, max_gap=10)
    short_start = int(0.3 * len(data.angle))
    long_start = int(0.7 * len(data.angle))
    assert not np.isnan(smoothed[short_start: short_start + 6]).any()
    assert np.isnan(smoothed[long_start: long_start + 30]).all()


def test_smoothing_reduces_jitter():
    data = make_set(n_reps=4, seed=6, dropout_gaps=())
    smoothed = smooth_signal(data.angle)
    raw_err = np.std(data.angle - data.clean)
    smooth_err = np.std(smoothed - data.clean)
    assert smooth_err < raw_err


def test_flat_signal_raises():
    with pytest.raises(NoRepsDetectedError):
        detect_reps(np.full(300, 170.0) + np.random.default_rng(0).normal(0, 1, 300), fps=30)


def test_phase_assignment_on_hand_built_rep():
    angle = np.concatenate([
        np.full(10, 170.0),
        np.linspace(170, 90, 20),
        np.full(5, 90.0),
        np.linspace(90, 170, 20),
        np.full(10, 170.0),
    ])
    reps = assign_phases(detect_reps(angle, fps=30), angle)
    assert len(reps) == 1
    assert [p.name for p in reps[0].phases][:4] == ["top", "descent", "bottom", "ascent"]
