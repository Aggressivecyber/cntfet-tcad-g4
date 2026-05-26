#!/usr/bin/env python3
"""
Generate SDEVICE workspace for 3 dielectric configs x 6 TID points = 18 runs.

Config A: SiO2 single layer (10nm)
Config B: HfO2 single layer (8nm)
Config C: Al2O3/HfO2 bilayer (2nm/6nm)
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

PROJECT = "/home/rylan/projects/sim-lab/20260427-034614-CNTFET-6T-SRAM-TID-Radiation-Multi-Scale-Simulatio"
DOCKER_PROJECT = "/root/projects/sim-lab/20260427-034614-CNTFET-6T-SRAM-TID-Radiation-Multi-Scale-Simulatio"
TCAD_SRC = f"{PROJECT}/data/simulation/tcad/src"
TCAD_OUTPUT = f"{PROJECT}/data/simulation/tcad/output"
DATEX_SRC = f"{PROJECT}/workspace/tcad/baseline/20260427-065553-cntfet-quasi-gaa-tid-radiation/datexcodes.txt"

# TID trap parameters table
TID_PARAMS = {
    0:     {"Nbt_SiO2": "5.0e17",  "Nbt_HfO2": "1.0e18",  "Nbt_Al2O3": "2.0e17",  "Nit_fc": "1.0e11",  "Nit_d": "5.0e10",  "Nit_a": "5.0e10"},
    100:   {"Nbt_SiO2": "6.0e17",  "Nbt_HfO2": "1.5e18",  "Nbt_Al2O3": "2.5e17",  "Nit_fc": "1.1e11",  "Nit_d": "5.5e10",  "Nit_a": "5.5e10"},
    500:   {"Nbt_SiO2": "5.5e17",  "Nbt_HfO2": "2.5e18",  "Nbt_Al2O3": "2.5e17",  "Nit_fc": "1.5e11",  "Nit_d": "7.5e10",  "Nit_a": "7.5e10"},
    1000:  {"Nbt_SiO2": "6.0e17",  "Nbt_HfO2": "3.0e18",  "Nbt_Al2O3": "2.5e17",  "Nit_fc": "2.0e11",  "Nit_d": "1.0e11",  "Nit_a": "1.0e11"},
    5000:  {"Nbt_SiO2": "1.0e18",  "Nbt_HfO2": "3.5e18",  "Nbt_Al2O3": "2.5e17",  "Nit_fc": "6.0e11",  "Nit_d": "3.0e11",  "Nit_a": "3.0e11"},
    10000: {"Nbt_SiO2": "1.5e18",  "Nbt_HfO2": "4.0e18",  "Nbt_Al2O3": "2.5e17",  "Nit_fc": "1.1e12",  "Nit_d": "5.5e11",  "Nit_a": "5.5e11"},
}

STRUCTURE_MAP = {
    "A": f"{DOCKER_PROJECT}/data/simulation/tcad/output/structure_configA_SiO2.tdr",
    "B": f"{DOCKER_PROJECT}/data/simulation/tcad/output/structure_configB_HfO2.tdr",
    "C": f"{DOCKER_PROJECT}/data/simulation/tcad/output/structure_configC_bilayer.tdr",
}


def gen_par_configA():
    """Config A par file: SiO2 single layer."""
    return """* Config A: SiO2 single layer dielectric (10nm)
* eps_r=3.9, Eg=9.0eV, Chi=0.9eV

Material = "CNT_thin_film" {

Epsilon
{
    epsilon = 5.0
}

Bandgap
{
    Chi0    = 4.0
    Bgn2Chi = 0.5
    Eg0     = 0.50
    alpha   = 0.0
    beta    = 0.0
    alpha2  = 0.0
    beta2   = 0.0
    EgMin   = 0.0
    dEgMin  = 0.01
    Tpar    = 300.0
}

eDOSMass
{
    Formula = 2
    Nc300   = 1.506e17
}

hDOSMass
{
    Formula = 2
    Nv300   = 1.506e17
}

ConstantMobility:
{
    mumax   = 1000.0 ,  1000.0
    Exponent = 1.5   ,  1.5
    mutunnel = 0.05  ,  0.05
}

HighFieldDependence:
{
    beta0   = 2  ,  2
    betaexp = 0.0 , 0.0
    alpha   = 0.0 , 0.0
    Vsat_Formula = 2 , 2
    A_vsat  = 1.0e7 , 8.0e6
    B_vsat  = 0.0   , 0.0
    vsat_min = 1.0e5 , 1.0e5
}

Scharfetter
{
    taumin  = 1.0e-12 , 1.0e-12
    taumax  = 1.0e-9  , 1.0e-9
    Nref    = 1.0e16  , 1.0e16
    gamma   = 1       , 1
    Talpha  = -1.5    , -1.5
    Etrap   = 0.0
}

}

Material = "SiO2" {

Epsilon
{
    epsilon = 3.9
}

Bandgap
{
    Chi0 = 0.9
    Eg0  = 9.0
    alpha = 0.0
    beta  = 0.0
    Tpar  = 300.0
}

}
"""


def gen_par_configB():
    """Config B par file: HfO2 single layer."""
    return """* Config B: HfO2 single layer dielectric (8nm)
* eps_r=25.0, Eg=5.8eV, Chi=2.5eV

Material = "CNT_thin_film" {

Epsilon
{
    epsilon = 5.0
}

Bandgap
{
    Chi0    = 4.0
    Bgn2Chi = 0.5
    Eg0     = 0.50
    alpha   = 0.0
    beta    = 0.0
    alpha2  = 0.0
    beta2   = 0.0
    EgMin   = 0.0
    dEgMin  = 0.01
    Tpar    = 300.0
}

eDOSMass
{
    Formula = 2
    Nc300   = 1.506e17
}

hDOSMass
{
    Formula = 2
    Nv300   = 1.506e17
}

ConstantMobility:
{
    mumax   = 1000.0 ,  1000.0
    Exponent = 1.5   ,  1.5
    mutunnel = 0.05  ,  0.05
}

HighFieldDependence:
{
    beta0   = 2  ,  2
    betaexp = 0.0 , 0.0
    alpha   = 0.0 , 0.0
    Vsat_Formula = 2 , 2
    A_vsat  = 1.0e7 , 8.0e6
    B_vsat  = 0.0   , 0.0
    vsat_min = 1.0e5 , 1.0e5
}

Scharfetter
{
    taumin  = 1.0e-12 , 1.0e-12
    taumax  = 1.0e-9  , 1.0e-9
    Nref    = 1.0e16  , 1.0e16
    gamma   = 1       , 1
    Talpha  = -1.5    , -1.5
    Etrap   = 0.0
}

}

Material = "HfO2" {

Epsilon
{
    epsilon = 25.0
}

Bandgap
{
    Chi0 = 2.5
    Eg0  = 5.8
    alpha = 0.0
    beta  = 0.0
    Tpar  = 300.0
}

}
"""


def gen_par_configC():
    """Config C par file: Al2O3/HfO2 bilayer."""
    return """* Config C: Al2O3/HfO2 bilayer dielectric (2nm/6nm)
* Al2O3: eps=9.0, Eg=8.8eV, Chi=1.4eV
* HfO2: eps=25.0, Eg=5.8eV, Chi=2.5eV

Material = "CNT_thin_film" {

Epsilon
{
    epsilon = 5.0
}

Bandgap
{
    Chi0    = 4.0
    Bgn2Chi = 0.5
    Eg0     = 0.50
    alpha   = 0.0
    beta    = 0.0
    alpha2  = 0.0
    beta2   = 0.0
    EgMin   = 0.0
    dEgMin  = 0.01
    Tpar    = 300.0
}

eDOSMass
{
    Formula = 2
    Nc300   = 1.506e17
}

hDOSMass
{
    Formula = 2
    Nv300   = 1.506e17
}

ConstantMobility:
{
    mumax   = 1000.0 ,  1000.0
    Exponent = 1.5   ,  1.5
    mutunnel = 0.05  ,  0.05
}

HighFieldDependence:
{
    beta0   = 2  ,  2
    betaexp = 0.0 , 0.0
    alpha   = 0.0 , 0.0
    Vsat_Formula = 2 , 2
    A_vsat  = 1.0e7 , 8.0e6
    B_vsat  = 0.0   , 0.0
    vsat_min = 1.0e5 , 1.0e5
}

Scharfetter
{
    taumin  = 1.0e-12 , 1.0e-12
    taumax  = 1.0e-9  , 1.0e-9
    Nref    = 1.0e16  , 1.0e16
    gamma   = 1       , 1
    Talpha  = -1.5    , -1.5
    Etrap   = 0.0
}

}

Material = "Al2O3" {

Epsilon
{
    epsilon = 9.0
}

Bandgap
{
    Chi0 = 1.4
    Eg0  = 8.8
    alpha = 0.0
    beta  = 0.0
    Tpar  = 300.0
}

}

Material = "HfO2" {

Epsilon
{
    epsilon = 25.0
}

Bandgap
{
    Chi0 = 2.5
    Eg0  = 5.8
    alpha = 0.0
    beta  = 0.0
    Tpar  = 300.0
}

}
"""


def gen_cmd_tid0(config, params):
    """Generate SDEVICE cmd file for TID=0 (no Load, solve from scratch)."""
    if config == "A":
        trap_section = f"""
* TID=0 krad: SiO2 gate dielectric bulk trapped charge (Region-specific to avoid substrate)
Physics (Region="R.GateSiO2") {{
    Traps ((FixedCharge SpatialShape=Uniform Conc={params['Nbt_SiO2']}))
}}

* Interface trapped charge: Donor + Acceptor states
Physics (MaterialInterface="CNT_thin_film/SiO2") {{
    Traps (
        (FixedCharge SpatialShape=Uniform Conc={params['Nit_fc']})
        (Donor Conc={params['Nit_d']} EnergyMid=0.0 EnergySig=0.1
            eXsection=1e-15 hXsection=1e-15 fromMidBandGap)
        (Acceptor Conc={params['Nit_a']} EnergyMid=0.0 EnergySig=0.1
            eXsection=1e-15 hXsection=1e-15 fromMidBandGap)
    )
}}
"""
    elif config == "B":
        trap_section = f"""
* TID=0 krad: HfO2 bulk trapped charge
Physics (Material="HfO2") {{
    Traps ((FixedCharge SpatialShape=Uniform Conc={params['Nbt_HfO2']}))
}}

* Interface trapped charge: Donor + Acceptor states
Physics (MaterialInterface="CNT_thin_film/HfO2") {{
    Traps (
        (FixedCharge SpatialShape=Uniform Conc={params['Nit_fc']})
        (Donor Conc={params['Nit_d']} EnergyMid=0.0 EnergySig=0.1
            eXsection=1e-15 hXsection=1e-15 fromMidBandGap)
        (Acceptor Conc={params['Nit_a']} EnergyMid=0.0 EnergySig=0.1
            eXsection=1e-15 hXsection=1e-15 fromMidBandGap)
    )
}}
"""
    else:  # Config C
        trap_section = f"""
* TID=0 krad: Bilayer oxide trapped charge
Physics (Material="Al2O3") {{
    Traps ((FixedCharge SpatialShape=Uniform Conc={params['Nbt_Al2O3']}))
}}
Physics (Material="HfO2") {{
    Traps ((FixedCharge SpatialShape=Uniform Conc={params['Nbt_HfO2']}))
}}

* CNT/Al2O3 interface: Donor + Acceptor states
Physics (MaterialInterface="CNT_thin_film/Al2O3") {{
    Traps (
        (FixedCharge SpatialShape=Uniform Conc={params['Nit_fc']})
        (Donor Conc={params['Nit_d']} EnergyMid=0.0 EnergySig=0.1
            eXsection=1e-15 hXsection=1e-15 fromMidBandGap)
        (Acceptor Conc={params['Nit_a']} EnergyMid=0.0 EnergySig=0.1
            eXsection=1e-15 hXsection=1e-15 fromMidBandGap)
    )
}}

* CNT/HfO2 interface: Donor + Acceptor states
Physics (MaterialInterface="CNT_thin_film/HfO2") {{
    Traps (
        (FixedCharge SpatialShape=Uniform Conc={params['Nit_fc']})
        (Donor Conc={params['Nit_d']} EnergyMid=0.0 EnergySig=0.1
            eXsection=1e-15 hXsection=1e-15 fromMidBandGap)
        (Acceptor Conc={params['Nit_a']} EnergyMid=0.0 EnergySig=0.1
            eXsection=1e-15 hXsection=1e-15 fromMidBandGap)
    )
}}
"""

    return f"""File {{
    Grid    = "input/structure_msh.tdr"
    Parameter = "input/sdevice.par"
    Plot    = "output/sdevice_plt.tdr"
    Current = "output/sdevice_IdVg.plt"
    Output  = "output/sdevice_log.log"
}}

Electrode {{
    {{ Name="source"    Voltage=0.0  Schottky Workfunction=4.0 }}
    {{ Name="drain"     Voltage=0.0  Schottky Workfunction=4.0 }}
    {{ Name="gate"      Voltage=0.0  Workfunction=4.65 }}
    {{ Name="substrate" Voltage=0.0 }}
}}

Physics {{
    AreaFactor=1e6
    Fermi
    Thermionic
    Mobility ( ConstantMobility HighFieldSaturation )
    Recombination ( SRH )
    EffectiveIntrinsicDensity ( NoBandGapNarrowing )
}}
{trap_section}
Plot {{
    eDensity hDensity Potential SpaceCharge
    eCurrent/Vector hCurrent/Vector
    eMobility hMobility ElectricField/Vector
    eQuasiFermi hQuasiFermi
    ConductionBandEnergy ValenceBandEnergy
}}

Math {{
    Extrapolate
    Method = Blocked
    SubMethod = ParDiSo
    NotDamped=200
    Iterations=200
    Digits=3
    RecBoxIntegr
    RHSmin=1e-12
    Number_of_threads=4
    CNormPrint
    Traps(Damping=100)
}}

Solve {{
    Poisson
    Coupled (Iterations=200) {{ Poisson Electron }}

    * Ramp Vds
    NewCurrentPrefix="ramp_vds_"
    Quasistationary (
        InitialStep=1e-3 MaxStep=0.05 MinStep=1e-8
        Increment=2 Decrement=2
        Goal {{ Name="drain" Voltage=0.05 }}
    ) {{ Coupled {{ Poisson Electron }} }}

    Coupled (Iterations=200) {{ Poisson Electron Hole }}

    * IdVg sweep
    NewCurrentPrefix="IdVg_"
    Quasistationary (
        InitialStep=1e-3 MaxStep=0.05 MinStep=1e-12
        Increment=2 Decrement=2
        Goal {{ Name="gate" Voltage=1.0 }}
    ) {{ Coupled {{ Poisson Electron Hole }} }}
}}
"""


def gen_cmd_tid_high(config, params, tid):
    """Generate SDEVICE cmd file for TID>0 (loads baseline solution)."""
    if config == "A":
        trap_section = f"""
* TID={tid} krad: SiO2 gate dielectric bulk trapped charge (Region-specific to avoid substrate)
Physics (Region="R.GateSiO2") {{
    Traps ((FixedCharge SpatialShape=Uniform Conc={params['Nbt_SiO2']}))
}}

* Interface trapped charge: Donor + Acceptor states
Physics (MaterialInterface="CNT_thin_film/SiO2") {{
    Traps (
        (FixedCharge SpatialShape=Uniform Conc={params['Nit_fc']})
        (Donor Conc={params['Nit_d']} EnergyMid=0.0 EnergySig=0.1
            eXsection=1e-15 hXsection=1e-15 fromMidBandGap)
        (Acceptor Conc={params['Nit_a']} EnergyMid=0.0 EnergySig=0.1
            eXsection=1e-15 hXsection=1e-15 fromMidBandGap)
    )
}}
"""
    elif config == "B":
        trap_section = f"""
* TID={tid} krad: HfO2 bulk trapped charge
Physics (Material="HfO2") {{
    Traps ((FixedCharge SpatialShape=Uniform Conc={params['Nbt_HfO2']}))
}}

* Interface trapped charge: Donor + Acceptor states
Physics (MaterialInterface="CNT_thin_film/HfO2") {{
    Traps (
        (FixedCharge SpatialShape=Uniform Conc={params['Nit_fc']})
        (Donor Conc={params['Nit_d']} EnergyMid=0.0 EnergySig=0.1
            eXsection=1e-15 hXsection=1e-15 fromMidBandGap)
        (Acceptor Conc={params['Nit_a']} EnergyMid=0.0 EnergySig=0.1
            eXsection=1e-15 hXsection=1e-15 fromMidBandGap)
    )
}}
"""
    else:  # Config C
        trap_section = f"""
* TID={tid} krad: Bilayer oxide trapped charge
Physics (Material="Al2O3") {{
    Traps ((FixedCharge SpatialShape=Uniform Conc={params['Nbt_Al2O3']}))
}}
Physics (Material="HfO2") {{
    Traps ((FixedCharge SpatialShape=Uniform Conc={params['Nbt_HfO2']}))
}}

* CNT/Al2O3 interface: Donor + Acceptor states
Physics (MaterialInterface="CNT_thin_film/Al2O3") {{
    Traps (
        (FixedCharge SpatialShape=Uniform Conc={params['Nit_fc']})
        (Donor Conc={params['Nit_d']} EnergyMid=0.0 EnergySig=0.1
            eXsection=1e-15 hXsection=1e-15 fromMidBandGap)
        (Acceptor Conc={params['Nit_a']} EnergyMid=0.0 EnergySig=0.1
            eXsection=1e-15 hXsection=1e-15 fromMidBandGap)
    )
}}

* CNT/HfO2 interface: Donor + Acceptor states
Physics (MaterialInterface="CNT_thin_film/HfO2") {{
    Traps (
        (FixedCharge SpatialShape=Uniform Conc={params['Nit_fc']})
        (Donor Conc={params['Nit_d']} EnergyMid=0.0 EnergySig=0.1
            eXsection=1e-15 hXsection=1e-15 fromMidBandGap)
        (Acceptor Conc={params['Nit_a']} EnergyMid=0.0 EnergySig=0.1
            eXsection=1e-15 hXsection=1e-15 fromMidBandGap)
    )
}}
"""

    return f"""File {{
    Grid    = "input/structure_msh.tdr"
    Parameter = "input/sdevice.par"
    Plot    = "output/sdevice_plt.tdr"
    Current = "output/sdevice_IdVg.plt"
    Output  = "output/sdevice_log.log"
}}

Electrode {{
    {{ Name="source"    Voltage=0.0  Schottky Workfunction=4.0 }}
    {{ Name="drain"     Voltage=0.0  Schottky Workfunction=4.0 }}
    {{ Name="gate"      Voltage=0.0  Workfunction=4.65 }}
    {{ Name="substrate" Voltage=0.0 }}
}}

Physics {{
    AreaFactor=1e6
    Fermi
    Thermionic
    Mobility ( ConstantMobility HighFieldSaturation )
    Recombination ( SRH )
    EffectiveIntrinsicDensity ( NoBandGapNarrowing )
}}
{trap_section}
Plot {{
    eDensity hDensity Potential SpaceCharge
    eCurrent/Vector hCurrent/Vector
    eMobility hMobility ElectricField/Vector
    eQuasiFermi hQuasiFermi
    ConductionBandEnergy ValenceBandEnergy
}}

Math {{
    Extrapolate
    Method = Blocked
    SubMethod = ParDiSo
    NotDamped=200
    Iterations=200
    Digits=3
    RecBoxIntegr
    RHSmin=1e-12
    Number_of_threads=4
    CNormPrint
    Traps(Damping=100)
}}

Solve {{
    * Load baseline TID=0 solution with non-zero carrier densities
    Load(FilePrefix="input/baseline_tid0")

    * Adapt electrostatic potential to new oxide trap charge
    Poisson
    Coupled (Iterations=200) {{ Poisson Electron }}

    * Switch to 3-eq with conservative damping
    Coupled (Iterations=200 LinesearchDamping=1e-3) {{ Poisson Electron Hole }}

    * Ramp Vds
    NewCurrentPrefix="ramp_vds_"
    Quasistationary (
        InitialStep=1e-3 MaxStep=0.05 MinStep=1e-10
        Increment=1.1 Decrement=3.0
        Goal {{ Name="drain" Voltage=0.05 }}
    ) {{ Coupled (Iterations=200) {{ Poisson Electron Hole }} }}

    * IdVg sweep
    NewCurrentPrefix="IdVg_"
    Quasistationary (
        InitialStep=5e-4 MaxStep=0.02 MinStep=1e-13
        Increment=1.1 Decrement=3.0
        Goal {{ Name="gate" Voltage=1.0 }}
    ) {{ Coupled (Iterations=200) {{ Poisson Electron Hole }} }}
}}
"""


def main():
    # Create workspace root
    run_id = "sdevice-3config-tid-ec2"
    ws_root = Path(f"{PROJECT}/workspace/tcad/production/{run_id}")
    ws_root.mkdir(parents=True, exist_ok=True)

    # Write par files
    par_generators = {
        "A": gen_par_configA,
        "B": gen_par_configB,
        "C": gen_par_configC,
    }

    config_names = {"A": "SiO2", "B": "HfO2", "C": "bilayer"}
    manifest = {
        "run_id": run_id,
        "configs": {},
        "total_runs": 18,
    }

    for config in ["A", "B", "C"]:
        config_dir = ws_root / f"config{config}"
        config_dir.mkdir(exist_ok=True)
        par_content = par_generators[config]()
        (config_dir / "sdevice.par").write_text(par_content)

        # Copy structure via Docker to avoid permission issues with root-owned files
        src = STRUCTURE_MAP[config]
        dst_docker = f"{DOCKER_PROJECT}/workspace/tcad/production/sdevice-3config-tid-ec2/config{config}/structure_msh.tdr"
        subprocess.run(["docker", "exec", "tcad-sentaurus", "cp", src, dst_docker], check=True, capture_output=True)

        manifest["configs"][config] = {
            "name": config_names[config],
            "structure": os.path.basename(STRUCTURE_MAP[config]),
            "tid_runs": [],
        }

        for tid in [0, 100, 500, 1000, 5000, 10000]:
            tid_dir = config_dir / f"TID_{tid}"
            tid_dir.mkdir(exist_ok=True)
            (tid_dir / "input").mkdir(exist_ok=True)
            (tid_dir / "output").mkdir(exist_ok=True)

            params = TID_PARAMS[tid]

            # Generate cmd file
            if tid == 0:
                cmd = gen_cmd_tid0(config, params)
            else:
                cmd = gen_cmd_tid_high(config, params, tid)

            (tid_dir / "input" / "sdevice.cmd").write_text(cmd)
            (tid_dir / "input" / "sdevice.par").write_text(par_content)

            # Copy structure via Docker to avoid permission issues
            src = STRUCTURE_MAP[config]
            dst_docker = f"{DOCKER_PROJECT}/workspace/tcad/production/sdevice-3config-tid-ec2/config{config}/TID_{tid}/input/structure_msh.tdr"
            subprocess.run(["docker", "exec", "tcad-sentaurus", "cp", src, dst_docker], check=True, capture_output=True)

            manifest["configs"][config]["tid_runs"].append({
                "tid_krad": tid,
                "workspace": str(tid_dir.relative_to(ws_root)),
                "needs_baseline": tid > 0,
            })

    # Write manifest
    (ws_root / "manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"Workspace created: {ws_root}")
    print(f"Total sub-workspaces: 18 (3 configs x 6 TID)")
    print(f"Config A (SiO2):  {ws_root}/configA/")
    print(f"Config B (HfO2):  {ws_root}/configB/")
    print(f"Config C (bilayer): {ws_root}/configC/")
    print()
    print("Next steps:")
    print("1. Run TID=0 for each config (generates baseline_tid0.tdr)")
    print("2. Run TID>0 for each config (loads baseline)")


if __name__ == "__main__":
    main()
