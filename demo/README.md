# Rep & phase segmentation demo

A small, standalone version of the signal-processing idea behind FlowCali's rep
counting. It generates a **synthetic** elbow-angle signal, smooths it, finds
the reps, and labels each rep's movement phases.

![Segmentation of a synthetic signal](segmentation.png)

*Illustrative only.* It isn't the production pipeline and it isn't an accuracy
benchmark. The data is synthetic, the parameters are demo defaults, and none of
FlowCali's exercise-specific form checks or calibrated thresholds are included.

## Run it

Python 3.10+:

```sh
cd demo
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python run_demo.py               # prints the reps and saves segmentation.png
python run_demo.py --reps 8 --seed 3 --out other.png
python -m pytest tests -q
```

## What's in it

| File | Purpose |
|---|---|
| `synthetic.py` | Builds a set of push-up-like reps with varying depth and tempo, a lead-in and walk-off at lockout, a small setup wiggle, jitter, and tracking dropouts. The true rep positions are known. |
| `rep_segmentation.py` | `smooth_signal` → `detect_reps` → `assign_phases` |
| `run_demo.py` | Runs the pipeline and plots it |
| `tests/` | Checks the pipeline against the synthetic ground truth |

**Smoothing.** Short dropouts are linearly interpolated; a Savitzky-Golay
filter removes jitter but keeps the shape of the movement; long gaps are put
back to `NaN` instead of being invented.

**Reps.** Each rep bottom is a valley found with `scipy.signal.find_peaks` on
the negated angle, with a minimum prominence (which rejects the setup wiggle)
and a minimum spacing. Boundaries between reps sit at the highest point between
two bottoms. The first and last rep snap to the nearest near-lockout frame so
lead-in and walk-off time isn't counted.

**Phases.** A state machine walks each rep through top → descent → bottom →
ascent, using bands relative to that rep's own range, with a little hysteresis
so jitter at a band edge can't end a phase after one frame. The hysteresis is
an addition made for this demo, found when one of the randomized tests failed
without it.

**Tests** check, across several random seeds and rep counts: the right number
of reps is found and the wiggle is ignored; detected bottoms land near the true
ones; edge reps exclude the lead-in and walk-off; phases come in order and tile
each rep; short gaps are filled but long ones are left missing; smoothing
reduces error against the clean signal; a flat signal raises an error.

Adapted from the general approach in FlowCali's private `temporal_smoother`,
`rep_counter`, and `phase_detector` modules.
