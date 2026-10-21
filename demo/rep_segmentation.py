"""Repetition and phase segmentation from a joint-angle signal.

Illustrative standalone example. It shows the *approach* FlowCali uses to turn
a noisy per-frame joint angle into reps and movement phases; it is not the
production pipeline, contains none of FlowCali's exercise-specific scoring
rules, and its default parameters are demo values rather than calibrated ones.

Adapted from the general signal-processing ideas in FlowCali's
`temporal_smoother`, `rep_counter`, and `phase_detector` modules.

Pipeline:
    raw angle (with NaN dropouts)
      -> smooth_signal()   gap-aware interpolation + Savitzky-Golay filter
      -> detect_reps()     valleys via scipy.signal.find_peaks
      -> assign_phases()   top / descent / bottom / ascent state machine
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.signal import find_peaks, savgol_filter


class NoRepsDetectedError(ValueError):
    """Raised when the signal contains no valley deep enough to be a rep."""


@dataclass
class Phase:
    name: str  # "top" | "descent" | "bottom" | "ascent"
    start: int  # first frame (inclusive)
    end: int  # last frame (exclusive)


@dataclass
class Rep:
    number: int
    start: int  # top position before the bottom
    bottom: int  # deepest frame
    end: int  # top position after the bottom
    phases: list[Phase] = field(default_factory=list)

    def duration(self, fps: float) -> float:
        return (self.end - self.start) / fps


# ---------------------------------------------------------------------------
# Smoothing
# ---------------------------------------------------------------------------

def smooth_signal(
    values: np.ndarray,
    window: int = 7,
    polyorder: int = 3,
    max_gap: int = 10,
) -> np.ndarray:
    """Fill short tracking dropouts and suppress per-frame jitter.

    Pose trackers lose a joint for a few frames at a time (occlusion, motion
    blur). Short gaps are linearly interpolated so the filter has a continuous
    signal; gaps longer than `max_gap` frames are restored to NaN afterwards,
    because inventing a second of motion would be worse than admitting it is
    missing.
    """
    x = np.asarray(values, dtype=float).copy()
    missing = np.isnan(x)
    if missing.all() or (~missing).sum() < 2:
        return x

    idx = np.arange(len(x))
    filled = x.copy()
    filled[missing] = np.interp(idx[missing], idx[~missing], x[~missing])

    wl = min(window, len(x))
    if wl % 2 == 0:
        wl -= 1
    smoothed = filled if wl < 3 else savgol_filter(filled, wl, min(polyorder, wl - 1))

    smoothed[missing & _long_gap_mask(missing, max_gap)] = np.nan
    return smoothed


def _long_gap_mask(missing: np.ndarray, max_gap: int) -> np.ndarray:
    mask = np.zeros(len(missing), dtype=bool)
    start = None
    for i, m in enumerate(np.append(missing, False)):
        if m and start is None:
            start = i
        elif not m and start is not None:
            if i - start > max_gap:
                mask[start:i] = True
            start = None
    return mask


# ---------------------------------------------------------------------------
# Rep detection
# ---------------------------------------------------------------------------

def detect_reps(
    angle: np.ndarray,
    fps: float,
    min_prominence: float = 20.0,
    min_rep_seconds: float = 0.8,
    edge_fraction: float = 0.95,
) -> list[Rep]:
    """One rep per valley (bottom position) in the angle signal.

    - `min_prominence` (degrees) is how far the angle must dip relative to its
      surroundings; it rejects small setup wiggles and residual noise.
    - Interior rep boundaries sit at the highest point between neighbouring
      bottoms, so each rep spans top -> bottom -> top.
    - The first and last reps snap to the nearest frame within `edge_fraction`
      of the local maximum instead of the global one. Real recordings include
      walk-in and walk-out footage; without this, those seconds get absorbed
      into the edge reps.
    """
    arr = _fill_nans(np.asarray(angle, dtype=float))
    if np.isnan(arr).all():
        raise NoRepsDetectedError("Signal is empty.")

    distance = max(int(fps * min_rep_seconds), 1)
    valleys, _ = find_peaks(-arr, distance=distance, prominence=min_prominence)
    if len(valleys) == 0:
        raise NoRepsDetectedError("No valley deep enough to count as a rep.")

    reps: list[Rep] = []
    for i, bottom in enumerate(valleys):
        bottom = int(bottom)
        if i == 0:
            start = _last_near_max(arr, 0, bottom, edge_fraction)
        else:
            prev = int(valleys[i - 1])
            start = prev + int(np.argmax(arr[prev: bottom + 1]))
        if i == len(valleys) - 1:
            end = _first_near_max(arr, bottom, len(arr), edge_fraction)
        else:
            nxt = int(valleys[i + 1])
            end = bottom + int(np.argmax(arr[bottom: nxt + 1]))
        reps.append(Rep(number=i + 1, start=start, bottom=bottom, end=end))
    return reps


def _last_near_max(arr: np.ndarray, lo: int, bottom: int, frac: float) -> int:
    seg = arr[lo: bottom + 1]
    thresh = seg[-1] + frac * (seg.max() - seg[-1])
    hits = np.nonzero(seg >= thresh)[0]
    return lo + int(hits[-1]) if len(hits) else lo


def _first_near_max(arr: np.ndarray, bottom: int, hi: int, frac: float) -> int:
    seg = arr[bottom:hi]
    thresh = seg[0] + frac * (seg.max() - seg[0])
    hits = np.nonzero(seg >= thresh)[0]
    return bottom + int(hits[0]) if len(hits) else hi - 1


def _fill_nans(arr: np.ndarray) -> np.ndarray:
    out = arr.copy()
    missing = np.isnan(out)
    if missing.all() or not missing.any():
        return out
    idx = np.arange(len(out))
    out[missing] = np.interp(idx[missing], idx[~missing], out[~missing])
    return out


# ---------------------------------------------------------------------------
# Phase segmentation
# ---------------------------------------------------------------------------

def assign_phases(
    reps: list[Rep], angle: np.ndarray, band: float = 0.10, hysteresis: float = 0.05
) -> list[Rep]:
    """Label each rep's frames as top / descent / bottom / ascent.

    Within a rep, the top band is the highest `band` fraction of that rep's
    own angle range and the bottom band the lowest. A small state machine walks
    the frames: leaving the top band starts the descent, entering the bottom
    band starts the bottom, leaving it starts the ascent, and re-entering the
    top band ends the rep. Using each rep's own range keeps it working when
    depth varies from rep to rep (e.g. with fatigue).
    """
    arr = np.asarray(angle, dtype=float)
    for rep in reps:
        rep.phases = _phases_for(rep, arr, band, hysteresis)
    return reps


_NEXT = {"top": "descent", "descent": "bottom", "bottom": "ascent", "ascent": "top"}


def _phases_for(rep: Rep, arr: np.ndarray, band: float, hysteresis: float) -> list[Phase]:
    seg = arr[rep.start: rep.end + 1]
    if np.isnan(seg).all() or rep.end <= rep.start:
        return [Phase("full_rep", rep.start, rep.end + 1)]
    lo, hi = np.nanmin(seg), np.nanmax(seg)
    span = hi - lo
    top_t, bottom_t = hi - band * span, lo + band * span
    # Hysteresis: leaving the top or bottom band requires clearing it by an
    # extra margin, so residual jitter at a band edge cannot end a phase after
    # one frame. (A small addition in this demo; not part of FlowCali.)
    margin = hysteresis * span

    def leaves(state: str, v: float) -> bool:
        return {
            "top": v <= top_t - margin,
            "descent": v <= bottom_t,
            "bottom": v > bottom_t + margin,
            "ascent": v >= top_t,
        }[state]

    phases: list[Phase] = []
    state, begin = "top", rep.start
    for i in range(rep.start, rep.end + 1):
        v = arr[i]
        if np.isnan(v):
            continue
        if leaves(state, v):
            if i > begin:
                phases.append(Phase(state, begin, i))
            state, begin = _NEXT[state], i
    phases.append(Phase(state, begin, rep.end + 1))
    return phases


def segment(raw_angle: np.ndarray, fps: float, **rep_kwargs) -> tuple[np.ndarray, list[Rep]]:
    """Convenience wrapper: smooth -> detect reps -> assign phases."""
    smoothed = smooth_signal(raw_angle)
    reps = detect_reps(smoothed, fps, **rep_kwargs)
    return smoothed, assign_phases(reps, smoothed)
