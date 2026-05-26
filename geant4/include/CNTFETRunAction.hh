#ifndef CNTFETRunAction_h
#define CNTFETRunAction_h 1

#include "globals.hh"
#include "G4UserRunAction.hh"
#include <vector>
#include <string>

class G4Run;

class CNTFETRunAction : public G4UserRunAction
{
public:
    CNTFETRunAction();
    virtual ~CNTFETRunAction();

    virtual void BeginOfRunAction(const G4Run* aRun) override;
    virtual void EndOfRunAction(const G4Run* aRun) override;

    void AddEnergyDeposition(G4int volumeId, G4double edep);

    void SetDielectricConfig(const G4String& config) { fDielectricConfig = config; }

private:
    void WriteDoseProfile();
    void WriteEnergySummary();
    void WriteDosimetryJSON();

    static const G4int kNumVolumes = 7;
    G4String fVolumeNames[kNumVolumes];

    std::vector<G4double> fTotalEdep;
    std::vector<G4double> fTotalEdep2;
    G4int fNumEvents;

    G4String fDielectricConfig;
};

#endif
