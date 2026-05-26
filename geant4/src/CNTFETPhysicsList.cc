#include "CNTFETPhysicsList.hh"

#include "G4EmLivermorePhysics.hh"
#include "G4DecayPhysics.hh"
#include "G4RadioactiveDecayPhysics.hh"
#include "G4SystemOfUnits.hh"

CNTFETPhysicsList::CNTFETPhysicsList()
: G4VModularPhysicsList()
{
    // Livermore: low-energy EM down to ~250 eV, needed for nm-scale dose accuracy
    RegisterPhysics(new G4EmLivermorePhysics());

    RegisterPhysics(new G4DecayPhysics());

    // Co-60 -> Ni-60* + gammas
    RegisterPhysics(new G4RadioactiveDecayPhysics());

    G4cout << "PhysicsList: G4EmLivermorePhysics + Decay + RadioactiveDecay" << G4endl;

    // Production cut: 100 nm. The smallest geometry features (CNT 0.745 nm radius,
    // dielectric 2-10 nm) are far below any reasonable cut. Lowering the cut below
    // 100 nm would dramatically increase simulation time for marginal spatial resolution
    // gain: Co-60 secondary electrons have energies ~hundreds of keV (range ~mm) and
    // deposit energy over distances far exceeding nm scales. The 100 nm cut captures
    // the dominant energy deposition channels without tracking sub-nm secondaries.
    SetDefaultCutValue(0.1 * um);

    G4cout << "Default production cut: 0.1 um (100 nm)" << G4endl;
}

CNTFETPhysicsList::~CNTFETPhysicsList()
{}

void CNTFETPhysicsList::SetCuts()
{
    SetCutValue(0.1 * um, "gamma");
    SetCutValue(0.1 * um, "e-");
    SetCutValue(0.1 * um, "e+");
    SetCutValue(0.1 * um, "proton");

    G4cout << "Production cuts set to 0.1 um (100 nm) for all particles." << G4endl;
}
