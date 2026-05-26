#include "CNTFETSteppingAction.hh"
#include "CNTFETEventAction.hh"
#include "CNTFETDetectorConstruction.hh"

#include "G4Step.hh"
#include "G4LogicalVolume.hh"
#include "G4VPhysicalVolume.hh"

CNTFETSteppingAction::CNTFETSteppingAction(CNTFETEventAction* eventAction)
: G4UserSteppingAction()
, fEventAction(eventAction)
{}

CNTFETSteppingAction::~CNTFETSteppingAction()
{}

G4int CNTFETSteppingAction::GetVolumeId(const G4Step* aStep) const
{
    G4LogicalVolume* lv = aStep->GetPreStepPoint()->GetTouchableHandle()
                           ->GetVolume()->GetLogicalVolume();
    const G4String& name = lv->GetName();

    // Match by logical volume name prefix
    if (name == "CNTLV")              return 0;
    if (name.find("Diel1LV_") == 0)   return 1;
    if (name.find("Diel2LV_") == 0)   return 2;
    if (name == "GateMetalLV")         return 3;
    if (name == "SourceLV")            return 4;
    if (name == "DrainLV")             return 5;
    if (name == "SubstrateLV")         return 6;

    return -1; // Not a sensitive volume
}

void CNTFETSteppingAction::UserSteppingAction(const G4Step* aStep)
{
    G4int volId = GetVolumeId(aStep);
    if (volId < 0) return; // Not in a sensitive volume

    G4double edep = aStep->GetTotalEnergyDeposit();
    if (edep <= 0) return;

    fEventAction->AddEnergyDeposition(volId, edep);
}
