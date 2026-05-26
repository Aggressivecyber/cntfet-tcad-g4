#!/bin/bash
SLUG="20260427-034614-CNTFET-6T-SRAM-TID-Radiation-Multi-Scale-Simulatio"
BASE="/root/projects/sim-lab/${SLUG}/workspace/tcad/exploration/20260427-081845-trial-execute-batch1"

for T in T2 T3 T4 T5 T6 T7 T8 T9; do
    TDIR="${BASE}/${T}"
    echo "[$(date +%H:%M:%S)] Starting ${T}..."
    docker exec -w "${TDIR}" tcad-sentaurus bash -c \
        "source /etc/profile.d/synopsys.sh && \
         DATEX=\${PWD}/datexcodes.txt && \
         sdevice input/sdevice_${T}.cmd" \
        > "${TDIR}/logs/sdevice_${T}.log" 2>&1 &
    PID=$!
    echo "  PID=${PID}"
done

echo "Waiting for all trials..."
wait
echo "All done at $(date)"
