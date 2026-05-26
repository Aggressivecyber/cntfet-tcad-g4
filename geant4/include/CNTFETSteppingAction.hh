#ifndef CNTFETSteppingAction_h
#define CNTFETSteppingAction_h 1

#include "globals.hh"
#include "G4UserSteppingAction.hh"

class CNTFETEventAction;

class CNTFETSteppingAction : public G4UserSteppingAction
{
public:
    CNTFETSteppingAction(CNTFETEventAction* eventAction);
    virtual ~CNTFETSteppingAction();

    virtual void UserSteppingAction(const G4Step* aStep) override;

private:
    CNTFETEventAction* fEventAction;
    G4int GetVolumeId(const G4Step* aStep) const;
};

#endif
