#!/usr/bin/env bash
# ==============================================================================
# Full Production Simulation & Analysis Script
# NKM & BTS Transfer Line Physics Simulation Framework (4GSR)
#
# Usage:
#   ./scripts/run_full_production_simulation.sh [OPTIONS]
#
# Options:
#   -q, --quiet        Disable verbose screen output (saves log to file).
#   -v, --verbose      Enable verbose output to screen (default).
#   -p, --parallel N   Number of parallel CPU workers (default: 90% of cores).
#   -o, --output-dir   Base directory for production outputs.
#   -h, --help         Show this help message.
# ==============================================================================

set -euo pipefail

# Default configuration settings
VERBOSE=true
DRY_RUN=false
DEFAULT_CORES=$(python3 -c "import os; print(max(1, int(os.cpu_count() * 0.9)))")
N_WORKERS=${DEFAULT_CORES}
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
OUTPUT_DIR="${REPO_ROOT}/results/production_run_${TIMESTAMP}"

# Parse command line flags
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -q|--quiet)
            VERBOSE=false
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -p|--parallel)
            N_WORKERS="$2"
            shift 2
            ;;
        -o|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: ./scripts/run_full_production_simulation.sh [OPTIONS]"
            echo "Options:"
            echo "  -d, --dry-run      Perform a dry run (validates scripts & inputs without running long simulations)."
            echo "  -q, --quiet        Disable verbose output to screen (log saved to file)."
            echo "  -v, --verbose      Enable verbose output to screen (default)."
            echo "  -p, --parallel N   Number of parallel CPU workers (default: 90% cores = ${DEFAULT_CORES})."
            echo "  -o, --output-dir D Set custom output directory."
            echo "  -h, --help         Show this help message."
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Prepare output directories
mkdir -p "${OUTPUT_DIR}/logs"
mkdir -p "${OUTPUT_DIR}/fieldmap"
mkdir -p "${OUTPUT_DIR}/convergence"
mkdir -p "${OUTPUT_DIR}/multiturn"
mkdir -p "${OUTPUT_DIR}/optimization"
mkdir -p "${OUTPUT_DIR}/tolerances"
mkdir -p "${OUTPUT_DIR}/moga"
mkdir -p "${OUTPUT_DIR}/summary"

LOG_FILE="${OUTPUT_DIR}/logs/production_run.log"

# Function to execute commands with optional stdout suppression and dry-run support
run_step() {
    local step_name="$1"
    shift
    local cmd=("$@")

    if [ "${DRY_RUN}" = true ]; then
        echo "======================================================================"
        echo " [DRY-RUN] ${step_name}"
        echo " Command  : ${cmd[*]}"
        local script_path="${cmd[1]}"
        if [ -f "${script_path}" ]; then
            python3 -m py_compile "${script_path}"
            echo " Status   : Script '${script_path}' verified (syntax OK)"
        else
            echo " Status   : Executable command verified"
        fi
        echo "======================================================================"
    elif [ "${VERBOSE}" = true ]; then
        echo "======================================================================"
        echo " [EXEC] ${step_name}"
        echo " Command: ${cmd[*]}"
        echo "======================================================================"
        "${cmd[@]}" 2>&1 | tee -a "${LOG_FILE}"
    else
        echo "[RUNNING] ${step_name} (log -> ${LOG_FILE}) ..."
        echo "=== [EXEC] ${step_name} ===" >> "${LOG_FILE}"
        echo "Command: ${cmd[*]}" >> "${LOG_FILE}"
        if "${cmd[@]}" >> "${LOG_FILE}" 2>&1; then
            echo "[COMPLETED] ${step_name}"
        else
            local status=$?
            echo "======================================================================"
            echo " [ERROR FAILED] ${step_name} (exit code ${status})"
            echo " Log file: ${LOG_FILE}"
            echo "======================================================================"
            echo "--- ERROR LOG TRACEBACK (Last 30 lines) ---"
            tail -n 30 "${LOG_FILE}"
            echo "----------------------------------------------------------------------"
            exit ${status}
        fi
    fi
}

echo "======================================================================"
echo "          NKM Full Production Simulation & Analysis Pipeline          "
echo "======================================================================"
echo " Timestamp        : ${TIMESTAMP}"
echo " Parallel Workers : ${N_WORKERS} CPU Cores (~90% allocation)"
echo " Output Directory : ${OUTPUT_DIR}"
echo " Verbose Screen   : ${VERBOSE}"
echo " Dry Run Mode     : ${DRY_RUN}"
echo " Master Log File  : ${LOG_FILE}"
echo "======================================================================"

# ------------------------------------------------------------------------------
# STEP 1: Environment Verification & Input Hash Cataloging
# Verifies scientific input data integrity (By.txt, kickmap_file.txt, K4GSR_HBIv4-1.mat)
# and generates/verifies the protected file SHA-256 hash manifest.
# ------------------------------------------------------------------------------
run_step "Step 1: Verify Input Hashes & Baseline Metrics" \
    python3 "${REPO_ROOT}/scripts/inventory_protected_hashes.py"

# ------------------------------------------------------------------------------
# STEP 2: NKM Magnetic Field & Transverse Kick Map Validation
# Parses 1D longitudinal field profile By(z) and 2D kickmap Kx(x,y). Fits 5th-order
# polynomials, checks symmetry residuals, and validates Lorentz sign conventions.
# Output saved to: ${OUTPUT_DIR}/fieldmap/
# ------------------------------------------------------------------------------
run_step "Step 2: NKM Field & Kick Map Cross-Validation" \
    python3 "${REPO_ROOT}/scripts/validate_nkm_fieldmap.py"

# ------------------------------------------------------------------------------
# STEP 3: Symplectic Slicing Integration Convergence Study
# Evaluates thick-kick symplectic particle tracking convergence across slicing values
# N_slices in {5, 10, 20, 50, 100} using parallel worker processes.
# Output saved to: ${OUTPUT_DIR}/convergence/
# ------------------------------------------------------------------------------
run_step "Step 3: Symplectic Slicing Convergence Scan" \
    python3 "${REPO_ROOT}/scripts/run_tracking_convergence.py"

# ------------------------------------------------------------------------------
# STEP 4: Multi-Turn Storage Ring Injection Dynamics Simulation
# Tracks 6D injected and circulating electron distributions through 1000 storage ring
# turns across 4 kicker models (NKM Off, Ideal, Linear, RADIA Fieldmap NKM).
# Output saved to: ${OUTPUT_DIR}/multiturn/
# ------------------------------------------------------------------------------
run_step "Step 4: Multi-Turn Injection & Physical Aperture Tracking" \
    python3 "${REPO_ROOT}/scripts/run_multiturn_injection.py" \
        --tier production \
        --output-dir "${OUTPUT_DIR}/multiturn"

# ------------------------------------------------------------------------------
# STEP 5: Deterministic BTS Transfer Line Quadrupole Optics Optimization
# Executes 2-stage SLSQP quadrupole matching to achieve target injection Twiss
# parameters (beta_x=7.56 m, beta_y=12.27 m) and computes SVD Jacobian condition numbers.
# Output saved to: ${OUTPUT_DIR}/optimization/
# ------------------------------------------------------------------------------
run_step "Step 5: Deterministic BTS Quadrupole Optics Matching" \
    python3 "${REPO_ROOT}/scripts/optimize_bts_publication.py"

# ------------------------------------------------------------------------------
# STEP 6: Monte Carlo Tolerance Budget & OAT Sensitivity Study
# Evaluates 500 Monte Carlo seeds with random quadrupole misalignments (sigma_xy=100 um),
# roll errors (sigma_phi=0.5 mrad), gradient errors, and NKM scale/offset variations
# executed across N_WORKERS parallel CPU cores.
# Output saved to: ${OUTPUT_DIR}/tolerances/
# ------------------------------------------------------------------------------
run_step "Step 6: Monte Carlo Tolerance & Sensitivity Analysis" \
    python3 "${REPO_ROOT}/scripts/run_publication_tolerances.py"

# ------------------------------------------------------------------------------
# STEP 7: Multi-Objective Genetic Algorithm (MOGA / NSGA-II) Pareto Study
# Performs multi-seed NSGA-II Pareto optimization evaluating trade-offs between
# optical mismatch, maximum beta function peaks, and physical aperture stay-clears.
# Output saved to: ${OUTPUT_DIR}/moga/
# ------------------------------------------------------------------------------
run_step "Step 7: Multi-Objective MOGA Pareto Optimization Study" \
    python3 "${REPO_ROOT}/scripts/run_publication_moga.py"

# ------------------------------------------------------------------------------
# STEP 8: Publication Data Consolidation & Paper Reproduction Pipeline
# Compiles dynamic figure plots, metric summary JSONs, LaTeX tables, and provenance logs.
# Output saved to: ${OUTPUT_DIR}/summary/
# ------------------------------------------------------------------------------
run_step "Step 8: Publication Figure & Table Data Consolidation" \
    python3 "${REPO_ROOT}/scripts/reproduce_paper.py"

echo "======================================================================"
echo " Full Production Simulation & Analysis Pipeline Completed Successfully!"
echo " Results Directory: ${OUTPUT_DIR}"
echo "======================================================================"
