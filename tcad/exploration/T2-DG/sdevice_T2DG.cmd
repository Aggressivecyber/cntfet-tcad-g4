* Trial T2-DG v2: T2 winner + DensityGradient quantum correction
* Fixed: eQuantumPotential must use DensityGradient section directly
* hbound set to CNT diameter 0.78nm

File {
    Grid    = "input/structure_msh.tdr"
    Parameter = "input/sdevice_T2DG.par"
    Plot    = "output/sdevice_T2DG_plt.tdr"
    Current = "output/sdevice_T2DG_IdVg.plt"
    Output  = "output/sdevice_T2DG_log.log"
}

Electrode {
    { Name="source"    Voltage=0.0  Schottky Workfunction=4.0 }
    { Name="drain"     Voltage=0.0  Schottky Workfunction=4.0 }
    { Name="gate"      Voltage=0.0  Workfunction=4.65 }
    { Name="substrate" Voltage=0.0 }
}

Physics {
    AreaFactor=1e6
    Fermi
    Thermionic
    Mobility (
        ConstantMobility
        HighFieldSaturation
    )
    Recombination ( SRH )
    EffectiveIntrinsicDensity (
        NoBandGapNarrowing
    )
    * ENHANCEMENT: DensityGradient quantum correction
    * For CNT: hbound = diameter = 0.78nm
    eQuantumPotential (
        DensityGradient
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
    ePotential hPotential
    eQuantumPotential hQuantumPotential
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
    ErrorExtrapolate
}

Solve {
    * Step 1: Initial solve with 2-eq
    Poisson
    Coupled { Poisson Electron }

    * Step 2: Ramp Vds
    NewCurrentPrefix="ramp_vds_"
    Quasistationary (
        InitialStep=1e-3 MaxStep=0.05 MinStep=1e-7
        Goal { Name="drain" Voltage=0.05 }
    ) { Coupled { Poisson Electron } }

    * Step 3: Add Hole + DG
    Coupled { Poisson Electron Hole eQuantumPotential }

    * Step 4: IdVg sweep
    NewCurrentPrefix="IdVg_"
    Quasistationary (
        InitialStep=1e-3 MaxStep=0.02 MinStep=1e-8
        Goal { Name="gate" Voltage=1.0 }
    ) { Coupled { Poisson Electron Hole eQuantumPotential } }
}
