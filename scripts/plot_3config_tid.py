#!/usr/bin/env python3
"""
Plot Id-Vg curves from extracted TCAD data (3 configs x 6 TID levels).
Uses mandatory color palette.
"""

import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
PROJECT = Path("/home/rylan/projects/sim-lab/20260427-034614-CNTFET-6T-SRAM-TID-Radiation-Multi-Scale-Simulatio")
OUTPUT_DIR = PROJECT / "data/simulation/tcad/output"

# ── Mandatory color palette ────────────────────────────────────────────────
COLORS_A = ['#081E33', '#1B425E', '#2E6689', '#4E94A0', '#6EC1B1', '#8CD5AB', '#ABEAA4', '#C5F2B0']
BG = "#FFFFFF"
GRID = "#E0E8E2"
TEXT = "#081E33"

plt.rcParams.update({
    'figure.facecolor': BG,
    'axes.facecolor': BG,
    'axes.edgecolor': TEXT,
    'axes.labelcolor': TEXT,
    'xtick.color': TEXT,
    'ytick.color': TEXT,
    'text.color': TEXT,
    'grid.color': GRID,
    'axes.prop_cycle': plt.cycler(color=COLORS_A),
})

CONFIGS = ["configA", "configB", "configC"]
CONFIG_LABELS = {
    "configA": "Config A: SiO2 10nm",
    "configB": "Config B: HfO2 8nm",
    "configC": "Config C: Al2O3(2nm)/HfO2(6nm)",
}
TID_LEVELS = [0, 100, 500, 1000, 5000, 10000]


def main():
    # Load CSV data (manual parsing since config column is string)
    csv_path = OUTPUT_DIR / "iv_curves.csv"
    vg_all = []
    id_all = []
    tid_all = []
    cfg_all = []
    with open(csv_path, 'r') as f:
        header = f.readline()  # skip header
        for line in f:
            parts = line.strip().split(',')
            if len(parts) == 4:
                vg_all.append(float(parts[0]))
                id_all.append(abs(float(parts[1])))
                tid_all.append(float(parts[2]))
                cfg_all.append(parts[3])

    vg_arr = np.array(vg_all)
    id_arr = np.array(id_all)
    tid_arr = np.array(tid_all)
    cfg_arr = np.array(cfg_all)

    # Load metrics for annotations
    with open(OUTPUT_DIR / "metrics.json") as f:
        all_metrics = json.load(f)

    # ── Plot: 3-panel figure, one per config ──────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)

    for ax_idx, config_name in enumerate(CONFIGS):
        ax = axes[ax_idx]
        mask_cfg = cfg_arr == config_name

        for tid_idx, tid_val in enumerate(TID_LEVELS):
            mask = mask_cfg & (tid_arr == tid_val)
            if not np.any(mask):
                continue

            vg_subset = vg_arr[mask]
            id_subset = id_arr[mask]

            # Sort by Vg
            sort_idx = np.argsort(vg_subset)
            vg_subset = vg_subset[sort_idx]
            id_subset = id_subset[sort_idx]

            color = COLORS_A[tid_idx % len(COLORS_A)]
            ax.semilogy(vg_subset, id_subset, '-o', markersize=2, linewidth=1.2,
                        color=color, label=f"TID={int(tid_val)} krad")

        ax.set_xlabel(r'$V_{GS}$ (V)', fontsize=12)
        if ax_idx == 0:
            ax.set_ylabel(r'$|I_{D}|$ per device (A)', fontsize=12)
        ax.set_title(CONFIG_LABELS[config_name], fontsize=11, fontweight='bold')
        ax.set_xlim(0, 1.05)
        ax.set_ylim(1e-16, 1e-4)
        ax.grid(True, alpha=0.3, which='both')
        ax.legend(fontsize=8, loc='lower right', framealpha=0.9)

    fig.suptitle('CNTFET Id-Vg Curves: TID Radiation Degradation (Vds=0.05V)',
                 fontsize=14, fontweight='bold', y=1.02)
    fig.tight_layout()

    plot_path = OUTPUT_DIR / "Id_Vg_curves.png"
    fig.savefig(plot_path, dpi=200, bbox_inches='tight', facecolor=BG)
    print(f"Plot saved: {plot_path}")
    plt.close(fig)

    # ── Plot: Vth shift summary ───────────────────────────────────────────
    fig2, ax2 = plt.subplots(figsize=(8, 5))

    for cfg_idx, config_name in enumerate(CONFIGS):
        vths = []
        tids = []
        for tid_val in TID_LEVELS:
            tid_str = str(tid_val)
            if tid_str in all_metrics.get(config_name, {}):
                vths.append(all_metrics[config_name][tid_str]["vth_V"])
                tids.append(tid_val)

        vth_shift = [v - vths[0] for v in vths]  # shift from TID=0 baseline
        color = COLORS_A[cfg_idx * 2]
        ax2.plot(tids, vth_shift, 'o-', color=color, linewidth=2, markersize=6,
                 label=CONFIG_LABELS[config_name])

    ax2.set_xlabel('TID (krad)', fontsize=12)
    ax2.set_ylabel(r'$\Delta V_{th}$ (V)', fontsize=12)
    ax2.set_title('Threshold Voltage Shift vs Total Ionizing Dose', fontsize=13, fontweight='bold')
    ax2.set_xscale('log')
    ax2.grid(True, alpha=0.3, which='both')
    ax2.legend(fontsize=10)
    ax2.axhline(y=0, color=GRID, linewidth=0.5, linestyle='--')

    plot_path2 = OUTPUT_DIR / "Vth_shift_vs_TID.png"
    fig2.savefig(plot_path2, dpi=200, bbox_inches='tight', facecolor=BG)
    print(f"Vth shift plot saved: {plot_path2}")
    plt.close(fig2)


if __name__ == "__main__":
    main()
