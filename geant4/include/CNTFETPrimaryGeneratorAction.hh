#ifndef CNTFETPrimaryGeneratorAction_h
#define CNTFETPrimaryGeneratorAction_h 1

#include "G4VUserPrimaryGeneratorAction.hh"
#include "globals.hh"

class G4ParticleGun;
class G4Event;

class CNTFETPrimaryGeneratorAction : public G4VUserPrimaryGeneratorAction
{
public:
    CNTFETPrimaryGeneratorAction();
    virtual ~CNTFETPrimaryGeneratorAction();

    virtual void GeneratePrimaries(G4Event* anEvent) override;

private:
    G4ParticleGun* fParticleGun;
    G4double fSourceDistance; // 1 cm
};

#endif
