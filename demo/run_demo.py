"""Run the segmentation demo on a synthetic set and save a plot.

    python run_demo.py                 # writes segmentation.png next to this file
    python run_demo.py --reps 7 --seed 3 --out my_plot.png
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from rep_segmentation import segment
from synthetic import make_set

PHASE_COLORS = {
    "top": "#d9ead3",
    "descent": "#fce5cd",
    "bottom": "#f4cccc",
    "ascent": "#cfe2f3",
}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reps", type=int, default=5)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--out", default=str(Path(__file__).with_name("segmentation.png")))
    args = p.parse_args()

    data = make_set(n_reps=args.reps, seed=args.seed)
    smoothed, reps = segment(data.angle, data.fps)
    t = np.arange(len(data.angle)) / data.fps

    print(f"Synthetic set: {len(data.true_bottoms)} reps generated, {len(reps)} detected")
    for r in reps:
        order = " -> ".join(ph.name for ph in r.phases)
        print(f"  rep {r.number}: {t[r.start]:5.2f}s -> bottom {t[r.bottom]:5.2f}s "
              f"-> {t[r.end]:5.2f}s  ({r.duration(data.fps):.2f}s)  [{order}]")

    fig, ax = plt.subplots(figsize=(12, 4.5))
    for r in reps:
        for ph in r.phases:
            ax.axvspan(t[ph.start], t[min(ph.end, len(t) - 1)],
                       color=PHASE_COLORS.get(ph.name, "#eeeeee"), lw=0)
        ax.axvline(t[r.start], color="#555", lw=0.8, ls="--")
        ax.text(t[r.bottom], np.nanmax(smoothed) + 4, f"rep {r.number}",
                ha="center", fontsize=9)
    ax.axvline(t[reps[-1].end], color="#555", lw=0.8, ls="--")

    ax.plot(t, data.angle, ".", ms=2.5, color="#999", label="raw angle (noise + dropouts)")
    ax.plot(t, smoothed, color="#1f4e79", lw=1.8, label="smoothed")
    ax.plot(t[[r.bottom for r in reps]], smoothed[[r.bottom for r in reps]],
            "v", color="#c00000", ms=8, label="detected bottom")
    ax.annotate("setup wiggle\n(rejected)", xy=(t[data.wiggle_frame], 162),
                xytext=(t[data.wiggle_frame] + 0.3, 120), fontsize=8,
                arrowprops=dict(arrowstyle="->", color="#555"))

    handles, labels = ax.get_legend_handles_labels()
    handles += [plt.Rectangle((0, 0), 1, 1, color=c) for c in PHASE_COLORS.values()]
    labels += list(PHASE_COLORS)
    ax.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, -0.14),
              fontsize=8, ncol=7, frameon=False)
    ax.set_xlabel("time (s)")
    ax.set_ylabel("elbow angle (deg)")
    ax.set_ylim(60, 190)
    ax.set_title("Synthetic elbow-angle signal: rep and phase segmentation (illustrative)")
    fig.tight_layout()
    fig.savefig(args.out, dpi=150)
    print(f"Saved plot to {args.out}")


if __name__ == "__main__":
    main()
