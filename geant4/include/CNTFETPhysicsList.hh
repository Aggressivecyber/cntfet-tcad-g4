#ifndef CNTFETPhysicsList_h
#define CNTFETPhysicsList_h 1

#include "globals.hh"
#include "G4VModularPhysicsList.hh"

class CNTFETPhysicsList : public G4VModularPhysicsList
{
public:
    CNTFETPhysicsList();
    virtual ~CNTFETPhysicsList();

    virtual void SetCuts() override;
};

#endif
