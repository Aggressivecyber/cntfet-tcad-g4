#ifndef CNTFETEventAction_h
#define CNTFETEventAction_h 1

#include "globals.hh"
#include "G4UserEventAction.hh"
#include <vector>

class CNTFETRunAction;

class CNTFETEventAction : public G4UserEventAction
{
public:
    CNTFETEventAction(CNTFETRunAction* runAction);
    virtual ~CNTFETEventAction();

    virtual void BeginOfEventAction(const G4Event* anEvent) override;
    virtual void EndOfEventAction(const G4Event* anEvent) override;

    void AddEnergyDeposition(G4int volumeId, G4double edep);

private:
    CNTFETRunAction* fRunAction;

    static const G4int kNumVolumes = 7;
    std::vector<G4double> fEventEdep;
};

#endif
