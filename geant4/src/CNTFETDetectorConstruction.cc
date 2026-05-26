#include "CNTFETDetectorConstruction.hh"

#include "G4Material.hh"
#include "G4NistManager.hh"
#include "G4Element.hh"
#include "G4Tubs.hh"
#include "G4Box.hh"
#include "G4LogicalVolume.hh"
#include "G4PVPlacement.hh"
#include "G4PVParameterised.hh"
#include "G4Region.hh"
#include "G4SystemOfUnits.hh"
#include "G4PhysicalConstants.hh"
#include "G4UnitsTable.hh"
#include "G4VisAttributes.hh"
#include "G4Colour.hh"

CNTFETDetectorConstruction::CNTFETDetectorConstruction()
: G4VUserDetectorConstruction()
, fDielectricConfig("A")
, fWorldPV(nullptr)
, fDeviceMotherPV(nullptr)
{
    for (G4int i = 0; i < kNumVolumes; ++i) {
        fSensitiveLV[i] = nullptr;
    }
    fGateStackLV = nullptr;
    DefineMaterials();
}

CNTFETDetectorConstruction::~CNTFETDetectorConstruction()
{}

void CNTFETDetectorConstruction::DefineMaterials()
{
    G4NistManager* nist = G4NistManager::Instance();

    // Vacuum (world)
    fVacuum = nist->FindOrBuildMaterial("G4_Galactic");

    // Graphite-based CNT material with effective density 1.3 g/cm3
    // Use G4_C from NIST and create custom density material
    G4Element* elC = nist->FindOrBuildElement("C");
    fGraphiteCNT = new G4Material("CNT_Graphite", 1.3 * g / cm3, 1);
    fGraphiteCNT->AddElement(elC, 1);

    // SiO2 from NIST
    fSiO2 = nist->FindOrBuildMaterial("G4_SILICON_DIOXIDE");

    // HfO2: Hf=1, O=2, density=9.68 g/cm3, I=139 eV
    G4Element* elHf = nist->FindOrBuildElement("Hf");
    G4Element* elO  = nist->FindOrBuildElement("O");
    fHfO2 = new G4Material("HfO2", 9.68 * g / cm3, 2);
    fHfO2->AddElement(elHf, 1);
    fHfO2->AddElement(elO, 2);
    fHfO2->GetIonisation()->SetMeanExcitationEnergy(139.0 * eV);

    // Al2O3: Al=2, O=3, density=3.95 g/cm3, I=145 eV
    G4Element* elAl = nist->FindOrBuildElement("Al");
    fAl2O3 = new G4Material("Al2O3", 3.95 * g / cm3, 2);
    fAl2O3->AddElement(elAl, 2);
    fAl2O3->AddElement(elO, 3);
    fAl2O3->GetIonisation()->SetMeanExcitationEnergy(145.0 * eV);

    // TiN: Ti=1, N=1, density=5.22 g/cm3
    G4Element* elTi = nist->FindOrBuildElement("Ti");
    G4Element* elN  = nist->FindOrBuildElement("N");
    fTiN = new G4Material("TiN", 5.22 * g / cm3, 2);
    fTiN->AddElement(elTi, 1);
    fTiN->AddElement(elN, 1);

    // Pd: density=12.02 g/cm3
    G4Element* elPd = nist->FindOrBuildElement("Pd");
    fPd = new G4Material("Pd", 12.02 * g / cm3, 1);
    fPd->AddElement(elPd, 1);

    G4cout << "Materials defined:" << G4endl;
    G4cout << "  CNT (graphite, rho=1.3): " << fGraphiteCNT << G4endl;
    G4cout << "  SiO2: " << fSiO2 << G4endl;
    G4cout << "  HfO2 (rho=9.68): " << fHfO2 << G4endl;
    G4cout << "  Al2O3 (rho=3.95): " << fAl2O3 << G4endl;
    G4cout << "  TiN (rho=5.22): " << fTiN << G4endl;
    G4cout << "  Pd (rho=12.02): " << fPd << G4endl;
}

void CNTFETDetectorConstruction::SetDielectricConfig(const G4String& config)
{
    if (config == "A" || config == "B" || config == "C") {
        fDielectricConfig = config;
    } else {
        G4Exception("CNTFETDetectorConstruction::SetDielectricConfig",
                     "InvalidConfig", FatalException,
                     "Dielectric config must be A, B, or C");
    }
}

G4VPhysicalVolume* CNTFETDetectorConstruction::Construct()
{
    return BuildGeometry();
}

G4VPhysicalVolume* CNTFETDetectorConstruction::BuildGeometry()
{
    // ----------------------------------------------------------------
    // Geometry parameters (all in nm)
    // ----------------------------------------------------------------
    const G4double cntRadius      = 0.745 * nm;    // CNT radius (19,0)
    const G4double channelLength  = 32.0 * nm;     // Gate length
    const G4double gateMetalThick = 5.0 * nm;      // TiN thickness
    const G4double halfChannelZ   = channelLength / 2.0;

    // Dielectric thicknesses depend on config
    G4double diel1Inner = cntRadius;
    G4double diel1Outer = 0;
    G4double diel2Inner = 0;
    G4double diel2Outer = 0;
    G4Material* diel1Mat = nullptr;
    G4Material* diel2Mat = nullptr;
    G4String diel1Name = "";
    G4String diel2Name = "";

    if (fDielectricConfig == "A") {
        // SiO2 10 nm
        diel1Outer = cntRadius + 10.0 * nm;
        diel1Mat = fSiO2;
        diel1Name = "SiO2";
    } else if (fDielectricConfig == "B") {
        // HfO2 8 nm
        diel1Outer = cntRadius + 8.0 * nm;
        diel1Mat = fHfO2;
        diel1Name = "HfO2";
    } else {
        // Config C: Al2O3 (2 nm) + HfO2 (6 nm)
        diel1Outer = cntRadius + 2.0 * nm;
        diel1Mat = fAl2O3;
        diel1Name = "Al2O3";
        diel2Inner = diel1Outer;
        diel2Outer = diel2Inner + 6.0 * nm;
        diel2Mat = fHfO2;
        diel2Name = "HfO2";
    }

    G4double dielectricOuter = (fDielectricConfig == "C") ? diel2Outer : diel1Outer;
    G4double gateMetalOuter  = dielectricOuter + gateMetalThick;

    // Source/Drain: Pd boxes, 50nm x 50nm x channelLength
    const G4double sdHalfX = 25.0 * nm;
    const G4double sdHalfY = 25.0 * nm;
    const G4double sdHalfZ = halfChannelZ;

    // Substrate: SiO2, 300nm x 300nm x 100nm
    const G4double subHalfX = 150.0 * nm;
    const G4double subHalfY = 150.0 * nm;
    const G4double subHalfZ = 50.0 * nm;

    // World: 1 um x 1 um x 1 um
    const G4double worldHalfX = 0.5 * um;
    const G4double worldHalfY = 0.5 * um;
    const G4double worldHalfZ = 0.5 * um;

    // Device mother volume: slightly larger than gate metal + S/D
    // S/D extend to halfChannelZ + 32nm = 48nm from center
    const G4double devHalfX = sdHalfX + 10.0 * nm;
    const G4double devHalfY = sdHalfY + 10.0 * nm;
    const G4double devHalfZ = halfChannelZ + 32.0 * nm + 10.0 * nm; // 58nm

    // ----------------------------------------------------------------
    // World volume
    // ----------------------------------------------------------------
    G4Box* worldSolid = new G4Box("World", worldHalfX, worldHalfY, worldHalfZ);
    G4LogicalVolume* worldLV = new G4LogicalVolume(worldSolid, fVacuum, "WorldLV");
    fWorldPV = new G4PVPlacement(nullptr, G4ThreeVector(), worldLV, "WorldPV",
                                  nullptr, false, 0);

    // ----------------------------------------------------------------
    // Substrate (placed below device)
    // ----------------------------------------------------------------
    G4double substrateZPos = -(gateMetalOuter + subHalfZ + 5.0 * nm);
    G4Box* substrateSolid = new G4Box("Substrate", subHalfX, subHalfY, subHalfZ);
    G4LogicalVolume* substrateLV = new G4LogicalVolume(substrateSolid, fSiO2, "SubstrateLV");
    new G4PVPlacement(nullptr, G4ThreeVector(0, 0, substrateZPos),
                       substrateLV, "SubstratePV", worldLV, false, 0);
    fSensitiveLV[6] = substrateLV;

    // ----------------------------------------------------------------
    // Device mother volume (for biasing region)
    // ----------------------------------------------------------------
    G4Box* deviceMotherSolid = new G4Box("DeviceMother", devHalfX, devHalfY, devHalfZ);
    G4LogicalVolume* deviceMotherLV = new G4LogicalVolume(deviceMotherSolid, fVacuum, "DeviceMotherLV");
    fDeviceMotherPV = new G4PVPlacement(nullptr, G4ThreeVector(0, 0, 0),
                                          deviceMotherLV, "DeviceMotherPV",
                                          worldLV, false, 0);

    // ================================================================
    // CONCENTRIC CYLINDER STACK - NESTED GEOMETRY
    // Each layer is placed inside the outer layer's logical volume.
    // This avoids Geant4 overlap issues with same-position volumes.
    // ================================================================

    // ----------------------------------------------------------------
    // Gate metal (outermost cylinder) - placed in deviceMotherLV
    // Full cylinder from r=0 to gateMetalOuter, material=TiN
    // but we use annular ring: dielectricOuter to gateMetalOuter
    // The gate metal contains the dielectric inside its inner bore
    // ----------------------------------------------------------------
    // Instead, use the gate metal as a FULL solid cylinder with TiN
    // material, then place dielectric as a daughter that fills the bore.
    // Actually, the cleanest approach: gate metal is an annular ring,
    // and we use a "filler" vacuum cylinder in the bore, which then
    // contains the dielectric stack.
    //
    // Even cleaner: just use non-overlapping annular rings all placed
    // in deviceMotherLV. Geant4 CAN handle this IF the solids don't
    // overlap. Annular rings with same Z but different R ranges DON'T
    // overlap.
    //
    // The segfault was likely due to S/D box overlap with cylinders.
    // Let me use a simpler approach: single full cylinder as mother.
    // ================================================================

    // Approach: Use gateMetalOuter radius as outer boundary.
    // Create a FULL solid cylinder (r=0 to gateMetalOuter) as "GateStack"
    // with vacuum material, then place concentric rings inside it.

    // Gate stack envelope (full cylinder, vacuum)
    G4Tubs* gateStackSolid = new G4Tubs("GateStack", 0., gateMetalOuter,
                                         halfChannelZ, 0., twopi);
    G4LogicalVolume* gateStackLV = new G4LogicalVolume(gateStackSolid, fVacuum, "GateStackLV");
    new G4PVPlacement(nullptr, G4ThreeVector(0, 0, 0),
                       gateStackLV, "GateStackPV", deviceMotherLV, false, 0);
    fGateStackLV = gateStackLV;  // Save for biasing

    // Gate metal (annular ring, outermost)
    G4Tubs* gateMetalSolid = new G4Tubs("GateMetal", dielectricOuter, gateMetalOuter,
                                         halfChannelZ, 0., twopi);
    G4LogicalVolume* gateMetalLV = new G4LogicalVolume(gateMetalSolid, fTiN, "GateMetalLV");
    new G4PVPlacement(nullptr, G4ThreeVector(0, 0, 0),
                       gateMetalLV, "GateMetalPV", gateStackLV, false, 0);
    fSensitiveLV[3] = gateMetalLV;

    // For config C: dielectric layer 2 (HfO2, outer dielectric)
    if (fDielectricConfig == "C") {
        G4Tubs* diel2Solid = new G4Tubs("Diel2", diel2Inner, diel2Outer,
                                         halfChannelZ, 0., twopi);
        G4LogicalVolume* diel2LV = new G4LogicalVolume(diel2Solid, diel2Mat,
                                                         "Diel2LV_" + diel2Name);
        new G4PVPlacement(nullptr, G4ThreeVector(0, 0, 0),
                           diel2LV, "Diel2PV", gateStackLV, false, 0);
        fSensitiveLV[2] = diel2LV;
    } else {
        fSensitiveLV[2] = nullptr;
    }

    // Dielectric layer 1 (annular ring around CNT)
    G4Tubs* diel1Solid = new G4Tubs("Diel1", diel1Inner, diel1Outer,
                                     halfChannelZ, 0., twopi);
    G4LogicalVolume* diel1LV = new G4LogicalVolume(diel1Solid, diel1Mat,
                                                     "Diel1LV_" + diel1Name);
    new G4PVPlacement(nullptr, G4ThreeVector(0, 0, 0),
                       diel1LV, "Diel1PV", gateStackLV, false, 0);
    fSensitiveLV[1] = diel1LV;

    // CNT channel core (solid cylinder at center)
    G4Tubs* cntSolid = new G4Tubs("CNT", 0., cntRadius, halfChannelZ, 0., twopi);
    G4LogicalVolume* cntLV = new G4LogicalVolume(cntSolid, fGraphiteCNT, "CNTLV");
    new G4PVPlacement(nullptr, G4ThreeVector(0, 0, 0),
                       cntLV, "CNTPV", gateStackLV, false, 0);
    fSensitiveLV[0] = cntLV;

    // ----------------------------------------------------------------
    // Source/Drain contacts (Pd boxes placed OUTSIDE gate region)
    // Source: from z = -(halfChannelZ + sdLength) to z = -halfChannelZ
    // Drain:  from z = +halfChannelZ to z = +(halfChannelZ + sdLength)
    // S/D are placed in deviceMotherLV (not in gateStackLV).
    // Their XY extent (50nm x 50nm) overlaps with gateStack cylinder
    // in XY but NOT in Z, so no actual overlap.
    // ----------------------------------------------------------------
    G4double sdLength = 32.0 * nm;
    G4double sdHalfLen = sdLength / 2.0;
    G4double sourceZPos = -(halfChannelZ + sdHalfLen);
    G4double drainZPos  = +(halfChannelZ + sdHalfLen);

    G4Box* sourceSolid = new G4Box("Source", sdHalfX, sdHalfY, sdHalfLen);
    G4LogicalVolume* sourceLV = new G4LogicalVolume(sourceSolid, fPd, "SourceLV");
    new G4PVPlacement(nullptr, G4ThreeVector(0, 0, sourceZPos),
                       sourceLV, "SourcePV", deviceMotherLV, false, 0);
    fSensitiveLV[4] = sourceLV;

    G4Box* drainSolid = new G4Box("Drain", sdHalfX, sdHalfY, sdHalfLen);
    G4LogicalVolume* drainLV = new G4LogicalVolume(drainSolid, fPd, "DrainLV");
    new G4PVPlacement(nullptr, G4ThreeVector(0, 0, drainZPos),
                       drainLV, "DrainPV", deviceMotherLV, false, 0);
    fSensitiveLV[5] = drainLV;

    // ----------------------------------------------------------------
    // Visualization
    // ----------------------------------------------------------------
    SetVisualization();

    // ----------------------------------------------------------------
    // Print geometry summary
    // ----------------------------------------------------------------
    G4cout << "\n========================================" << G4endl;
    G4cout << "CNTFET Geometry - Config " << fDielectricConfig << G4endl;
    G4cout << "========================================" << G4endl;
    G4cout << "CNT radius:       " << G4BestUnit(cntRadius, "Length") << G4endl;
    G4cout << "Channel length:   " << G4BestUnit(channelLength, "Length") << G4endl;
    G4cout << "Diel1 (" << diel1Name << "): "
            << G4BestUnit(diel1Inner, "Length") << " -> "
            << G4BestUnit(diel1Outer, "Length") << G4endl;
    if (fDielectricConfig == "C") {
        G4cout << "Diel2 (" << diel2Name << "): "
                << G4BestUnit(diel2Inner, "Length") << " -> "
                << G4BestUnit(diel2Outer, "Length") << G4endl;
    }
    G4cout << "Gate metal outer: " << G4BestUnit(gateMetalOuter, "Length") << G4endl;
    G4cout << "========================================\n" << G4endl;

    return fWorldPV;
}

void CNTFETDetectorConstruction::SetVisualization()
{
    // World: invisible
    fWorldPV->GetLogicalVolume()->SetVisAttributes(G4VisAttributes::GetInvisible());

    // CNT: green
    G4VisAttributes* cntVis = new G4VisAttributes(G4Colour(0.0, 1.0, 0.0));
    cntVis->SetForceSolid(true);
    if (fSensitiveLV[0]) fSensitiveLV[0]->SetVisAttributes(cntVis);

    // Dielectric 1: blue
    G4VisAttributes* diel1Vis = new G4VisAttributes(G4Colour(0.0, 0.0, 1.0, 0.5));
    diel1Vis->SetForceSolid(true);
    if (fSensitiveLV[1]) fSensitiveLV[1]->SetVisAttributes(diel1Vis);

    // Dielectric 2: cyan (config C only)
    G4VisAttributes* diel2Vis = new G4VisAttributes(G4Colour(0.0, 1.0, 1.0, 0.5));
    diel2Vis->SetForceSolid(true);
    if (fSensitiveLV[2]) fSensitiveLV[2]->SetVisAttributes(diel2Vis);

    // Gate metal: gray
    G4VisAttributes* gateVis = new G4VisAttributes(G4Colour(0.5, 0.5, 0.5, 0.7));
    gateVis->SetForceSolid(true);
    if (fSensitiveLV[3]) fSensitiveLV[3]->SetVisAttributes(gateVis);

    // Source/Drain: red/orange
    G4VisAttributes* srcVis = new G4VisAttributes(G4Colour(1.0, 0.3, 0.0, 0.6));
    srcVis->SetForceSolid(true);
    if (fSensitiveLV[4]) fSensitiveLV[4]->SetVisAttributes(srcVis);

    G4VisAttributes* drnVis = new G4VisAttributes(G4Colour(1.0, 0.5, 0.0, 0.6));
    drnVis->SetForceSolid(true);
    if (fSensitiveLV[5]) fSensitiveLV[5]->SetVisAttributes(drnVis);

    // Substrate: light gray
    G4VisAttributes* subVis = new G4VisAttributes(G4Colour(0.8, 0.8, 0.8, 0.3));
    subVis->SetForceSolid(true);
    if (fSensitiveLV[6]) fSensitiveLV[6]->SetVisAttributes(subVis);

    // Device mother: invisible
    G4VisAttributes* devVis = new G4VisAttributes(G4VisAttributes::GetInvisible());
    if (fDeviceMotherPV && fDeviceMotherPV->GetLogicalVolume())
        fDeviceMotherPV->GetLogicalVolume()->SetVisAttributes(devVis);
}

G4LogicalVolume* CNTFETDetectorConstruction::GetSensitiveLV(G4int id) const
{
    if (id >= 0 && id < kNumVolumes) return fSensitiveLV[id];
    return nullptr;
}
