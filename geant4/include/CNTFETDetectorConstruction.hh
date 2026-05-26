#ifndef CNTFETDetectorConstruction_h
#define CNTFETDetectorConstruction_h 1

#include "globals.hh"
#include "G4VUserDetectorConstruction.hh"

class G4VPhysicalVolume;
class G4LogicalVolume;
class G4Material;

class CNTFETDetectorConstruction : public G4VUserDetectorConstruction
{
public:
    CNTFETDetectorConstruction();
    virtual ~CNTFETDetectorConstruction();

    virtual G4VPhysicalVolume* Construct() override;

    void SetDielectricConfig(const G4String& config);
    const G4String& GetDielectricConfig() const { return fDielectricConfig; }

    G4VPhysicalVolume* GetWorldPV() const { return fWorldPV; }
    G4VPhysicalVolume* GetDeviceVolume() const { return fDeviceMotherPV; }
    G4LogicalVolume* GetGateStackLV() const { return fGateStackLV; }

    static const G4int kNumVolumes = 7;
    G4LogicalVolume* GetSensitiveLV(G4int id) const;

private:
    void DefineMaterials();
    G4VPhysicalVolume* BuildGeometry();
    void SetVisualization();

    G4String fDielectricConfig;
    G4VPhysicalVolume* fWorldPV;
    G4VPhysicalVolume* fDeviceMotherPV;
    G4LogicalVolume* fGateStackLV;
    G4LogicalVolume* fSensitiveLV[kNumVolumes];

    G4Material* fVacuum;
    G4Material* fGraphiteCNT;
    G4Material* fSiO2;
    G4Material* fHfO2;
    G4Material* fAl2O3;
    G4Material* fTiN;
    G4Material* fPd;
};

#endif
