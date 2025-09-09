#!/bin/bash

# Demo script for Hybrid consensus with presentation-friendly logging
# Usage: ./demo_hybrid_presentation.sh [seed]

SEED=${1:-42}

echo "=========================================="
echo "HYBRID CONSENSUS - PRESENTATION MODE DEMO"
echo "=========================================="
echo "Seed: $SEED"
echo "Log Mode: Presentation (Easy to read)"
echo "Duration: 30 seconds"
echo "Scenario: Network delays"
echo ""

# Clean up any previous runs
./scripts/utils/cleanup.sh

echo "Starting 5-node Hybrid consensus network..."
echo "Expected behavior:"
echo "🎯 Stake-weighted leader selection"
echo "⚡ Light PoW mining"
echo "✅ Block validation and propagation"
echo "⚖️ Chain selection by stake weight"
echo ""

# Start network with presentation logging
python main.py --node-id 0 --consensus hybrid --scenario delays --seed $SEED --config-dir config &
NODE0_PID=$!

python main.py --node-id 1 --consensus hybrid --scenario delays --seed $SEED --config-dir config &
NODE1_PID=$!

python main.py --node-id 2 --consensus hybrid --scenario delays --seed $SEED --config-dir config &
NODE2_PID=$!

python main.py --node-id 3 --consensus hybrid --scenario delays --seed $SEED --config-dir config &
NODE3_PID=$!

python main.py --node-id 4 --consensus hybrid --scenario delays --seed $SEED --config-dir config &
NODE4_PID=$!

echo "Network started. Monitoring Node 0 output..."
echo "Press Ctrl+C to stop monitoring (simulation will continue)"
echo ""

# Monitor the first node's output for demo
wait $NODE0_PID

echo ""
echo "Demo completed! Check logs/node_*.log for detailed information."
