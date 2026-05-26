File {
    Grid    = "input/structure_msh.tdr"
    Parameter = "input/sdevice_mvp.par"
    Plot    = "output/sdevice_mvp_plt.tdr"
    Current = "output/sdevice_mvp_IdVg.plt"
    Output  = "output/sdevice_mvp_log.log"
}

Electrode {
    { Name="source"    Voltage=0.0  Schottky Workfunction=3.5 }
    { Name="drain"     Voltage=0.0  Schottky Workfunction=3.5 }
    { Name="gate"      Voltage=0.0  Workfunction=4.65 }
    { Name="substrate" Voltage=0.0 }
}

Physics {
    AreaFactor=1e6
    Thermionic
    Mobility (
        ConstantMobility
        HighFieldSaturation
    )
    Recombination ( SRH )
}

Plot {
    eDensity hDensity
    Potential SpaceCharge
    eCurrent/Vector hCurrent/Vector
    eMobility
    ElectricField/Vector
}

Math {
    Extrapolate
    Method = Blocked
    SubMethod = ParDiSo
    NotDamped=50
    Iterations=25
    Digits=4
    RecBoxIntegr
    RHSmin=1e-12
    Number_of_threads=4
}

Solve {
    Poisson
    Coupled { Poisson Electron }

    NewCurrentPrefix="ramp_vds_"
    Quasistationary (
        InitialStep=1e-3 MaxStep=0.05 MinStep=1e-7
        Goal { Name="drain" Voltage=0.05 }
    ) { Coupled { Poisson Electron } }

    NewCurrentPrefix="IdVg_"
    Quasistationary (
        InitialStep=1e-3 MaxStep=0.02 MinStep=1e-8
        Goal { Name="gate" Voltage=1.0 }
    ) { Coupled { Poisson Electron } }
}
