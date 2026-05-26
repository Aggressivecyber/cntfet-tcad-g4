#!/usr/bin/env python3
"""
6T SRAM TID Radiation Degradation Simulation via ngspice + BSIM-CMG OSDI.

Reads TCAD-extracted parameters from metrics.json, calibrates BSIM-CMG model cards,
generates 6T SRAM netlists, runs ngspice simulations, and extracts SNM + Write Margin.

Key technical notes:
- BSIM-CMG via OSDI: device instances use N prefix (M/P reserved by ngspice).
- PHIG controls Vth with ~1:1 linear relationship: PHIG = Vth + 4.216 (calibrated).
- Model continuation lines use + prefix.
"""

import json
import os
import subprocess
import sys
import numpy as np
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone

# ── Paths ──────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path("/home/rylan/projects/sim-lab/20260427-034614-CNTFET-6T-SRAM-TID-Radiation-Multi-Scale-Simulatio")
TCAD_DATA = PROJECT_ROOT / "data/simulation/tcad/output/metrics.json"
WORKSPACE = PROJECT_ROOT / "workspace/ngspice/production/sram-6t-tid"
SRC_DIR = WORKSPACE / "src"
OUTPUT_DIR = WORKSPACE / "output"
LOGS_DIR = WORKSPACE / "logs"
DATA_OUTPUT = PROJECT_ROOT / "data/simulation/ngspice/output"

VDD = 0.9
CONFIGS = ["configA", "configB", "configC"]
TID_LEVELS = [0, 100, 500, 1000, 5000, 10000]

# PHIG calibration per config: PHIG = Vth + PHIG_OFFSET
# Calibrated against corrected BSIM-CMG dielectric parameters
PHIG_OFFSET = {
    "configA": 4.216,    # SiO2 (unchanged)
    "configB": 4.118,    # HfO2 (recalibrated for EPSROX=25)
    "configC": 4.121,    # Al2O3/HfO2 bilayer (recalibrated for EPSROX=17.3)
}

# Dielectric parameters per config (physically correct values)
DIELECTRIC_PARAMS = {
    "configA": {"eot": 1.50e-9, "toxp": 2.10e-9, "epsrox": 3.9, "label": "SiO2 10nm"},
    "configB": {"eot": 1.248e-9, "toxp": 8.00e-9, "epsrox": 25.0, "label": "HfO2 8nm"},
    "configC": {"eot": 1.803e-9, "toxp": 8.00e-9, "epsrox": 17.3, "label": "Al2O3(2nm)/HfO2(6nm)"},
}


def make_model_lines(params_str):
    """Convert a multi-line parameter string into BSIM-CMG model card lines with + prefix."""
    lines = []
    for line in params_str.strip().splitlines():
        line = line.strip()
        if line:
            lines.append(f"+ {line}")
    return "\n".join(lines)


def build_nmos_model(model_name, phig, u0, eot, toxp, epsrox):
    """Build BSIM-CMG NMOS model card with proper continuation."""
    base_params = """\
BULKMOD = 1 CGEOMOD = 0 TYPE = 1 GEOMOD = 0
GIDLMOD = 1 IGBMOD = 0 IGCMOD = 1 IIMOD = 0
NGATE = 0 NQSMOD = 0 RDSMOD = 0 RGATEMOD = 0 RGEOMOD = 0
SDTERM = 0 SHMOD = 0
AGIDL = 1e-12 AGISL = 1e-12
CDSC = 0.01 CDSCD = 0.01
CFD = 0.2e-10 CFS = 0.2e-10
CGDO = 1e-10 CGSO = 1e-10
CTH0 = 0.000001243
DELTAVSAT = 0.5 DROUT = 1 DSUB = 0.5
DVT0 = 0.05 DVT1 = 0.5 DVTSHIFT = 0
EASUB = 4.05 EOTACC = 1e-10 EOTBOX = 1.40e-7
EPSRSUB = 11.9
ETA0 = 0.05 ETAMOB = 2 EU = 1.2
FPITCH = 4e-8 HFIN = 3e-8
IGT = 2.5 K1RSCE = 0 KSATIV = 2
KT1 = 0 KT1L = 0
LINT = -2e-9 LPE0 = 0 LCDSCD = 5e-5 LCDSCDR = 5e-5
LRDSW = 0.2 LVSAT = 0
MEXP = 4 NBODY = 1e22 NC0SUB = 2.86e25 NI0SUB = 1.1e16 NSD = 2e26
PCLM = 0.05 PCLMCV = 0.013 PCLMG = 0
PDIBL1 = 0 PDIBL2 = 0.002
PHIN = 0.05 POXEDGE = 1.1 PQM = 0.66
PRT = 0 PTWG = 0 PTWGT = 0.004 PVAG = 0
QM0 = 0.001 QMFACTOR = 2.5
RDSW = 200 RDSWMIN = 0 RDWMIN = 0 RSHD = 0 RSHS = 0 RSWMIN = 0
RTH0 = 0.225
TBGASUB = 4.73e-4 TBGBSUB = 636
TFIN = 1.4e-8 TGIDL = -0.007 TMEXP = 0
TNOM = 25
UA = 0.55 UA1 = 0.001032 UCS = 1 UCSTE = -0.004775
UD = 0 UD1 = 0 UP = 0 UTE = -0.7 UTL = 0
VSAT = 80000 WR = 1 WTH0 = 2.6e-7 XL = 0"""
    tail = f"""\
PHIG = {phig:.4f}
EOT = {eot:.2e}
TOXP = {toxp:.2e}
EPSROX = {epsrox:.1f}
EPSRSP = {epsrox:.1f}
U0 = {u0:.6f}"""

    return f".model {model_name} bsimcmg_va\n{make_model_lines(base_params)}\n{make_model_lines(tail)}\n"


def build_pmos_model(model_name, phig, eot, toxp, epsrox):
    """Build BSIM-CMG PMOS model card with proper continuation."""
    base_params = """\
BULKMOD = 1 CGEOMOD = 0 TYPE = 0 GEOMOD = 0
GIDLMOD = 1 IGBMOD = 0 IGCMOD = 1 IIMOD = 0
NGATE = 0 NQSMOD = 0 RDSMOD = 0 RGATEMOD = 0 RGEOMOD = 0
SDTERM = 0 SHMOD = 0
AGIDL = 2e-12 AGISL = 2e-12
AIGC = 0.007 AIGD = 0.006 AIGS = 0.006
AT = 0.0008234
CDSC = 0.003469 CDSCD = 0.001486
CFD = 0.2e-10 CFS = 0.2e-10
CGDO = 1e-10 CGSO = 1e-10
CIT = 0
CKAPPAD = 0.6 CKAPPAS = 0.6
CTH0 = 1.243e-6
DELTAVSAT = 11.56 DELTAW = 0 DELTAWCV = -1e-8
DLBIN = 0 DLC = -9.2e-9 DLCIGD = 5e-9 DLCIGS = 5e-9
DROUT = 4.97 DSUB = 0.5
DVT0 = 0.05006 DVT1 = 0.4 DVTSHIFT = 0
EASUB = 4.05 EOTACC = 3e-10 EOTBOX = 1.40e-7
EPSRSUB = 11.9
ETA0 = 0.03952 ETAMOB = 4 EU = 0.05
FPITCH = 4e-8 HFIN = 3e-8
IGT = 3.5 K1RSCE = 0 KSATIV = 1.592
KT1 = 0.08387 KT1L = 0
LINT = -2.5e-9 LPE0 = 0 LCDSCD = 0 LCDSCDR = 0
LRDSW = 1.3 LVSAT = 1441
MEXP = 2.491 NBODY = 1e22 NC0SUB = 2.86e25 NI0SUB = 1.1e16 NSD = 2e26
PCLM = 0.01 PCLMCV = 0.013 PCLMG = 1
PDIBL1 = 800 PDIBL2 = 0.005704
PHIN = 0.05 POXEDGE = 1.152 PQM = 0.66
PRT = 0.002477 PTWG = 6.322 PTWGT = 0.0015 PVAG = 200
QM0 = 2.183e-12 QMFACTOR = 0
RDSW = 190.6 RDSWMIN = 0 RDWMIN = 0 RSHD = 0 RSHS = 0 RSWMIN = 0
RTH0 = 0.15
TBGASUB = 4.73e-4 TBGBSUB = 636
TFIN = 1.4e-8 TGIDL = -0.01 TMEXP = 0
TNOM = 25
UA = 1.133 UA1 = 0.00134 UCS = 0.2672 UCSTE = 0
UD = 0.0105 UD1 = 0 UP = 0 UTE = 0 UTL = 0.001
VSAT = 48390 WR = 1 WTH0 = 2.6e-7 XL = 0"""
    tail = f"""\
PHIG = {phig:.4f}
EOT = {eot:.2e}
TOXP = {toxp:.2e}
EPSROX = {epsrox:.1f}
EPSRSP = {epsrox:.1f}
U0 = 0.02935"""

    return f".model {model_name} bsimcmg_va\n{make_model_lines(base_params)}\n{make_model_lines(tail)}\n"


def generate_snm_netlist(config, tid_krad, nmos_name, pmos_name, nmos_model, pmos_model,
                         vdd=0.9, mode="hold"):
    """Generate SNM butterfly curve netlist with literal values (no .param in .control)."""
    access_load = ""
    if mode == "read":
        access_load = f"""
* Access transistor loading (read mode)
NAL1 out1 vdd1 vdd1 0 {nmos_name}
NAL2 out2 vdd2 vdd2 0 {nmos_name}
"""

    out_vtc1 = str(OUTPUT_DIR / f"{config}_TID{tid_krad}_{mode}_vtc1.txt")
    out_vtc2 = str(OUTPUT_DIR / f"{config}_TID{tid_krad}_{mode}_vtc2.txt")

    return f"""* 6T SRAM SNM ({mode}) - {config} TID={tid_krad} krad

{nmos_model}
{pmos_model}

* === Inverter 1 ===
VIN1 in1 0 0
VDD1 vdd1 0 {vdd}

NPD1 out1 in1 0 0 {nmos_name}
NPU1 out1 in1 vdd1 vdd1 {pmos_name}
{access_load}
* === Inverter 2 ===
VIN2 in2 0 0
VDD2 vdd2 0 {vdd}

NPD2 out2 in2 0 0 {nmos_name}
NPU2 out2 in2 vdd2 vdd2 {pmos_name}

.control
set filetype=ascii

dc VIN1 0 {vdd} 0.002
let vtc1_vin = v(in1)
let vtc1_vout = v(out1)
write {out_vtc1} vtc1_vin vtc1_vout

reset
dc VIN2 0 {vdd} 0.002
let vtc2_vin = v(in2)
let vtc2_vout = v(out2)
write {out_vtc2} vtc2_vin vtc2_vout

quit
.endc
.end
"""


def generate_wm_netlist(config, tid_krad, nmos_name, pmos_name, nmos_model, pmos_model, vdd=0.9):
    """Generate Write Margin netlist using transient BL ramp.

    Write margin = minimum BL voltage needed to flip the cell.
    Method:
    1. Use .IC netlist card to force cell state Q=VDD, QB=0.
    2. Run tran command inside .control with UIC flag.
    3. BL ramps from VDD to 0 via PWL source over 20ns.
    4. Find the BL voltage when Q crosses VDD/2. WM = VDD - VBL_trip.
    This avoids DC convergence issues with bistable cross-coupled inverters.
    """
    out_write = str(OUTPUT_DIR / f"{config}_TID{tid_krad}_write.txt")
    ramp_time_ns = 20.0  # 20ns ramp from VDD to 0

    return f"""* 6T SRAM Write Margin - {config} TID={tid_krad} krad

{nmos_model}
{pmos_model}

* Supplies
VDD_S vdd_node 0 {vdd}

* Inverter 1: gate=QB, drain=Q
NPD1 q qb 0 0 {nmos_name}
NPU1 q qb vdd_node vdd_node {pmos_name}

* Inverter 2: gate=Q, drain=QB
NPD2 qb q 0 0 {nmos_name}
NPU2 qb q vdd_node vdd_node {pmos_name}

* Access transistors
NAX5 q wl bl 0 {nmos_name}
NAX6 qb wl blb 0 {nmos_name}

* WL = VDD (write enable)
VWL wl 0 {vdd}

* BLB = VDD (not pulling QB)
VBLB blb 0 {vdd}

* BL: PWL ramp from VDD to 0 over {ramp_time_ns:.0f}ns
VBL bl 0 PWL(0 {vdd} {ramp_time_ns:.0f}n 0)

* Initial conditions: force cell to Q=VDD, QB=0
.IC V(q)={vdd} V(qb)=0

.control
set filetype=ascii

* Run transient with UIC (use initial conditions)
tran 0.01n {ramp_time_ns:.0f}n uic

let vq = v(q)
let vqb = v(qb)
let vbl = v(bl)

write {out_write} vbl vq vqb

quit
.endc
.end
"""


def run_ngspice(netlist_path, log_path):
    """Run ngspice in batch mode."""
    result = subprocess.run(
        ["ngspice", "-b", str(netlist_path)],
        capture_output=True, text=True,
        cwd=str(netlist_path.parent),
        timeout=300
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(result.stdout + "\n--- STDERR ---\n" + result.stderr)
    return result.returncode == 0, result.stdout, result.stderr


def parse_ngspice_raw(filepath):
    """Parse ngspice ascii write output. Returns (col1, col2) from the data section.

    ngspice 'set filetype=ascii' format:
    - Header lines: Title, Date, Command, Plotname, Flags, No. Variables, No. Points, Variables, Values
    - Data: index on one line, then indented values (one per variable)
    We want columns 1 and 2 (skip column 0 = v-sweep index, use col1=vin, col2=vout).
    """
    try:
        col1, col2 = [], []
        with open(filepath) as f:
            lines = f.readlines()

        # Find "Values:" marker
        in_data = False
        data_buffer = []
        for line in lines:
            s = line.strip()
            if s.startswith("Values:"):
                in_data = True
                continue
            if in_data:
                if s:
                    data_buffer.append(s)

        # Parse data: pairs of lines (index, then values)
        i = 0
        while i < len(data_buffer):
            # First line: index
            idx_line = data_buffer[i].split()
            if len(idx_line) < 1:
                i += 1
                continue
            try:
                int(idx_line[0])  # Verify it's an index
            except ValueError:
                i += 1
                continue

            # Next lines: value lines (one per variable)
            vals = []
            j = i + 1
            while j < len(data_buffer) and len(vals) < 3:
                parts = data_buffer[j].split()
                if parts:
                    try:
                        vals.append(float(parts[0]))
                    except ValueError:
                        break
                j += 1

            if len(vals) >= 2:
                col1.append(vals[0])
                col2.append(vals[1])

            i = j

        if not col1:
            return None, None
        return np.array(col1), np.array(col2)
    except Exception:
        return None, None


def extract_snm(vtc1_file, vtc2_file, vdd=0.9):
    """Extract SNM using the VTC-based method.

    For high-gain CNTFET inverters, the butterfly curve method gives
    a very narrow eye due to the steep transition. We use the
    VIH/VIL noise margin method instead:
      NMH = VOH - VIH  (noise margin high)
      NML = VIL - VOL  (noise margin low)
      SNM = min(NMH, NML)
    where VIH/VIL are the input voltages where |gain| = 1.
    """
    vin, vout = parse_ngspice_raw(vtc1_file)
    if vin is None:
        return None

    # Compute gain (dvout/dvin)
    gain = np.gradient(vout, vin)

    # Find VIL: first point where |gain| >= 1 from the left
    vil = None
    vih = None
    for i in range(1, len(gain)):
        if abs(gain[i-1]) < 1.0 and abs(gain[i]) >= 1.0 and gain[i] < 0:
            if vil is None:
                vil = vin[i]
            vih = vin[i]

    # If we didn't find clear VIL/VIH, use trip point method
    if vil is None or vih is None:
        # Find trip point (VTC crosses diagonal)
        for i in range(1, len(vin)):
            if (vout[i-1] - vin[i-1]) > 0 and (vout[i] - vin[i]) <= 0:
                d_prev = vout[i-1] - vin[i-1]
                d_curr = vout[i] - vin[i]
                denom = d_prev - d_curr
                frac = d_prev / denom if abs(denom) > 1e-15 else 0.5
                vtrip = vin[i-1] + frac * (vin[i] - vin[i-1])
                nmh = vdd - vtrip
                nml = vtrip
                return max(0, min(nmh, nml) * 1000)

    # VOH = VDD (ideal), VOL = 0 (ideal) for steep inverters
    # More precise: VOH at vin=0, VOL at vin=VDD
    voh = vout[0]
    vol = vout[-1]

    nmh = voh - vih if vih is not None else vdd / 2
    nml = vil - vol if vil is not None else vdd / 2
    snm = min(nmh, nml)

    return max(0, snm * 1000)  # mV


def extract_write_margin(write_file, vdd=0.9):
    """Extract write margin from BL sweep data.

    The output file has (vbl, vq, vqb). Write margin = VDD - VBL_trip
    where VBL_trip is the BL voltage where Q flips from VDD to below VDD/2.
    """
    try:
        data = []
        with open(write_file) as f:
            in_data = False
            buf = []
            for line in f:
                s = line.strip()
                if s.startswith("Values:"):
                    in_data = True
                    continue
                if in_data and s:
                    buf.append(s)

        vbl, vq, vqb = [], [], []
        i = 0
        while i < len(buf):
            parts = buf[i].split()
            if not parts:
                i += 1
                continue
            try:
                int(parts[0])
            except ValueError:
                i += 1
                continue
            vals = []
            j = i + 1
            while j < len(buf) and len(vals) < 3:
                p = buf[j].split()
                if p:
                    try:
                        vals.append(float(p[0]))
                    except ValueError:
                        break
                j += 1
            if len(vals) >= 3:
                vbl.append(vals[0])
                vq.append(vals[1])
                vqb.append(vals[2])
            i = j

        if not vbl:
            return None

        vbl = np.array(vbl)
        vq = np.array(vq)
        vqb = np.array(vqb)

        # Find where Q drops through VDD/2 as BL decreases
        vdd_half = vdd / 2.0
        for i in range(1, len(vq)):
            if vq[i-1] > vdd_half and vq[i] <= vdd_half:
                denom = vq[i-1] - vq[i]
                frac = (vq[i-1] - vdd_half) / denom if abs(denom) > 1e-15 else 0
                vbl_trip = vbl[i-1] + frac * (vbl[i] - vbl[i-1])
                wm = (vdd - vbl_trip) * 1000  # mV
                return max(0, float(wm))

        # Cell never flipped -> write failure (WM = 0)
        # This means the access transistor cannot overcome the cross-coupled feedback
        return 0.0
    except Exception:
        return None


def generate_plots(metrics):
    """Generate SNM and Write Margin vs TID plots."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print("  [PLOT] matplotlib not available")
        return

    COLORS = ['#081D33', '#1B425E', '#2E6689', '#4E94A0', '#6EC1B1', '#8CD5AB', '#ABEAA4', '#C5F2B0']
    cfg_color = {"configA": COLORS[0], "configB": COLORS[3], "configC": COLORS[5]}
    cfg_marker = {"configA": "o", "configB": "s", "configC": "^"}
    cfg_label = {
        "configA": r"SiO$_2$ 10nm",
        "configB": r"HfO$_2$ 8nm",
        "configC": r"Al$_2$O$_3$/HfO$_2$ bilayer",
    }

    for metric_key, ylabel, title, fname in [
        ("snm_hold_mV", r"SNM$_{hold}$ (mV)", "Static Noise Margin (Hold) vs TID", "snm_vs_tid.png"),
        ("snm_read_mV", r"SNM$_{read}$ (mV)", "Static Noise Margin (Read) vs TID", "snm_read_vs_tid.png"),
        ("write_margin_mV", "Write Margin (mV)", "Write Margin vs TID", "write_margin_vs_tid.png"),
    ]:
        fig, ax = plt.subplots(1, 1, figsize=(8, 6))
        has_data = False
        for config in CONFIGS:
            if config not in metrics.get("configs", {}):
                continue
            tids, vals = [], []
            for entry in metrics["configs"][config]["tid_sweep"]:
                v = entry.get(metric_key)
                if v is not None:
                    tids.append(entry["tid_krad"])
                    vals.append(v)
            if tids:
                has_data = True
                ax.plot(tids, vals, marker=cfg_marker[config], color=cfg_color[config],
                        label=cfg_label[config], linewidth=2, markersize=8)
        if not has_data:
            plt.close()
            continue

        ax.set_xlabel("TID (krad)", fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.set_title(title, fontsize=13)
        ax.legend(fontsize=10)
        ax.set_xscale('log')
        ax.set_xlim(50, 15000)
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.savefig(DATA_OUTPUT / fname, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Plot: {DATA_OUTPUT / fname}")


def main():
    print("=" * 70)
    print("  6T SRAM TID Radiation Degradation - ngspice BSIM-CMG")
    print("=" * 70)

    # ── Load TCAD data ──
    print("\n[1/5] Loading TCAD metrics data...")
    with open(TCAD_DATA) as f:
        tcad_data = json.load(f)
    for config in CONFIGS:
        n = len(tcad_data.get(config, {}))
        print(f"  {config}: {n} TID levels")

    # ── Generate netlists ──
    print("\n[2/5] Generating netlists...")
    sim_jobs = []

    for config in CONFIGS:
        config_data = tcad_data[config]
        dp = DIELECTRIC_PARAMS[config]

        # PMOS baseline: use TID=0 for all configs (corrected extraction)
        baseline = config_data["0"]

        # PMOS uses baseline (TID-insensitive)
        # configA uses 0.15V delta; configB/C need 0.43V for balanced write margin
        pmos_delta = {"configA": 0.15, "configB": 0.43, "configC": 0.43}[config]
        pmos_phig = baseline["vth_V"] + pmos_delta + PHIG_OFFSET[config]
        pmos_name = f"pmos_{config}"
        pmos_model = build_pmos_model(pmos_name, pmos_phig, dp["eot"], dp["toxp"], dp["epsrox"])

        for tid_krad in TID_LEVELS:
            tid_key = str(tid_krad)
            if tid_key not in config_data:
                continue
            td = config_data[tid_key]

            nmos_phig = td["vth_V"] + PHIG_OFFSET[config]
            nmos_name = f"nmos_{config}_tid{tid_krad}"

            # U0: scale gently with Ion degradation
            ion_ref = 1.9e-7
            u0 = 0.025 * (td["ion_per_device_A"] / ion_ref) ** 0.3
            u0 = max(0.015, min(0.050, u0))

            nmos_model = build_nmos_model(nmos_name, nmos_phig, u0, dp["eot"], dp["toxp"], dp["epsrox"])

            # SNM hold, SNM read, Write Margin
            for mode in ["hold", "read"]:
                netlist = generate_snm_netlist(config, tid_krad, nmos_name, pmos_name,
                                                nmos_model, pmos_model, VDD, mode)
                fpath = SRC_DIR / f"sram_{config}_tid{tid_krad}_snm_{mode}.cir"
                fpath.write_text(netlist)
                sim_jobs.append({"config": config, "tid_krad": tid_krad,
                                 "mode": f"snm_{mode}", "netlist": fpath})

            wm_netlist = generate_wm_netlist(config, tid_krad, nmos_name, pmos_name,
                                              nmos_model, pmos_model, VDD)
            wm_path = SRC_DIR / f"sram_{config}_tid{tid_krad}_write.cir"
            wm_path.write_text(wm_netlist)
            sim_jobs.append({"config": config, "tid_krad": tid_krad,
                             "mode": "write_margin", "netlist": wm_path})

    print(f"  {len(sim_jobs)} netlists ({len(sim_jobs)//3} combos x 3 modes)")

    # ── Test-first ──
    print("\n[3/5] Test-first: configA TID=0 SNM hold...")
    test_job = next(j for j in sim_jobs
                    if j["config"] == "configA" and j["tid_krad"] == 0 and j["mode"] == "snm_hold")
    ok, stdout, stderr = run_ngspice(test_job["netlist"], LOGS_DIR / "test_first.log")

    if not ok:
        print("  TEST FAILED!")
        for line in stderr.splitlines()[-15:]:
            print(f"    {line}")
        # Show generated netlist for debugging
        print(f"\n  Netlist ({test_job['netlist']}):")
        with open(test_job["netlist"]) as f:
            for i, line in enumerate(f.readlines()[:15], 1):
                print(f"    {i:3d}: {line.rstrip()}")
        sys.exit(1)

    vtc1 = OUTPUT_DIR / "configA_TID0_hold_vtc1.txt"
    vtc2 = OUTPUT_DIR / "configA_TID0_hold_vtc2.txt"
    if not vtc1.exists() or not vtc2.exists():
        print(f"  TEST: Output missing! vtc1={vtc1.exists()} vtc2={vtc2.exists()}")
        sys.exit(1)

    snm_test = extract_snm(vtc1, vtc2, VDD)
    print(f"  TEST PASSED! SNM_hold(configA, TID=0) = {snm_test:.1f} mV")

    # ── Run all (parallel via subprocess.Popen) ──
    print(f"\n[4/5] Running {len(sim_jobs)} simulations...")

    # Launch all ngspice processes in parallel
    procs = {}
    for i, job in enumerate(sim_jobs):
        log_path = LOGS_DIR / f"{job['config']}_TID{job['tid_krad']}_{job['mode']}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.Popen(
            ["ngspice", "-b", str(job["netlist"])],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=str(job["netlist"].parent),
        )
        procs[i] = (proc, job, log_path)

    # Wait for all to complete
    done = 0
    total = len(procs)
    for i, (proc, job, log_path) in procs.items():
        stdout, stderr = proc.communicate(timeout=300)
        done += 1
        ok = proc.returncode == 0
        log_path.write_text(stdout.decode(errors='replace') + "\n--- STDERR ---\n" + stderr.decode(errors='replace'))
        tag = f"{job['config']} TID={job['tid_krad']} {job['mode']}"
        print(f"  [{done}/{total}] {tag}: {'OK' if ok else 'FAIL'}")

    # ── Extract metrics ──
    print("\n[5/5] Extracting SNM and Write Margin...")

    metrics = {
        "extraction_method": "programmatic (ngspice BSIM-CMG butterfly curve)",
        "interface_version": "1.0",
        "tool": "ngspice",
        "model": "BSIM-CMG 111 via OSDI",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "vdd": VDD,
        "cell_type": "6T SRAM",
        "phig_offset": PHIG_OFFSET[config],
        "configs": {},
    }

    for config in CONFIGS:
        metrics["configs"][config] = {
            "config_label": DIELECTRIC_PARAMS[config]["label"],
            "tid_sweep": [],
        }
        for tid_krad in TID_LEVELS:
            entry = {"tid_krad": tid_krad}

            # SNM hold
            v1h = OUTPUT_DIR / f"{config}_TID{tid_krad}_hold_vtc1.txt"
            v2h = OUTPUT_DIR / f"{config}_TID{tid_krad}_hold_vtc2.txt"
            entry["snm_hold_mV"] = extract_snm(v1h, v2h, VDD) if v1h.exists() and v2h.exists() else None

            # SNM read
            v1r = OUTPUT_DIR / f"{config}_TID{tid_krad}_read_vtc1.txt"
            v2r = OUTPUT_DIR / f"{config}_TID{tid_krad}_read_vtc2.txt"
            entry["snm_read_mV"] = extract_snm(v1r, v2r, VDD) if v1r.exists() and v2r.exists() else None

            # Write Margin
            wf = OUTPUT_DIR / f"{config}_TID{tid_krad}_write.txt"
            entry["write_margin_mV"] = extract_write_margin(wf, VDD) if wf.exists() else None

            # Ensure JSON-serializable types
            for k in ("snm_hold_mV", "snm_read_mV", "write_margin_mV"):
                v = entry[k]
                if v is not None:
                    entry[k] = float(v)

            metrics["configs"][config]["tid_sweep"].append(entry)

            sh = entry["snm_hold_mV"]
            sr = entry["snm_read_mV"]
            wm = entry["write_margin_mV"]
            sh_s = f"{sh:.1f}" if sh is not None else "N/A"
            sr_s = f"{sr:.1f}" if sr is not None else "N/A"
            wm_s = f"{wm:.1f}" if wm is not None else "N/A"
            print(f"  {config} TID={tid_krad:>5}: SNM_h={sh_s:>7} SNM_r={sr_s:>7} WM={wm_s:>7} mV")

    # ── Save ──
    DATA_OUTPUT.mkdir(parents=True, exist_ok=True)

    with open(DATA_OUTPUT / "metrics.json", 'w') as f:
        json.dump(metrics, f, indent=2)

    interface = {
        "extraction_method": "programmatic (ngspice BSIM-CMG 6T SRAM)",
        "interface_version": "1.0",
        "tool": "ngspice",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cell_type": "6T SRAM",
        "model": "BSIM-CMG 111 via OSDI",
        "vdd": VDD,
        "device_configs": [],
    }
    for config in CONFIGS:
        cm = metrics["configs"][config]
        ce = {"config_name": config, "config_label": cm["config_label"], "tid_sweep": []}
        for e in cm["tid_sweep"]:
            ce["tid_sweep"].append({
                "tid_krad": e["tid_krad"],
                "snm_hold_mV": e.get("snm_hold_mV"),
                "snm_read_mV": e.get("snm_read_mV"),
                "write_margin_mV": e.get("write_margin_mV"),
                "snm_degraded": e.get("snm_hold_mV") is not None and e.get("snm_hold_mV", 9999) < 50,
                "write_failure": e.get("write_margin_mV") is not None and e.get("write_margin_mV", 9999) < 10,
            })
        interface["device_configs"].append(ce)

    with open(DATA_OUTPUT / "interface.json", 'w') as f:
        json.dump(interface, f, indent=2)

    generate_plots(metrics)

    print(f"\n{'='*70}")
    print("  Done!")
    for p in sorted(DATA_OUTPUT.glob("*")):
        print(f"    {p}")
    print(f"{'='*70}")

    return metrics


if __name__ == "__main__":
    main()
