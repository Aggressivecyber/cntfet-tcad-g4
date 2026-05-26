#include "CNTFETDetectorConstruction.hh"
#include "CNTFETPhysicsList.hh"
#include "CNTFETActionInitialization.hh"

#include "G4RunManagerFactory.hh"
#include "G4UImanager.hh"
#include "G4VisExecutive.hh"
#include "G4UIExecutive.hh"

int main(int argc, char** argv)
{
    // Detect interactive mode
    G4UIExecutive* ui = nullptr;
    if (argc == 1) {
        ui = new G4UIExecutive(argc, argv);
    }

    // Parse command line arguments
    // Usage: cntfet_dosimetry [A|B|C] [macro_file]
    G4String dielectricConfig = "A";
    G4String macroFile = "";

    for (G4int i = 1; i < argc; ++i) {
        G4String arg = argv[i];
        if (arg == "A" || arg == "B" || arg == "C") {
            dielectricConfig = arg;
        } else if (arg[0] != '-') {
            macroFile = arg;
        }
    }

    // Force single-threaded mode
    setenv("G4FORCENUMBEROFTHREADS", "1", 1);

    // Construct the run manager
    auto* runManager = G4RunManagerFactory::CreateRunManager(
        G4RunManagerType::Serial);

    // Set mandatory initialization classes
    auto* detector = new CNTFETDetectorConstruction();
    detector->SetDielectricConfig(dielectricConfig);
    runManager->SetUserInitialization(detector);

    auto* physicsList = new CNTFETPhysicsList();
    runManager->SetUserInitialization(physicsList);

    // Set user action initialization
    auto* actionInit = new CNTFETActionInitialization(detector);
    runManager->SetUserInitialization(actionInit);

    // Initialize G4 kernel
    runManager->Initialize();

    // Initialize visualization
    G4VisManager* visManager = new G4VisExecutive;
    visManager->Initialize();

    // Get the pointer to the User Interface manager
    G4UImanager* UImanager = G4UImanager::GetUIpointer();

    // Process macro or start interactive session
    if (ui) {
        ui->SessionStart();
        delete ui;
    } else {
        if (!macroFile.empty()) {
            G4String command = "/control/execute " + macroFile;
            UImanager->ApplyCommand(command);
        }
    }

    // Job termination
    delete visManager;
    delete runManager;

    return 0;
}
