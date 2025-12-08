#!/bin/bash
# ============================================================
# Network Anomaly Evaluation - Environment Initialization
# ============================================================
# Usage: source init.sh
# ============================================================

# ─────────────────────────────────────────────────────────────
# 1. Environment Variables
# ─────────────────────────────────────────────────────────────

export PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export NETWORK_DIR="${PROJECT_ROOT}/network"
export RESULTS_DIR="${NETWORK_DIR}/results"
export SCRIPTS_DIR="${NETWORK_DIR}/scripts"

# ─────────────────────────────────────────────────────────────
# 2. System Check
# ─────────────────────────────────────────────────────────────

check_mininet() {
    if command -v mn &> /dev/null; then
        echo "✅ Mininet is installed: $(mn --version 2>&1 | head -1)"
        return 0
    else
        echo "❌ Mininet not found. Install with:"
        echo "    sudo apt install mininet"
        return 1
    fi
}

check_tools() {
    local missing=()
    
    command -v iperf3 &> /dev/null || missing+=("iperf3")
    command -v tc &> /dev/null || missing+=("iproute2")
    command -v curl &> /dev/null || missing+=("curl")
    command -v python3 &> /dev/null || missing+=("python3")
    
    if [ ${#missing[@]} -eq 0 ]; then
        echo "✅ All required tools installed"
    else
        echo "❌ Missing tools: ${missing[*]}"
        echo "    sudo apt install ${missing[*]}"
    fi
}

# ─────────────────────────────────────────────────────────────
# 3. Summary
# ─────────────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "📁 Network Anomaly Evaluation - Environment"
echo "───────────────────────────────────────────────────────────"
echo "  Project:      ${PROJECT_ROOT}"
echo "  Scripts:      ${SCRIPTS_DIR}"
echo "  Results:      ${RESULTS_DIR}"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check OS
if [[ "$(uname)" == "Linux" ]]; then
    check_mininet
    check_tools
else
    echo "⚠️  Mininet requires Linux. Current OS: $(uname)"
    echo "    Options:"
    echo "    1. Use Ubuntu VM (VirtualBox/VMware)"
    echo "    2. Use Docker with Linux container"  
    echo "    3. Use WSL2 on Windows"
fi

echo ""
echo "💡 Quick Commands:"
echo "    sudo mn --topo single,2           # Test topology"
echo "    sudo python3 run_baseline.py      # Run baseline"
echo ""
