File {
    Grid    = "input/structure_msh.tdr"
    Parameter = "input/sdevice.par"
    Plot    = "output/sdevice_plt.tdr"
    Current = "output/sdevice_IdVg.plt"
    Output  = "output/sdevice_log.log"
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
    Mobility ( ConstantMobility HighFieldSaturation )
    Recombination ( SRH )
    EffectiveIntrinsicDensity ( NoBandGapNarrowing )
}

* TID=0 krad: HfO2 bulk trapped charge
Physics (Material="HfO2") {
    Traps ((FixedCharge SpatialShape=Uniform Conc=1.0e18))
}

* Interface trapped charge: Donor + Acceptor states
Physics (MaterialInterface="CNT_thin_film/HfO2") {
    Traps (
        (FixedCharge SpatialShape=Uniform Conc=1.0e11)
        (Donor Conc=5.0e10 EnergyMid=0.0 EnergySig=0.1
            eXsection=1e-15 hXsection=1e-15 fromMidBandGap)
        (Acceptor Conc=5.0e10 EnergyMid=0.0 EnergySig=0.1
            eXsection=1e-15 hXsection=1e-15 fromMidBandGap)
    )
}

Plot {
    eDensity hDensity Potential SpaceCharge
    eCurrent/Vector hCurrent/Vector
    eMobility hMobility ElectricField/Vector
    eQuasiFermi hQuasiFermi
    ConductionBandEnergy ValenceBandEnergy
}

Math {
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
}

Solve {
    Poisson
    Coupled (Iterations=200) { Poisson Electron }

    * Ramp Vds
    NewCurrentPrefix="ramp_vds_"
    Quasistationary (
        InitialStep=1e-3 MaxStep=0.05 MinStep=1e-8
        Increment=2 Decrement=2
        Goal { Name="drain" Voltage=0.05 }
    ) { Coupled { Poisson Electron } }

    Coupled (Iterations=200) { Poisson Electron Hole }

    * IdVg sweep
    NewCurrentPrefix="IdVg_"
    Quasistationary (
        InitialStep=1e-3 MaxStep=0.05 MinStep=1e-12
        Increment=2 Decrement=2
        Goal { Name="gate" Voltage=1.0 }
    ) { Coupled { Poisson Electron Hole } }
}
