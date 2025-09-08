#!/bin/bash

# Run Hybrid consensus with partition & heal scenario
# Usage: ./run_hybrid_partition.sh [seed]

SEED=${1:-42}

echo "=================================="
echo "Running Hybrid with Partition & Heal"
echo "Seed: $SEED"
echo "=================================="

./scripts/start_network.sh hybrid partition $SEED

echo ""
echo "Hybrid + Partition & Heal scenario started"
echo "Monitor logs/node_*.log for detailed information"
echo "Use 'screen -list' to see running node sessions"
echo "Use 'screen -r node0' to attach to a specific node (node0-node4)"
echo "Expected behavior:"
echo "- Network will be partitioned into 2 groups"
echo "- Each partition will select leaders independently"
echo "- Different chains will develop in each partition"
echo "- After healing, highest stake-weight chain wins"
