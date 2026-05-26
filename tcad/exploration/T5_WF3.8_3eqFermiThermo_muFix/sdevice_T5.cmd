File {
    Grid    = "input/structure_msh.tdr"
    Parameter = "input/sdevice_T5.par"
    Plot    = "output/sdevice_T5_plt.tdr"
    Current = "output/sdevice_T5_IdVg.plt"
    Output  = "output/sdevice_T5_log.log"
}

Electrode {
    * WF=3.8: moderate barriers
    { Name="source"    Voltage=0.0  Schottky Workfunction=3.8 }
    { Name="drain"     Voltage=0.0  Schottky Workfunction=3.8 }
    { Name="gate"      Voltage=0.0  Workfunction=4.65 }
    { Name="substrate" Voltage=0.0 }
}

Thermode {
    * Required for Thermodynamic model
    { Name="source"    Temperature=300 SurfaceResistance=1e-3 }
    { Name="drain"     Temperature=300 SurfaceResistance=1e-3 }
    { Name="gate"      Temperature=300 SurfaceResistance=1e-3 }
    { Name="substrate" Temperature=300 }
}

Physics {
    AreaFactor=1e6
    Fermi
    Thermodynamic             * Adds lattice heat equation
    Thermionic
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
    Temperature
    TotalRecombination
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
    Poisson
    Coupled { Poisson Electron }

    NewCurrentPrefix="ramp_vds_"
    Quasistationary (
        InitialStep=1e-3 MaxStep=0.05 MinStep=1e-7
        Goal { Name="drain" Voltage=0.05 }
    ) { Coupled { Poisson Electron } }

    Coupled { Poisson Electron Hole }

    NewCurrentPrefix="IdVg_"
    Quasistationary (
        InitialStep=1e-3 MaxStep=0.02 MinStep=1e-8
        Goal { Name="gate" Voltage=1.0 }
    ) { Coupled { Poisson Electron Hole Temperature } }
}
