#ifndef CNTFETActionInitialization_h
#define CNTFETActionInitialization_h 1

#include "globals.hh"
#include "G4VUserActionInitialization.hh"

class CNTFETDetectorConstruction;

class CNTFETActionInitialization : public G4VUserActionInitialization
{
public:
    CNTFETActionInitialization(CNTFETDetectorConstruction* det);
    virtual ~CNTFETActionInitialization();

    virtual void BuildForMaster() const override;
    virtual void Build() const override;

private:
    CNTFETDetectorConstruction* fDetector;
};

#endif
