#include "CNTFETEventAction.hh"
#include "CNTFETRunAction.hh"

#include "G4Event.hh"

#include <algorithm>

CNTFETEventAction::CNTFETEventAction(CNTFETRunAction* runAction)
: G4UserEventAction()
, fRunAction(runAction)
{
    fEventEdep.resize(kNumVolumes, 0.0);
}

CNTFETEventAction::~CNTFETEventAction()
{}

void CNTFETEventAction::BeginOfEventAction(const G4Event* /*anEvent*/)
{
    std::fill(fEventEdep.begin(), fEventEdep.end(), 0.0);
}

void CNTFETEventAction::AddEnergyDeposition(G4int volumeId, G4double edep)
{
    if (volumeId >= 0 && volumeId < kNumVolumes) {
        fEventEdep[volumeId] += edep;
    }
}

void CNTFETEventAction::EndOfEventAction(const G4Event* /*anEvent*/)
{
    for (G4int i = 0; i < kNumVolumes; ++i) {
        fRunAction->AddEnergyDeposition(i, fEventEdep[i]);
    }
}
