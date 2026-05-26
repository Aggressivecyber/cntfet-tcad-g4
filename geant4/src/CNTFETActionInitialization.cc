#include "CNTFETActionInitialization.hh"
#include "CNTFETDetectorConstruction.hh"
#include "CNTFETPrimaryGeneratorAction.hh"
#include "CNTFETRunAction.hh"
#include "CNTFETEventAction.hh"
#include "CNTFETSteppingAction.hh"

CNTFETActionInitialization::CNTFETActionInitialization(CNTFETDetectorConstruction* det)
: G4VUserActionInitialization()
, fDetector(det)
{}

CNTFETActionInitialization::~CNTFETActionInitialization()
{}

void CNTFETActionInitialization::BuildForMaster() const
{
    SetUserAction(new CNTFETRunAction());
}

void CNTFETActionInitialization::Build() const
{
    auto* runAction = new CNTFETRunAction();
    runAction->SetDielectricConfig(fDetector->GetDielectricConfig());

    auto* eventAction = new CNTFETEventAction(runAction);
    auto* primaryGenerator = new CNTFETPrimaryGeneratorAction();
    auto* steppingAction = new CNTFETSteppingAction(eventAction);

    SetUserAction(runAction);
    SetUserAction(eventAction);
    SetUserAction(primaryGenerator);
    SetUserAction(steppingAction);
}
