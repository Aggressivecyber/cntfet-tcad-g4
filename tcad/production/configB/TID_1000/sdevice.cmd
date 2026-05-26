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

* TID=1000 krad: HfO2 bulk trapped charge
Physics (Material="HfO2") {
    Traps ((FixedCharge SpatialShape=Uniform Conc=3.0e18))
}

* Interface trapped charge: Donor + Acceptor states
Physics (MaterialInterface="CNT_thin_film/HfO2") {
    Traps (
        (FixedCharge SpatialShape=Uniform Conc=2.0e11)
        (Donor Conc=1.0e11 EnergyMid=0.0 EnergySig=0.1
            eXsection=1e-15 hXsection=1e-15 fromMidBandGap)
        (Acceptor Conc=1.0e11 EnergyMid=0.0 EnergySig=0.1
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
    * Load baseline TID=0 solution with non-zero carrier densities
    Load(FilePrefix="input/baseline_tid0")

    * Adapt electrostatic potential to new oxide trap charge
    Poisson
    Coupled (Iterations=200) { Poisson Electron }

    * Switch to 3-eq with conservative damping
    Coupled (Iterations=200 LinesearchDamping=1e-3) { Poisson Electron Hole }

    * Ramp Vds
    NewCurrentPrefix="ramp_vds_"
    Quasistationary (
        InitialStep=1e-3 MaxStep=0.05 MinStep=1e-10
        Increment=1.1 Decrement=3.0
        Goal { Name="drain" Voltage=0.05 }
    ) { Coupled (Iterations=200) { Poisson Electron Hole } }

    * IdVg sweep
    NewCurrentPrefix="IdVg_"
    Quasistationary (
        InitialStep=5e-4 MaxStep=0.02 MinStep=1e-13
        Increment=1.1 Decrement=3.0
        Goal { Name="gate" Voltage=1.0 }
    ) { Coupled (Iterations=200) { Poisson Electron Hole } }
}
