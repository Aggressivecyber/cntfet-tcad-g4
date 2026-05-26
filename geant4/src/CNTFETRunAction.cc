#include "CNTFETRunAction.hh"

#include "G4Run.hh"
#include "G4SystemOfUnits.hh"
#include "G4PhysicalConstants.hh"
#include "G4UnitsTable.hh"

#include <fstream>
#include <sstream>
#include <iomanip>
#include <cmath>
#include <algorithm>

CNTFETRunAction::CNTFETRunAction()
: G4UserRunAction()
, fNumEvents(0)
, fDielectricConfig("A")
{
    fTotalEdep.resize(kNumVolumes, 0.0);
    fTotalEdep2.resize(kNumVolumes, 0.0);

    fVolumeNames[0] = "CNT_channel";
    fVolumeNames[1] = "Dielectric_layer1";
    fVolumeNames[2] = "Dielectric_layer2";
    fVolumeNames[3] = "Gate_metal_TiN";
    fVolumeNames[4] = "Source_Pd";
    fVolumeNames[5] = "Drain_Pd";
    fVolumeNames[6] = "Substrate_SiO2";
}

CNTFETRunAction::~CNTFETRunAction()
{}

void CNTFETRunAction::BeginOfRunAction(const G4Run* aRun)
{
    fNumEvents = 0;
    std::fill(fTotalEdep.begin(), fTotalEdep.end(), 0.0);
    std::fill(fTotalEdep2.begin(), fTotalEdep2.end(), 0.0);

    G4cout << "=== Run " << aRun->GetRunID() << " starting ===" << G4endl;
    G4cout << "Config: " << fDielectricConfig << G4endl;
}

void CNTFETRunAction::AddEnergyDeposition(G4int volumeId, G4double edep)
{
    if (volumeId < 0 || volumeId >= kNumVolumes) return;

    fTotalEdep[volumeId]  += edep;
    fTotalEdep2[volumeId] += edep * edep;
}

void CNTFETRunAction::EndOfRunAction(const G4Run* aRun)
{
    fNumEvents = aRun->GetNumberOfEvent();

    if (fNumEvents == 0) {
        G4cout << "No events processed." << G4endl;
        return;
    }

    G4cout << "\n================================================" << G4endl;
    G4cout << "Run Summary: " << fNumEvents << " events, Config "
            << fDielectricConfig << G4endl;
    G4cout << "================================================" << G4endl;

    for (G4int i = 0; i < kNumVolumes; ++i) {
        if (i == 2 && fDielectricConfig != "C") continue;

        G4double meanEdep = fTotalEdep[i] / fNumEvents;
        G4double meanEdep2 = fTotalEdep2[i] / fNumEvents;
        G4double variance = meanEdep2 - meanEdep * meanEdep;
        if (variance < 0) variance = 0;
        G4double rms = std::sqrt(variance);
        G4double relError = (meanEdep > 0) ? (rms / meanEdep) / std::sqrt(fNumEvents) : 0.0;

        G4cout << "  " << std::setw(22) << std::left << fVolumeNames[i]
                << " Edep/event = " << std::setw(12) << std::setprecision(4) << meanEdep / eV
                << " eV"
                << "  rel_err = " << std::setw(8) << std::setprecision(4) << relError * 100 << "%"
                << G4endl;
    }

    G4cout << "================================================\n" << G4endl;

    WriteDoseProfile();
    WriteEnergySummary();
    WriteDosimetryJSON();
}

void CNTFETRunAction::WriteDoseProfile()
{
    std::ostringstream fname;
    fname << "dose_profile_" << fDielectricConfig << ".csv";
    std::ofstream out(fname.str());

    out << "# Quasi-GAA CNTFET Co-60 Dosimetry - Config " << fDielectricConfig << "\n";
    out << "# Events: " << fNumEvents << "\n";
    out << "volume_name,total_edep_eV,mean_edep_per_event_eV,statistical_error_pct\n";

    for (G4int i = 0; i < kNumVolumes; ++i) {
        if (i == 2 && fDielectricConfig != "C") continue;

        G4double meanEdep = fTotalEdep[i] / fNumEvents;
        G4double meanEdep2 = fTotalEdep2[i] / fNumEvents;
        G4double variance = meanEdep2 - meanEdep * meanEdep;
        if (variance < 0) variance = 0;
        G4double relError = (meanEdep > 0) ?
            (std::sqrt(variance) / meanEdep) / std::sqrt(static_cast<double>(fNumEvents)) * 100.0 : 0.0;

        out << fVolumeNames[i] << ","
            << std::setprecision(6) << fTotalEdep[i] / eV << ","
            << std::setprecision(6) << meanEdep / eV << ","
            << std::setprecision(4) << relError << "\n";
    }
    out.close();
    G4cout << "Written: " << fname.str() << G4endl;
}

void CNTFETRunAction::WriteEnergySummary()
{
    std::ostringstream fname;
    fname << "energy_deposition_summary.json";
    std::ofstream out(fname.str());

    out << "{\n";
    out << "  \"dielectric_config\": \"" << fDielectricConfig << "\",\n";
    out << "  \"num_events\": " << fNumEvents << ",\n";
    out << "  \"source\": \"Co-60 gamma (1.1732 + 1.3325 MeV)\",\n";
    out << "  \"volumes\": {\n";

    bool first = true;
    for (G4int i = 0; i < kNumVolumes; ++i) {
        if (i == 2 && fDielectricConfig != "C") continue;

        G4double meanEdep = fTotalEdep[i] / fNumEvents;
        G4double meanEdep2 = fTotalEdep2[i] / fNumEvents;
        G4double variance = meanEdep2 - meanEdep * meanEdep;
        if (variance < 0) variance = 0;
        G4double relError = (meanEdep > 0) ?
            (std::sqrt(variance) / meanEdep) / std::sqrt(static_cast<double>(fNumEvents)) : 0.0;

        if (!first) out << ",\n";
        first = false;

        out << "    \"" << fVolumeNames[i] << "\": {\n";
        out << "      \"total_edep_eV\": " << std::setprecision(6) << fTotalEdep[i] / eV << ",\n";
        out << "      \"mean_edep_per_event_eV\": " << std::setprecision(6) << meanEdep / eV << ",\n";
        out << "      \"statistical_error_pct\": " << std::setprecision(4) << relError * 100.0 << "\n";
        out << "    }";
    }
    out << "\n  }\n";
    out << "}\n";
    out.close();
    G4cout << "Written: " << fname.str() << G4endl;
}

void CNTFETRunAction::WriteDosimetryJSON()
{
    std::ostringstream fname;
    fname << "geant4_dosimetry.json";
    std::ofstream out(fname.str());

    out << "{\n";
    out << "  \"simulation_type\": \"Co-60_gamma_dosimetry\",\n";
    out << "  \"device\": \"quasi-GAA-CNTFET\",\n";
    out << "  \"dielectric_config\": \"" << fDielectricConfig << "\",\n";
    out << "  \"cnt_chirality\": \"(19,0)\",\n";
    out << "  \"cnt_diameter_nm\": 1.49,\n";
    out << "  \"channel_length_nm\": 32.0,\n";
    out << "  \"num_events\": " << fNumEvents << ",\n";
    out << "  \"source\": {\n";
    out << "    \"type\": \"Co-60\",\n";
    out << "    \"gamma_energies_MeV\": [1.1732, 1.3325],\n";
    out << "    \"geometry\": \"collimated_beam_along_z\"\n";
    out << "  },\n";
    out << "  \"physics\": {\n";
    out << "    \"em_physics\": \"G4EmLivermorePhysics\",\n";
    out << "    \"production_cut_um\": 0.1\n";
    out << "  },\n";

    // Dielectric stack info
    out << "  \"dielectric_stack\": {\n";
    if (fDielectricConfig == "A") {
        out << "    \"layer1\": {\"material\": \"SiO2\", \"thickness_nm\": 10.0, \"eps_r\": 3.9},\n";
    } else if (fDielectricConfig == "B") {
        out << "    \"layer1\": {\"material\": \"HfO2\", \"thickness_nm\": 8.0, \"eps_r\": 25.0},\n";
    } else {
        out << "    \"layer1\": {\"material\": \"Al2O3\", \"thickness_nm\": 2.0, \"eps_r\": 9.0},\n";
        out << "    \"layer2\": {\"material\": \"HfO2\", \"thickness_nm\": 6.0, \"eps_r\": 25.0},\n";
    }
    out << "    \"gate_metal\": {\"material\": \"TiN\", \"thickness_nm\": 5.0}\n";
    out << "  },\n";

    // Dose results per volume
    out << "  \"dose_results\": {\n";
    bool first = true;
    for (G4int i = 0; i < kNumVolumes; ++i) {
        if (i == 2 && fDielectricConfig != "C") continue;

        G4double meanEdep = fTotalEdep[i] / fNumEvents;
        G4double meanEdep2 = fTotalEdep2[i] / fNumEvents;
        G4double variance = meanEdep2 - meanEdep * meanEdep;
        if (variance < 0) variance = 0;
        G4double relError = (meanEdep > 0) ?
            (std::sqrt(variance) / meanEdep) / std::sqrt(static_cast<double>(fNumEvents)) : 0.0;

        if (!first) out << ",\n";
        first = false;

        out << "    \"" << fVolumeNames[i] << "\": {\n";
        out << "      \"mean_edep_per_event_eV\": " << std::setprecision(6) << meanEdep / eV << ",\n";
        out << "      \"statistical_error_pct\": " << std::setprecision(4) << relError * 100.0 << "\n";
        out << "    }";
    }
    out << "\n  },\n";

    // TCAD coupling interface
    out << "  \"tcad_coupling\": {\n";
    out << "    \"comment\": \"Dose in dielectric per event. "
           "Use dose_per_fluence to compute trap density via Nbt(D) = Nbt0 + gamma_ox * D.\",\n";

    G4double cntR = 0.745 * nm;
    G4double halfL = 16.0 * nm;

    G4double diel1Outer = 0;
    if (fDielectricConfig == "A") diel1Outer = cntR + 10.0 * nm;
    else if (fDielectricConfig == "B") diel1Outer = cntR + 8.0 * nm;
    else diel1Outer = cntR + 2.0 * nm;

    G4double diel1Volume = CLHEP::pi * (diel1Outer * diel1Outer - cntR * cntR) * 2 * halfL;
    G4double diel1Density = 0;
    if (fDielectricConfig == "A") diel1Density = 2.32 * g / cm3;
    else if (fDielectricConfig == "B") diel1Density = 9.68 * g / cm3;
    else diel1Density = 3.95 * g / cm3;

    G4double diel1Mass = diel1Density * diel1Volume;
    G4double diel1MeanEdep = fTotalEdep[1] / fNumEvents;
    G4double diel1DosePerEvent = (diel1Mass > 0) ? diel1MeanEdep / diel1Mass / gray : 0;

    out << "    \"dielectric_layer1\": {\n";
    out << "      \"mean_dose_per_event_Gy\": " << std::setprecision(6) << diel1DosePerEvent << ",\n";
    out << "      \"mean_dose_per_event_rad\": " << std::setprecision(6) << diel1DosePerEvent * 100.0 << ",\n";
    out << "      \"volume_cm3\": " << std::setprecision(6) << diel1Volume / cm3 << ",\n";
    out << "      \"mass_g\": " << std::setprecision(6) << diel1Mass / g << "\n";
    out << "    }";

    if (fDielectricConfig == "C") {
        G4double diel2Inner = diel1Outer;
        G4double diel2Outer = diel2Inner + 6.0 * nm;
        G4double diel2Volume = CLHEP::pi * (diel2Outer * diel2Outer - diel2Inner * diel2Inner) * 2 * halfL;
        G4double diel2Density = 9.68 * g / cm3;
        G4double diel2Mass = diel2Density * diel2Volume;
        G4double diel2MeanEdep = fTotalEdep[2] / fNumEvents;
        G4double diel2DosePerEvent = (diel2Mass > 0) ? diel2MeanEdep / diel2Mass / gray : 0;

        out << ",\n    \"dielectric_layer2\": {\n";
        out << "      \"mean_dose_per_event_Gy\": " << std::setprecision(6) << diel2DosePerEvent << ",\n";
        out << "      \"mean_dose_per_event_rad\": " << std::setprecision(6) << diel2DosePerEvent * 100.0 << ",\n";
        out << "      \"volume_cm3\": " << std::setprecision(6) << diel2Volume / cm3 << ",\n";
        out << "      \"mass_g\": " << std::setprecision(6) << diel2Mass / g << "\n";
        out << "    }";
    }

    out << "\n  }\n";
    out << "}\n";
    out.close();
    G4cout << "Written: " << fname.str() << G4endl;
}
