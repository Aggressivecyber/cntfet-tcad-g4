File {
    Grid    = "input/structure_msh.tdr"
    Parameter = "input/sdevice_T7.par"
    Plot    = "output/sdevice_T7_plt.tdr"
    Current = "output/sdevice_T7_IdVg.plt"
    Output  = "output/sdevice_T7_log.log"
}

Electrode {
    * Ohmic contacts - no Schottky specification
    * NOTE: This assumes SDE has doping in S/D extension regions.
    * If SDE has no doping, this will fail. May need to use
    * Charge=0 or ohmic with artificial doping.
    * Alternative: Use Schottky with very high WF to simulate ohmic.
    { Name="source"    Voltage=0.0 }
    { Name="drain"     Voltage=0.0 }
    { Name="gate"      Voltage=0.0  Workfunction=4.65 }
    { Name="substrate" Voltage=0.0 }
}

Physics {
    AreaFactor=1e6
    Fermi
    Mobility (
        ConstantMobility
        HighFieldSaturation
    )
    Recombination ( SRH )
    EffectiveIntrinsicDensity (
        NoBandGapNarrowing
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
    * Warm-up with 2-eq
    Poisson
    Coupled { Poisson Electron }

    * Ramp Vds
    NewCurrentPrefix="ramp_vds_"
    Quasistationary (
        InitialStep=1e-3 MaxStep=0.05 MinStep=1e-7
        Goal { Name="drain" Voltage=0.05 }
    ) { Coupled { Poisson Electron } }

    * Switch to 3-eq
    Coupled { Poisson Electron Hole }

    * IdVg sweep
    NewCurrentPrefix="IdVg_"
    Quasistationary (
        InitialStep=1e-3 MaxStep=0.02 MinStep=1e-8
        Goal { Name="gate" Voltage=1.0 }
    ) { Coupled { Poisson Electron Hole } }
}
