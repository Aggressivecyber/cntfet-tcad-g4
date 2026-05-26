File {
    Grid    = "input/structure_msh.tdr"
    Parameter = "input/sdevice_T9.par"
    Plot    = "output/sdevice_T9_plt.tdr"
    Current = "output/sdevice_T9_IdVg.plt"
    Output  = "output/sdevice_T9_log.log"
}

Electrode {
    * Ohmic contacts - target production configuration
    { Name="source"    Voltage=0.0 }
    { Name="drain"     Voltage=0.0 }
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

    * Quantum correction for CNT confinement
    eQuantumPotential (
        * Density gradient model for CNT
        * Effective mass ~ 0.05 m0 for (19,0) zigzag CNT
        * gamma_0 calibrated for d=1.49nm CNT
        Equation (
            Type = "DensityGradient"
            nQuantumPotential
            * Parameters defined in .par file
        )
    )

    Mobility (
        * Use built-in CNT mobility model (Landauer approach)
        * Reference: OLH ID:6030
        CarbonNanotube
        HighFieldSaturation
    )

    Recombination (
        SRH
        Auger                    * Added for off-state leakage suppression
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
    PotentialSpaceCharge
    TotalRecombination
    eGradQuasiFermi/Vector
    hGradQuasiFermi/Vector
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
    * Quantum potential specific settings
    ComputeGradQuasiFermiAtContacts = UseQuasiFermi
}

Solve {
    * Phase 1: DD warm-up without quantum correction
    Poisson
    Coupled { Poisson Electron }

    NewCurrentPrefix="ramp_vds_"
    Quasistationary (
        InitialStep=1e-3 MaxStep=0.05 MinStep=1e-7
        Goal { Name="drain" Voltage=0.05 }
    ) { Coupled { Poisson Electron } }

    * Phase 2: Add Hole equation
    Coupled { Poisson Electron Hole }

    * Phase 3: IdVg sweep with full physics
    * NOTE: If eQP causes convergence issues, remove Temperature
    * from Coupled and run as: Coupled { Poisson Electron Hole }
    NewCurrentPrefix="IdVg_"
    Quasistationary (
        InitialStep=1e-3 MaxStep=0.01 MinStep=1e-9
        Goal { Name="gate" Voltage=1.0 }
    ) { Coupled { Poisson Electron Hole Temperature } }
}
