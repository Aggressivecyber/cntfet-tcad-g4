* Trial T2-Thermo v2: T2 winner + Thermodynamic model
* Fixed: Temperature only in Thermode section, not in Electrode

File {
    Grid    = "input/structure_msh.tdr"
    Parameter = "input/sdevice_T2Thermo.par"
    Plot    = "output/sdevice_T2Thermo_plt.tdr"
    Current = "output/sdevice_T2Thermo_IdVg.plt"
    Output  = "output/sdevice_T2Thermo_log.log"
}

Electrode {
    { Name="source"    Voltage=0.0  Schottky Workfunction=4.0 }
    { Name="drain"     Voltage=0.0  Schottky Workfunction=4.0 }
    { Name="gate"      Voltage=0.0  Workfunction=4.65 }
    { Name="substrate" Voltage=0.0 }
}

Thermode {
    { Name="source"    Temperature=300.0 }
    { Name="drain"     Temperature=300.0 }
    { Name="gate"      Temperature=300.0 }
    { Name="substrate" Temperature=300.0 }
}

Physics {
    AreaFactor=1e6
    Fermi
    Thermionic
    Thermodynamic
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
    LatticeTemperature
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
    * Step 1: Initial solve
    Poisson
    Coupled { Poisson Electron }

    * Step 2: Ramp Vds
    NewCurrentPrefix="ramp_vds_"
    Quasistationary (
        InitialStep=1e-3 MaxStep=0.05 MinStep=1e-7
        Goal { Name="drain" Voltage=0.05 }
    ) { Coupled { Poisson Electron } }

    * Step 3: Switch to 4-eq (add Hole + Temperature)
    Coupled { Poisson Electron Hole Temperature }

    * Step 4: IdVg sweep with Thermodynamic
    NewCurrentPrefix="IdVg_"
    Quasistationary (
        InitialStep=1e-3 MaxStep=0.02 MinStep=1e-8
        Goal { Name="gate" Voltage=1.0 }
    ) { Coupled { Poisson Electron Hole Temperature } }
}
