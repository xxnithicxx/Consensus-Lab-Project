#!/bin/bash

# Run Proof of Work with partition & heal scenario
# Usage: ./run_pow_partition.sh [seed]

SEED=${1:-42}

echo "=================================="
echo "Running PoW with Partition & Heal"
echo "Seed: $SEED"
echo "=================================="

./scripts/start_network.sh pow partition $SEED

echo ""
echo "PoW + Partition & Heal scenario started"
echo "Monitor logs/node_*.log for detailed information"
echo "Use 'screen -list' to see running node sessions"
echo "Use 'screen -r node0' to attach to a specific node (node0-node4)"
echo "Expected behavior:"
echo "- Network will be partitioned into 2 groups"
echo "- Each partition will develop separate chains"
echo "- After healing, longest chain wins"
echo "- Some blocks may be reorganized"
