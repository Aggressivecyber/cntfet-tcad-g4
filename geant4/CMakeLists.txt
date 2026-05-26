cmake_minimum_required(VERSION 3.16)
project(CNTFETDosimetry)

# Require C++17
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Geant4
find_package(Geant4 REQUIRED)

# Include directories
include_directories(
    ${CMAKE_SOURCE_DIR}/include
    ${Geant4_INCLUDE_DIRS}
)

# Source files
set(SOURCES
    src/cntfet_dosimetry.cc
    src/CNTFETDetectorConstruction.cc
    src/CNTFETPhysicsList.cc
    src/CNTFETPrimaryGeneratorAction.cc
    src/CNTFETRunAction.cc
    src/CNTFETEventAction.cc
    src/CNTFETSteppingAction.cc
    src/CNTFETActionInitialization.cc
)

# Build executable
add_executable(cntfet_dosimetry ${SOURCES})

# Link with Geant4 libraries
target_link_libraries(cntfet_dosimetry
    ${Geant4_LIBRARIES}
)

# Copy macros to build directory
file(COPY ${CMAKE_SOURCE_DIR}/input/ DESTINATION ${CMAKE_BINARY_DIR}/input/)

# Install Geant4 data files hooks (optional)
include(${Geant4_USE_FILE})
