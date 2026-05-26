#!/usr/bin/env python3
"""
TCAD_EXTRACT: Extract Id-Vg data from 3-config x 6-TID SDevice PLT files.

Parses DF-ISE .plt format, computes device metrics, generates:
  - iv_curves.csv
  - metrics.json
  - interface.json (3 configs x 6 TID points)
  - Id_Vg_curves.png

File selection logic:
  - For all runs: use IdVg_sdevice_IdVg.plt (the actual Vg sweep output)
  - For configB/configC TID_0: combine phase1 (Vg 0-0.3V) + IdVg (Vg 0.3-1.0V)
    to get full-range 3-eq data, rather than using 2-eq files
"""

import json
import re
import numpy as np
from pathlib import Path
from datetime import datetime, timezone

# ── Paths ──────────────────────────────────────────────────────────────────
PROJECT = Path("/home/rylan/projects/sim-lab/20260427-034614-CNTFET-6T-SRAM-TID-Radiation-Multi-Scale-Simulatio")
BASE_DIR = PROJECT / "workspace/tcad/production/sdevice-3config-tid-ec2"
OUTPUT_DIR = PROJECT / "data/simulation/tcad/output"

CONFIGS = ["configA", "configB", "configC"]
CONFIG_LABELS = {
    "configA": "SiO2 10nm",
    "configB": "HfO2 8nm",
    "configC": "Al2O3(2nm)/HfO2(6nm)",
}
TID_LEVELS = [0, 100, 500, 1000, 5000, 10000]

AREA_FACTOR = 1e6  # 1e6 CNTs per device
VDD = 1.0


# ── DF-ISE PLT Parser ─────────────────────────────────────────────────────

def parse_plt_header(filepath: Path) -> list[str]:
    """Parse the datasets list from DF-ISE PLT file header.
    Returns list of column names like ["time", "gate OuterVoltage", ...].
    Uses name-based lookup - never hardcodes indices.
    """
    buf = ""
    with open(filepath, 'r') as f:
        in_datasets = False
        for line in f:
            stripped = line.strip()
            if stripped.startswith('datasets'):
                in_datasets = True
                rest = stripped[len('datasets'):].strip()
                if rest.startswith('='):
                    rest = rest[1:].strip()
                if rest.startswith('['):
                    rest = rest[1:]
                buf += rest + " "
                continue
            if in_datasets:
                if ']' in stripped:
                    buf += stripped[:stripped.index(']')]
                    break
                buf += stripped + " "
    return re.findall(r'"([^"]+)"', buf)


def parse_plt_data(filepath: Path, datasets: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """Parse the Data block from a DF-ISE PLT file.
    Returns (vg_array, id_array) using name-based column lookup.
    """
    vg_idx = datasets.index("gate OuterVoltage")
    id_idx = datasets.index("drain TotalCurrent")
    ncols = len(datasets)

    all_values: list[float] = []
    with open(filepath, 'r') as f:
        in_data = False
        for line in f:
            stripped = line.strip()
            if stripped == "Data {":
                in_data = True
                continue
            if stripped == "}":
                if in_data:
                    break
                continue
            if not in_data:
                continue
            for token in stripped.split():
                try:
                    all_values.append(float(token))
                except ValueError:
                    pass

    ntotal = len(all_values)
    nrows = ntotal // ncols
    if nrows == 0:
        raise ValueError(f"No data rows found in {filepath}")

    data = np.array(all_values[:nrows * ncols]).reshape(nrows, ncols)
    return data[:, vg_idx], data[:, id_idx]


def load_idvg(output_dir: Path) -> tuple[np.ndarray, np.ndarray, str]:
    """Load the best available Id-Vg data from an output directory.

    Strategy:
      1. For configB/configC at TID_0: the 3-eq staged simulation split Vg into
         phase1 (0-0.3V) and main sweep (0.3-1.0V). We stitch these together
         to get the full-range 3-eq result.
      2. For all other runs: IdVg_sdevice_IdVg.plt has the full sweep.

    Returns (vg, id_raw, source_description).
    """
    # Check if this is a staged baseline fix case
    phase1_file = output_dir / "phase1_sdevice_baseline_fix_IdVg.plt"
    main_fix_file = output_dir / "IdVg_fix_sdevice_baseline_fix_IdVg.plt"

    if phase1_file.exists() and main_fix_file.exists():
        # Stitched 3-eq: combine phase1 + main sweep
        ds = parse_plt_header(phase1_file)
        vg1, id1 = parse_plt_data(phase1_file, ds)
        ds2 = parse_plt_header(main_fix_file)
        vg2, id2 = parse_plt_data(main_fix_file, ds2)

        # Remove overlap at Vg=0.3V boundary (keep phase1 up to boundary,
        # skip first point of main that duplicates)
        if len(vg2) > 1 and vg2[0] <= vg1[-1]:
            vg2 = vg2[1:]
            id2 = id2[1:]

        vg = np.concatenate([vg1, vg2])
        id_raw = np.concatenate([id1, id2])
        return vg, id_raw, "stitched 3-eq (phase1+main)"

    # Standard case: IdVg_sdevice_IdVg.plt has the full Vg sweep
    main_plt = output_dir / "IdVg_sdevice_IdVg.plt"
    if main_plt.exists() and main_plt.stat().st_size > 100:
        ds = parse_plt_header(main_plt)
        vg, id_raw = parse_plt_data(main_plt, ds)
        # Verify this has a real Vg sweep (not just Vg=0)
        if len(vg) > 5 and vg.max() > 0.1:
            return vg, id_raw, "IdVg_sdevice_IdVg.plt (3-eq)"

    # Fallback: sdevice_IdVg.plt (initial bias only - limited data)
    fallback = output_dir / "sdevice_IdVg.plt"
    if fallback.exists() and fallback.stat().st_size > 100:
        ds = parse_plt_header(fallback)
        vg, id_raw = parse_plt_data(fallback, ds)
        if len(vg) > 2:
            return vg, id_raw, "sdevice_IdVg.plt (fallback)"

    raise FileNotFoundError(f"No usable IdVg PLT in {output_dir}")


# ── Device Metrics Extraction ──────────────────────────────────────────────

def compute_metrics(vg: np.ndarray, id_per_device: np.ndarray) -> dict:
    """Extract Vth, Ion, Ioff, On/Off, gm_max, SS from Id-Vg curve."""
    # Sort by Vg
    sort_idx = np.argsort(vg)
    vg = vg[sort_idx]
    id_dev = np.abs(id_per_device[sort_idx])

    # ── Ion: Id at Vg = Vdd ──
    idx_vdd = np.argmin(np.abs(vg - VDD))
    ion = id_dev[idx_vdd]

    # ── Ioff: minimum Id in low-Vg region (Vg < 0.2V) ──
    low_vg_mask = vg < 0.2
    if np.any(low_vg_mask):
        ioff = np.min(id_dev[low_vg_mask])
    else:
        ioff = np.min(id_dev[:max(1, len(id_dev) // 10)])

    # ── On/Off ratio ──
    on_off = ion / ioff if ioff > 0 else float('inf')

    # ── gm = dId/dVg (per device) ──
    dId = np.diff(id_dev)
    dVg = np.diff(vg)
    valid = np.abs(dVg) > 1e-15
    gm = np.zeros_like(dId)
    gm[valid] = dId[valid] / dVg[valid]
    gm_max = float(np.max(gm))

    # ── Vth: linear extrapolation from max-gm point ──
    gm_max_idx = int(np.argmax(gm))
    if gm_max > 0:
        vth = vg[gm_max_idx] - id_dev[gm_max_idx] / gm_max
    else:
        vth = 0.0

    # ── SS: subthreshold swing, only in subthreshold region ──
    # Id_per_device in [1e-12, 1e-8] A -- only compute where Id is in this window
    ss_values = []
    for i in range(1, len(id_dev) - 1):
        if 1e-12 <= id_dev[i] <= 1e-8:
            dVg_local = vg[i + 1] - vg[i - 1]
            if id_dev[i + 1] > 0 and id_dev[i - 1] > 0:
                dlogId = np.log10(id_dev[i + 1]) - np.log10(id_dev[i - 1])
                if abs(dlogId) > 1e-12:
                    ss_local = abs(dVg_local / dlogId) * 1000  # mV/dec
                    if ss_local < 500:  # sanity cap
                        ss_values.append(ss_local)

    ss = min(ss_values) if ss_values else float('nan')

    return {
        "vth_V": round(float(vth), 4),
        "ion_per_device_A": float(ion),
        "ioff_per_device_A": float(ioff),
        "on_off_ratio": float(on_off),
        "gm_max_per_device_A_per_V": float(gm_max),
        "ss_mV_per_dec": round(float(ss), 1) if not np.isnan(ss) else None,
    }


# ── Main Extraction ────────────────────────────────────────────────────────

def main():
    all_rows: list[dict] = []
    all_metrics: dict[str, dict] = {}
    interface_configs: list[dict] = []

    for config in CONFIGS:
        all_metrics[config] = {}
        config_sweeps: list[dict] = []

        for tid in TID_LEVELS:
            tid_dir = BASE_DIR / config / f"TID_{tid}" / "output"
            if not tid_dir.exists():
                print(f"WARNING: {tid_dir} does not exist, skipping")
                continue

            try:
                vg, id_raw, source = load_idvg(tid_dir)
            except (FileNotFoundError, ValueError) as e:
                print(f"WARNING: {config}/TID_{tid}: {e}")
                continue

            # Normalize by AreaFactor
            id_per_device = id_raw / AREA_FACTOR

            print(f"[{config}/TID_{tid}] source={source}  "
                  f"{len(vg)} pts  Vg=[{vg.min():.4f}, {vg.max():.4f}]  "
                  f"|Id/dev|=[{np.abs(id_per_device).min():.2e}, "
                  f"{np.abs(id_per_device).max():.2e}]")

            # Compute metrics
            metrics = compute_metrics(vg, id_per_device)
            metrics["tid_krad"] = tid
            metrics["config"] = config
            metrics["config_label"] = CONFIG_LABELS[config]
            metrics["sweep_points"] = int(len(vg))
            metrics["vg_sweep_range"] = [round(float(vg.min()), 4),
                                          round(float(vg.max()), 4)]
            metrics["source"] = source

            all_metrics[config][str(tid)] = metrics
            print(f"  Vth={metrics['vth_V']:.4f}V  "
                  f"Ion={metrics['ion_per_device_A']:.2e}A  "
                  f"Ioff={metrics['ioff_per_device_A']:.2e}A  "
                  f"On/Off={metrics['on_off_ratio']:.1e}  "
                  f"SS={metrics['ss_mV_per_dec']}mV/dec")

            # CSV rows
            for v, i in zip(vg, id_per_device):
                all_rows.append({
                    "vg_V": round(float(v), 6),
                    "id_per_device_A": float(i),
                    "tid_krad": tid,
                    "config": config,
                })

            # Interface sweep entry
            config_sweeps.append({
                "tid_krad": tid,
                "equation_type": "3eq",
                "vth_V": metrics["vth_V"],
                "ion_per_device_A": metrics["ion_per_device_A"],
                "ioff_per_device_A": metrics["ioff_per_device_A"],
                "on_off_ratio": metrics["on_off_ratio"],
                "gm_max_per_device_A_per_V": metrics["gm_max_per_device_A_per_V"],
                "ss_mV_per_dec": metrics["ss_mV_per_dec"],
                "sweep_points": metrics["sweep_points"],
                "vg_sweep_range": metrics["vg_sweep_range"],
            })

        interface_configs.append({
            "config_name": config,
            "config_label": CONFIG_LABELS[config],
            "dielectric": CONFIG_LABELS[config],
            "tid_sweep": config_sweeps,
        })

    # ── Write CSV ──────────────────────────────────────────────────────────
    csv_path = OUTPUT_DIR / "iv_curves.csv"
    with open(csv_path, 'w') as f:
        f.write("vg_V,id_per_device_A,tid_krad,config\n")
        for row in all_rows:
            f.write(f"{row['vg_V']},{row['id_per_device_A']},"
                    f"{row['tid_krad']},{row['config']}\n")
    print(f"\nCSV written: {csv_path} ({len(all_rows)} rows)")

    # ── Write metrics.json ─────────────────────────────────────────────────
    metrics_path = OUTPUT_DIR / "metrics.json"
    with open(metrics_path, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    print(f"Metrics written: {metrics_path}")

    # ── Write interface.json ───────────────────────────────────────────────
    interface = {
        "extraction_method": "programmatic (Sentaurus SDevice PLT parser)",
        "interface_version": "1.0",
        "extraction_timestamp": datetime.now(timezone.utc).isoformat(),
        "device_type": "CNTFET",
        "device_configs": interface_configs,
        "contact_type": "Schottky (Sc WF=4.0eV)",
        "gate_wf": 4.65,
        "area_factor": AREA_FACTOR,
        "vds_operating_V": 0.05,
        "source_files": "workspace/tcad/production/sdevice-3config-tid-ec2/",
        "n_configs": len(interface_configs),
        "n_tid_per_config": len(TID_LEVELS),
    }
    interface_path = OUTPUT_DIR / "interface.json"
    with open(interface_path, 'w') as f:
        json.dump(interface, f, indent=2)
    print(f"Interface written: {interface_path}")

    # ── Data Validation ────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("DATA VALIDATION")
    print("=" * 60)

    for config in CONFIGS:
        print(f"\n--- {config} ({CONFIG_LABELS[config]}) ---")
        vths = []
        for tid in TID_LEVELS:
            tid_str = str(tid)
            if tid_str in all_metrics.get(config, {}):
                m = all_metrics[config][tid_str]
                vths.append(m["vth_V"])
                print(f"  TID={tid:>5d} krad: Vth={m['vth_V']:.4f}V  "
                      f"Ion={m['ion_per_device_A']:.2e}A  "
                      f"Ioff={m['ioff_per_device_A']:.2e}A  "
                      f"On/Off={m['on_off_ratio']:.1e}  "
                      f"SS={m['ss_mV_per_dec']}mV/dec")

        for v in vths:
            if abs(v) > 2.0:
                print(f"  WARNING: Vth={v:.4f}V outside ±2V range!")
        if len(vths) >= 2:
            print(f"  Vth range: {min(vths):.4f} to {max(vths):.4f}V")

    # Cross-config check
    if all(c in all_metrics for c in CONFIGS):
        print("\n--- Cross-config degradation check ---")
        for tid in [100, 500, 1000, 5000, 10000]:
            tid_str = str(tid)
            vths_cross = {}
            for config in CONFIGS:
                if tid_str in all_metrics[config]:
                    vths_cross[config] = all_metrics[config][tid_str]["vth_V"]
            if len(vths_cross) == 3:
                print(f"  TID={tid:>5d} krad: "
                      f"Vth_A={vths_cross['configA']:.4f}  "
                      f"Vth_B={vths_cross['configB']:.4f}  "
                      f"Vth_C={vths_cross['configC']:.4f}")

    print("\nExtraction complete.")
    return all_metrics


if __name__ == "__main__":
    main()
