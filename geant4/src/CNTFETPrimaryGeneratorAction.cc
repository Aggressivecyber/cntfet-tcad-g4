#include "CNTFETPrimaryGeneratorAction.hh"

#include "G4ParticleGun.hh"
#include "G4SystemOfUnits.hh"
#include "G4PhysicalConstants.hh"
#include "G4ParticleDefinition.hh"
#include "G4ParticleTable.hh"
#include "G4RandomTools.hh"

CNTFETPrimaryGeneratorAction::CNTFETPrimaryGeneratorAction()
: G4VUserPrimaryGeneratorAction()
, fParticleGun(nullptr)
, fSourceDistance(0.5 * um)
{
    G4int nParticle = 1;
    fParticleGun = new G4ParticleGun(nParticle);

    G4ParticleDefinition* gamma =
        G4ParticleTable::GetParticleTable()->FindParticle("gamma");
    fParticleGun->SetParticleDefinition(gamma);

    fParticleGun->SetParticleEnergy(1.1732 * MeV);
}

CNTFETPrimaryGeneratorAction::~CNTFETPrimaryGeneratorAction()
{
    delete fParticleGun;
}

void CNTFETPrimaryGeneratorAction::GeneratePrimaries(G4Event* anEvent)
{
    // Co-60 gamma: randomly choose between 1.1732 MeV and 1.3325 MeV
    G4double energy;
    if (G4UniformRand() < 0.5) {
        energy = 1.1732 * MeV;
    } else {
        energy = 1.3325 * MeV;
    }
    fParticleGun->SetParticleEnergy(energy);

    // Generate gamma aimed at the device region
    // Place source just above the substrate (y = gateMetalOuter + small gap)
    // and aim downward through the device
    // Use a small area around the device center to maximize hits
    //
    // The device gate stack has outer radius ~15.7 nm
    // Generate gammas on a small disk (50nm radius) above the device
    // aiming straight down (-y direction)
    //
    // This represents a collimated beam geometry where fluence is known.
    // The dose per gamma can later be scaled to any fluence level.

    // Source along the Z axis (cylinder axis), gammas aimed along -z
    // The G4Tubs cylinder is along z-axis from z=-16nm to z=+16nm
    // Gamma from (x0, y0, +0.5um) going -z will enter the cylinder
    // if sqrt(x0^2 + y0^2) <= 15.7 nm (the gate metal outer radius)
    // This ensures the gamma travels along the cylinder, maximizing path length

    G4double sourceZ = 0.49 * um;  // Just inside the world boundary
    G4double r = 15.0 * nm * std::sqrt(G4UniformRand());
    G4double phi = G4UniformRand() * twopi;
    G4double x0 = r * std::cos(phi);
    G4double y0 = r * std::sin(phi);

    fParticleGun->SetParticlePosition(G4ThreeVector(x0, y0, sourceZ));

    // Direction: along -z axis (along cylinder axis) -- maximum path length
    fParticleGun->SetParticleMomentumDirection(G4ThreeVector(0., 0., -1.));

    fParticleGun->GeneratePrimaryVertex(anEvent);
}
