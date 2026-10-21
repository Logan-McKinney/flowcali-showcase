"""Synthetic elbow-angle sequences with known ground truth.

The generated signal imitates what a side-on pose tracker produces for a set
of push-up-style reps: a lead-in with arms straight, reps of varying depth and
tempo with short pauses at the top, a small setup wiggle that should NOT count
as a rep, Gaussian jitter, and tracking dropouts (NaN). No real footage or
real landmarks are involved.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class SyntheticSet:
    angle: np.ndarray  # raw per-frame angle in degrees, NaN where tracking dropped
    clean: np.ndarray  # the same signal before noise/dropouts
    fps: float
    true_bottoms: list[int]  # frame index of each real rep's deepest point
    true_starts: list[int]  # frame index where each real rep begins descending
    wiggle_frame: int  # centre of the setup wiggle (not a rep)


def make_set(
    n_reps: int = 5,
    fps: float = 30.0,
    top: float = 170.0,
    seed: int = 7,
    noise_deg: float = 2.5,
    dropout_gaps: tuple[tuple[float, float], ...] = ((0.25, 0.1), (0.6, 0.2)),
    long_gap: tuple[float, float] | None = None,
) -> SyntheticSet:
    """Build a synthetic set.

    dropout_gaps: (position as fraction of the clip, length in seconds) pairs.
    long_gap: optional gap that should survive smoothing as NaN.
    """
    rng = np.random.default_rng(seed)
    pieces: list[np.ndarray] = []
    bottoms: list[int] = []
    starts: list[int] = []
    t = 0

    def hold(seconds: float, level: float) -> None:
        nonlocal t
        n = int(seconds * fps)
        pieces.append(np.full(n, level))
        t += n

    # Lead-in: arms straight, plus a shallow setup wiggle (~8 deg).
    hold(1.2, top)
    n = int(0.6 * fps)
    wiggle = top - 8.0 * np.sin(np.linspace(0, np.pi, n))
    wiggle_frame = t + n // 2
    pieces.append(wiggle)
    t += n
    hold(0.8, top)

    for _ in range(n_reps):
        depth = rng.uniform(80.0, 100.0)  # bottom elbow angle varies rep to rep
        down = rng.uniform(0.9, 1.3)
        pause = rng.uniform(0.1, 0.25)
        up = rng.uniform(0.8, 1.2)
        starts.append(t)
        nd, npz, nu = int(down * fps), int(pause * fps), int(up * fps)
        descent = top - (top - depth) * (1 - np.cos(np.linspace(0, np.pi, nd))) / 2
        ascent = depth + (top - depth) * (1 - np.cos(np.linspace(0, np.pi, nu))) / 2
        pieces += [descent, np.full(npz, depth), ascent]
        bottoms.append(t + nd + npz // 2)
        t += nd + npz + nu
        hold(rng.uniform(0.3, 0.7), top)

    hold(1.5, top)  # walk-off

    clean = np.concatenate(pieces)
    raw = clean + rng.normal(0.0, noise_deg, len(clean))
    for frac, secs in dropout_gaps:
        s = int(frac * len(raw))
        raw[s: s + int(secs * fps)] = np.nan
    if long_gap is not None:
        frac, secs = long_gap
        s = int(frac * len(raw))
        raw[s: s + int(secs * fps)] = np.nan

    return SyntheticSet(raw, clean, fps, bottoms, starts, wiggle_frame)
