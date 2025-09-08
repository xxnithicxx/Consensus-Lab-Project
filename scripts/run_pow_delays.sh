#!/bin/bash

# Run Proof of Work with network delays scenario
# Usage: ./run_pow_delays.sh [seed]

SEED=${1:-42}
DURATION=30  # Default simulation duration in seconds

echo "=================================="
echo "Running PoW with Network Delays"
echo "Seed: $SEED"
echo "Duration: ${DURATION}s"
echo "=================================="

# Start the network (TCP socket-based multi-process architecture)
./scripts/start_network.sh pow delays $SEED

echo ""
echo "PoW + Network Delays scenario started"
echo "Monitor logs/node_*.log for detailed information"
echo "Use 'screen -list' to see running node sessions"
echo "Use 'screen -r node0' to attach to node 0 (or node1-4)"
echo "Expected behavior:"
echo "- Nodes will mine blocks competitively"
echo "- Network delays will cause occasional forks"
echo "- Longest chain rule will resolve forks"
echo "- Final blocks should be consistent across nodes"
echo ""

# Wait a moment for nodes to start
sleep 2

# Monitor simulation progress
echo "Monitoring simulation progress..."
echo "Press Ctrl+C to stop monitoring (simulation will continue in background)"

START_TIME=$(date +%s)
LAST_LOG_SIZE=0

while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    REMAINING=$((DURATION - ELAPSED))
    
    # Check if any node sessions are still running
    RUNNING_NODES=$(screen -list | grep -c "node[0-4]" || true)
    
    if [ $RUNNING_NODES -eq 0 ]; then
        echo "All node sessions have completed."
        break
    fi
    
    if [ $REMAINING -le 0 ]; then
        echo "Simulation time elapsed (${DURATION}s), waiting for nodes to finish..."
        # Give nodes a few more seconds to complete cleanup
        sleep 5
        RUNNING_NODES=$(screen -list | grep -c "node[0-4]" || true)
        if [ $RUNNING_NODES -eq 0 ]; then
            break
        fi
    fi
    
    # Show progress
    if [ $REMAINING -gt 0 ]; then
        printf "\rSimulation running... Elapsed: %ds, Remaining: %ds, Status: %s" $ELAPSED $REMAINING $([ $RUNNING_NODES -gt 0 ] && echo "Running" || echo "Stopped")
    else
        printf "\rWaiting for simulation to complete... Status: %s" $([ $RUNNING_NODES -gt 0 ] && echo "Running" || echo "Stopped")
    fi
    
    sleep 1
done

echo ""
echo ""
echo "=================================="
echo "Simulation Complete!"
echo "=================================="

# Show final results
if [ -f logs/node_0.log ]; then
    echo "Final blockchain state from node 0:"
    tail -10 logs/node_0.log | grep "Blockchain state" | tail -1 | sed 's/.*Blockchain state: /  /'
    
    echo ""
    echo "Total simulation time:"
    TOTAL_TIME=$(tail -20 logs/node_0.log | grep "Simulation completed after" | tail -1 | sed 's/.*after /  /' | sed 's/ seconds/s/')
    if [ -n "$TOTAL_TIME" ]; then
        echo "  $TOTAL_TIME"
    else
        echo "  Information not available"
    fi
    
    echo ""
    echo "Log files available in logs/ directory:"
    ls -la logs/node_*.log | awk '{print "  " $9 " (" $5 " bytes)"}'
else
    echo "Warning: No log files found. Check if simulation ran successfully."
fi

echo ""
echo "Use 'tail -f logs/node_0.log' to see detailed logs from node 0"
echo "Use 'grep \"EVENT:\" logs/node_*.log' to see all blockchain events"
