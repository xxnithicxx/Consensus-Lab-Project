#!/bin/bash

# Run Hybrid consensus with network delays scenario
# Usage: ./run_hybrid_delays.sh [seed]

SEED=${1:-42}

echo "=================================="
echo "Running Hybrid with Network Delays"
echo "Seed: $SEED"
echo "=================================="

./scripts/start_network.sh hybrid delays $SEED

echo ""
echo "Hybrid + Network Delays scenario started"
echo "Monitor logs/node_*.log for detailed information"
echo "Use 'screen -list' to see running node sessions"
echo "Use 'screen -r node0' to attach to a specific node (node0-node4)"
echo "Expected behavior:"
echo "- Nodes will be selected as leaders based on stake"
echo "- Light PoW will be performed for each block"
echo "- Network delays may cause leader timeouts"
echo "- Stake-weighted chain selection will resolve conflicts"
