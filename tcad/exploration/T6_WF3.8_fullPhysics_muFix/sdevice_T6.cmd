File {
    Grid    = "input/structure_msh.tdr"
    Parameter = "input/sdevice_T6.par"
    Plot    = "output/sdevice_T6_plt.tdr"
    Current = "output/sdevice_T6_IdVg.plt"
    Output  = "output/sdevice_T6_log.log"
}

Electrode {
    * WF=3.8: moderate barriers for both carriers
    { Name="source"    Voltage=0.0  Schottky Workfunction=3.8 }
    { Name="drain"     Voltage=0.0  Schottky Workfunction=3.8 }
    { Name="gate"      Voltage=0.0  Workfunction=4.65 }
    { Name="substrate" Voltage=0.0 }
}

Thermode {
    { Name="source"    Temperature=300 SurfaceResistance=1e-3 }
    { Name="drain"     Temperature=300 SurfaceResistance=1e-3 }
    { Name="gate"      Temperature=300 SurfaceResistance=1e-3 }
    { Name="substrate" Temperature=300 }
}

Physics {
    AreaFactor=1e6
    Fermi
    Thermodynamic
    Thermionic

    eQuantumPotential (
        Equation (
            Type = "DensityGradient"
            nQuantumPotential
        )
    )

    Mobility (
        ConstantMobility
        HighFieldSaturation
    )

    Recombination (
        SRH
        Auger
    )

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
    eQuantumPotential
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
    ComputeGradQuasiFermiAtContacts = UseQuasiFermi
}

Solve {
    * Phase 1: DD warm-up without QP
    Poisson
    Coupled { Poisson Electron }

    NewCurrentPrefix="ramp_vds_"
    Quasistationary (
        InitialStep=1e-3 MaxStep=0.05 MinStep=1e-7
        Goal { Name="drain" Voltage=0.05 }
    ) { Coupled { Poisson Electron } }

    * Phase 2: Add Hole
    Coupled { Poisson Electron Hole }

    * Phase 3: IdVg sweep
    * If convergence fails with Temperature, remove it
    NewCurrentPrefix="IdVg_"
    Quasistationary (
        InitialStep=1e-3 MaxStep=0.01 MinStep=1e-9
        Goal { Name="gate" Voltage=1.0 }
    ) { Coupled { Poisson Electron Hole Temperature } }
}
