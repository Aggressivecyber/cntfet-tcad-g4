File {
    Grid    = "input/structure_msh.tdr"
    Parameter = "input/sdevice_T1.par"
    Plot    = "output/sdevice_T1_plt.tdr"
    Current = "output/sdevice_T1_IdVg.plt"
    Output  = "output/sdevice_T1_log.log"
}

Electrode {
    * FIX: WF raised from 3.5 to 4.0 eV
    * Phi_Bn = Chi - WF = 4.0 - 4.0 = 0.0 eV (ohmic for electrons)
    * Phi_Bp = Eg - Phi_Bn = 0.50 - 0.0 = 0.50 eV (blocking for holes)
    * This eliminates the ambipolar behavior seen in baseline
    { Name="source"    Voltage=0.0  Schottky Workfunction=4.0 }
    { Name="drain"     Voltage=0.0  Schottky Workfunction=4.0 }
    { Name="gate"      Voltage=0.0  Workfunction=4.65 }
    { Name="substrate" Voltage=0.0 }
}

Physics {
    AreaFactor=1e6
    Fermi                    * Fermi-Dirac statistics (mandatory for CNTFET)
    Thermionic               * Schottky contact thermionic emission
    Mobility (
        ConstantMobility
        HighFieldSaturation
    )
    Recombination ( SRH )
    EffectiveIntrinsicDensity (
        NoBandGapNarrowing    * CNT: no BGN model, disable default
    )
}

Plot {
    eDensity hDensity
    Potential SpaceCharge
    eCurrent/Vector hCurrent/Vector
    eMobility hMobility
    ElectricField/Vector
    eQuasiFermi hQuasiFermi
    ConductionBandEnergy ValenceBandEnergy
}

Math {
    Extrapolate
    Method = Blocked
    SubMethod = ParDiSo
    NotDamped=50
    Iterations=30
    Digits=4
    RecBoxIntegr
    RHSmin=1e-12
    Number_of_threads=4
    CNormPrint
}

Solve {
    * Step 1: Initial solve with 2-eq (Poisson + Electron) for warm-up
    Poisson
    Coupled { Poisson Electron }

    * Step 2: Ramp Vds to operating point
    NewCurrentPrefix="ramp_vds_"
    Quasistationary (
        InitialStep=1e-3 MaxStep=0.05 MinStep=1e-7
        Goal { Name="drain" Voltage=0.05 }
    ) { Coupled { Poisson Electron } }

    * Step 3: Switch to 3-eq (add Hole) and solve at Vds=0.05, Vg=0
    Coupled { Poisson Electron Hole }

    * Step 4: IdVg sweep with 3-eq + Fermi
    NewCurrentPrefix="IdVg_"
    Quasistationary (
        InitialStep=1e-3 MaxStep=0.02 MinStep=1e-8
        Goal { Name="gate" Voltage=1.0 }
    ) { Coupled { Poisson Electron Hole } }
}
