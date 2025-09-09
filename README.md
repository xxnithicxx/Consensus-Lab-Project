# Blockchain Simulator Project

A comprehensive blockchain simulator implementing Proof of Work (PoW) and Hybrid consensus mechanisms with socket-based network communication.

## Project Overview

This project simulates blockchain networks with different consensus algorithms under various network conditions to study their behavior, particularly focusing on:

- **Finality properties** under network delays and partitions
- **Fork resolution** mechanisms
- **Consensus safety** and liveness properties
- **Performance comparison** between PoW and Hybrid consensus
- **Real network communication** using TCP sockets

The simulator runs multiple blockchain nodes as separate processes, communicating via TCP sockets to create a realistic distributed network environment.

## Project Architecture

### Directory Structure

```
blockchain-simulator/
├── src/
│   ├── core/                 # Core blockchain components
│   │   ├── block.py         # Block structure and validation
│   │   ├── transaction.py   # Transaction handling and validation
│   │   ├── blockchain.py    # Blockchain state management
│   │   └── crypto.py        # Cryptographic functions (hashing, signatures)
│   ├── consensus/           # Consensus algorithm implementations
│   │   ├── base.py         # Base consensus interface and common methods
│   │   ├── pow.py          # Proof of Work implementation
│   │   └── hybrid.py       # Hybrid consensus (stake + light PoW)
│   ├── network/            # Network communication layer
│   │   ├── socket_node.py  # Socket-based node implementation
│   │   ├── socket_network.py # TCP socket network layer
│   │   └── messages.py     # Message types and serialization
│   └── simulator/          # Simulation orchestration
│       ├── simulator.py    # Main simulation engine
│       └── scenarios.py    # Network scenario implementations
├── scripts/                # Execution and utility scripts
│   ├── run_*.sh           # Main simulation runners
│   ├── demo_*.sh          # Demo scripts with predefined seeds
│   ├── start_network.sh   # Manual network startup
│   └── utils/             # Utility scripts
│       ├── cleanup.sh     # Process cleanup
│       ├── screen_manager.sh # Screen session management
│       └── setup_terminals.sh # Terminal setup
├── config/                 # Configuration files
│   ├── pow_config.json    # PoW consensus parameters
│   ├── hybrid_config.json # Hybrid consensus parameters
│   └── network_config.json # Network topology configuration
├── logs/                   # Runtime logs (generated)
│   └── node_*.log         # Individual node logs
├── main.py                 # Entry point for individual nodes
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

The simulator creates a 5-node blockchain network with the following configuration:

| Node ID | TCP Port | Screen Session | Log File |
|---------|----------|----------------|----------|
| 0 | 9000 | consensus_node_0 | logs/node_0.log |
| 1 | 9001 | consensus_node_1 | logs/node_1.log |
| 2 | 9002 | consensus_node_2 | logs/node_2.log |
| 3 | 9003 | consensus_node_3 | logs/node_3.log |
| 4 | 9004 | consensus_node_4 | logs/node_4.log |

### Communication Protocol
- **Real TCP sockets** for inter-node communication
- Each node runs as an independent process
- Realistic network delays and partitions
- JSON-based message protocol
- Supports distributed deployment across machines

## Consensus Algorithms

### 1. Proof of Work (PoW)
- **Chain Selection**: Longest chain rule
- **Mining**: Hash puzzle with adjustable difficulty
- **Finality**: k-deep confirmation (k=4)
- **Fork Resolution**: Longest valid chain wins

### 2. Hybrid Consensus
- **Leader Selection**: Stake-weighted deterministic selection
- **Light PoW**: Lightweight proof of work for each block
- **Chain Selection**: Highest cumulative stake-weight
- **Finality**: k-deep confirmation with stake consideration

## Network Scenarios

### Scenario 1: Network Delays
- Simulates realistic network delays (50-200ms)
- Tests consensus behavior under normal network conditions
- Validates fork resolution mechanisms

### Scenario 2: Partition & Heal
- Creates network partition (2-3 node split)
- Tests consensus behavior during network splits
- Validates chain reorganization after healing

## System Requirements

### Prerequisites
- **Python 3.8+** (tested with Python 3.8-3.11)
- **Linux environment** (Ubuntu 18.04+ recommended)
- **Screen utility** - **REQUIRED for running simulations**
- **TCP ports 9000-9004** must be available
- Basic understanding of blockchain concepts

### Critical Dependency: Screen
This project **requires** the `screen` utility to manage multiple terminal sessions for each blockchain node. Each node runs in its own screen session for proper isolation and monitoring.

#### Installing Screen
**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install screen
```

**CentOS/RHEL/Fedora:**
```bash
# CentOS/RHEL
sudo yum install screen

# Fedora
sudo dnf install screen
```

**Verify Screen Installation:**
```bash
screen --version
# Should output: Screen version 4.xx.xx
```

## Quick Start Guide

### Step 1: Clone and Setup
```bash
# Clone the repository
git clone <repository-url>
cd blockchain-simulator

# Install Python dependencies
pip install -r requirements.txt

# Make all scripts executable
chmod +x scripts/*.sh scripts/utils/*.sh
```

### Step 2: Verify Prerequisites
```bash
# Check Python version
python3 --version

# Verify screen is installed
screen --version

# Check if ports are available
netstat -tuln | grep -E ':(9000|9001|9002|9003|9004)'
# Should return empty (no output means ports are free)
```

### Step 3: Run Your First Simulation

#### Option A: PoW Consensus with Network Delays
```bash
./scripts/run_pow_delays.sh 42
```

#### Option B: Hybrid Consensus with Network Partition
```bash
./scripts/run_hybrid_partition.sh 42
```

The simulation will:
1. Start 5 blockchain nodes in separate screen sessions
2. Create a distributed network with TCP communication
3. Run the selected consensus algorithm
4. Simulate network conditions (delays or partitions)
5. Generate logs in the `logs/` directory

### Step 4: Monitor the Simulation
While the simulation runs, you can monitor progress:

```bash
# View all screen sessions
screen -ls

# Attach to a specific node (e.g., node 0)
screen -r consensus_node_0

# Detach from screen session (while attached)
# Press: Ctrl+A, then D

# View real-time logs
tail -f logs/node_0.log
```

## Available Simulations

The simulator provides four main simulation scenarios. All simulations use a random seed for reproducible results.

### 1. PoW with Network Delays
Simulates Proof of Work consensus under realistic network delays (50-200ms).
```bash
./scripts/run_pow_delays.sh [seed]

# Example with specific seed
./scripts/run_pow_delays.sh 12345
```

### 2. PoW with Network Partition & Heal
Tests PoW consensus during network partitions and recovery.
```bash
./scripts/run_pow_partition.sh [seed]

# Example with specific seed
./scripts/run_pow_partition.sh 67890
```

### 3. Hybrid Consensus with Network Delays
Simulates Hybrid consensus (stake + light PoW) under network delays.
```bash
./scripts/run_hybrid_delays.sh [seed]

# Example with specific seed
./scripts/run_hybrid_delays.sh 11111
```

### 4. Hybrid Consensus with Network Partition & Heal
Tests Hybrid consensus during network partitions and recovery.
```bash
./scripts/run_hybrid_partition.sh [seed]

# Example with specific seed
./scripts/run_hybrid_partition.sh 22222
```

### Manual Network Control
For advanced users who want to manually start and control the network:

```bash
# Start network manually with specific parameters
./scripts/start_network.sh <consensus_type> <scenario_type> <seed>

# Examples
./scripts/start_network.sh pow delays 42
./scripts/start_network.sh hybrid partition 123
```

### Single Node Testing
Run a single node for debugging or testing:

```bash
python main.py --node-id 0 --consensus pow --scenario delays --seed 42
```

## Understanding the Output

### Screen Sessions
Each simulation creates 5 screen sessions (one per node):
- `consensus_node_0` - Node 0
- `consensus_node_1` - Node 1  
- `consensus_node_2` - Node 2
- `consensus_node_3` - Node 3
- `consensus_node_4` - Node 4

### Log Files
Each node generates detailed logs in `logs/node_X.log`:
```bash
# Monitor specific node
tail -f logs/node_0.log

# Monitor all nodes simultaneously
tail -f logs/node_*.log
```

### Simulation Duration
- Most simulations run for **30 seconds** by default
- Network partition scenarios include healing phases
- Logs continue until all nodes properly shut down

## Network Topology

### Node Configuration

## Advanced Usage

### Custom Configuration

#### Modifying PoW Parameters
Edit `config/pow_config.json`:
```json
{
    "difficulty": 4,           # Mining difficulty (higher = slower)
    "block_time_ms": 500,      # Target block time in milliseconds
    "finality_depth": 4,       # Blocks deep for finality
    "initial_balances": [1000, 1000, 1000, 1000, 1000]  # Starting balances
}
```

#### Modifying Hybrid Parameters  
Edit `config/hybrid_config.json`:
```json
{
    "light_difficulty": 2,     # Light PoW difficulty
    "block_time_ms": 300,      # Target block time in milliseconds  
    "stakes": [200, 300, 150, 250, 100],  # Stake distribution
    "leader_timeout_ms": 1000  # Leader selection timeout
}
```

### Running Custom Scenarios

#### Extended Simulation Duration
```bash
# Modify simulation time in scripts (default: 30 seconds)
# Edit the script files and change SIMULATION_TIME variable
```

#### Custom Network Delays
```bash
# Run with custom parameters
python main.py --node-id 0 --consensus pow --scenario delays \
    --seed 42 --simulation-time 60 --delay-range 100-500
```

### Monitoring and Analysis

#### Real-time Dashboard (Terminal-based)
```bash
# Monitor all nodes simultaneously
watch -n 1 'tail -5 logs/node_*.log | grep -E "(block_created|finalized)"'

# Monitor network activity
watch -n 1 'netstat -tuln | grep -E ":(9000|9001|9002|9003|9004)"'
```

#### Log Analysis Scripts
```bash
# Extract block creation events
grep "block_created" logs/node_*.log > block_creation_analysis.txt

# Analyze finality patterns
grep "finalized" logs/node_*.log | sort -k1 > finality_timeline.txt

# Network partition detection
grep "partition" logs/node_*.log > partition_events.txt
```

### Testing and Validation

#### Reproducible Testing
```bash
# Always use the same seed for reproducible results
./scripts/run_pow_delays.sh 12345
./scripts/run_pow_delays.sh 12345  # Same results

# Test different seeds
for seed in 100 200 300 400 500; do
    echo "Testing with seed $seed"
    ./scripts/run_pow_delays.sh $seed
    sleep 5  # Wait between tests
done
```

#### Integration Testing
```bash
# Run all simulation types with known seeds
./scripts/run_pow_delays.sh 1001
./scripts/run_pow_partition.sh 1002  
./scripts/run_hybrid_delays.sh 1003
./scripts/run_hybrid_partition.sh 1004
```

#### Performance Testing
```bash
# Measure simulation performance
time ./scripts/run_pow_delays.sh 42

# Monitor resource usage during simulation
htop  # In a separate terminal while simulation runs
```

## Key Features

### Invariant Checking
- **Finality Consistency**: No two different blocks final at same height
- **Chain Progression**: Final height only increases
- **No Double-Spending**: Validated in final chains

### Logging & Monitoring
- Structured JSON logging for each node
- Real-time blockchain state monitoring
- Network event tracking
- Performance metrics collection

### Deterministic Behavior
- Seed-based randomization for reproducible results
- Deterministic leader selection in Hybrid consensus
- Consistent network delay patterns

## Implementation Details

### Block Structure
```python
class Block:
    - height: int
    - prev_hash: str
    - transactions: List[Transaction]
    - timestamp: float
    - nonce: int
    - hash: str
```

### Consensus Interface
```python
class ConsensusAlgorithm:
    - can_propose_block()
    - create_block()
    - validate_block()
    - select_best_chain()
```

### Network Simulation
- Message-based communication
- Configurable delays and partitions
- Realistic network behavior simulation

## Testing

### Unit Tests
```bash
cd tests
python -m pytest
```

### Integration Tests
```bash
# Test with known seeds for reproducibility
./scripts/run_pow_delays.sh 12345
./scripts/run_hybrid_partition.sh 67890
```

## Log Analysis

Logs are stored in `logs/node_*.log` with structured format:

```json
{
    "timestamp": 1234567890.123,
    "node_id": "0",
    "event_type": "block_created",
    "data": {
        "height": 5,
        "hash": "0000abc...",
        "transactions": 3
    }
}
```

## Performance Metrics

The simulator tracks:
- Block creation time
- Fork frequency
- Finality delays
- Network message overhead
- Chain reorganization events

## Troubleshooting

### Common Issues and Solutions

#### 1. Screen Not Found
**Error**: `screen: command not found`
**Solution**: Install screen utility
```bash
# Ubuntu/Debian
sudo apt-get install screen

# CentOS/RHEL
sudo yum install screen

# Fedora
sudo dnf install screen
```

#### 2. Permission Denied on Scripts
**Error**: `Permission denied` when running scripts
**Solution**: Make scripts executable
```bash
chmod +x scripts/*.sh scripts/utils/*.sh
```

#### 3. Port Already in Use
**Error**: `Address already in use` or port conflicts
**Solution**: Kill existing processes and clean up
```bash
# Kill processes using ports 9000-9004
sudo lsof -ti:9000-9004 | xargs sudo kill -9

# Or use the cleanup script
./scripts/utils/cleanup.sh
```

#### 4. Module Not Found
**Error**: `ModuleNotFoundError: No module named 'src'`
**Solution**: Ensure you're in the correct directory
```bash
# Make sure you're in the project root
pwd
# Should show: /path/to/blockchain-simulator

# Check if src directory exists
ls -la src/
```

#### 5. Screen Sessions Not Starting
**Error**: Nodes not appearing in screen sessions
**Solution**: Check screen configuration and permissions
```bash
# List current screen sessions
screen -ls

# Check if screen is working
screen -S test_session
# Exit with: Ctrl+A, then D

# Kill test session
screen -S test_session -X quit
```

#### 6. Simulation Hangs or Doesn't Complete
**Solution**: Clean up and restart
```bash
# Clean up any remaining processes
./scripts/utils/cleanup.sh

# Check for hanging screen sessions
screen -ls

# Kill all consensus-related screen sessions
screen -ls | grep consensus | cut -d. -f1 | xargs -I {} screen -S {} -X quit
```

### Debug Mode
Run individual nodes with debug logging:
```bash
python main.py --node-id 0 --consensus pow --scenario delays --seed 42 --log-level DEBUG
```

### Viewing Detailed Logs
```bash
# Real-time monitoring of all nodes
tail -f logs/node_*.log

# Search for specific events
grep "block_created" logs/node_*.log
grep "ERROR" logs/node_*.log

# View simulation summary
grep "simulation_summary" logs/node_*.log
```

### Network Connectivity Test
```bash
# Test if ports are accessible
telnet localhost 9000
# Should connect if node 0 is running

# Check listening ports
netstat -tuln | grep -E ':(9000|9001|9002|9003|9004)'
```

## Simulation Lifecycle

### Starting a Simulation
1. **Initialization**: Scripts create screen sessions for each node
2. **Network Setup**: Nodes start TCP servers and establish connections
3. **Consensus Start**: Nodes begin block creation and validation
4. **Scenario Execution**: Network conditions are applied (delays/partitions)
5. **Monitoring**: Real-time logging and state tracking
6. **Completion**: Automatic cleanup after simulation time expires

### Stopping a Simulation
Most simulations auto-complete, but you can manually stop them:

```bash
# Graceful shutdown - kills all consensus node processes
./scripts/utils/cleanup.sh

# Force kill all screen sessions
screen -ls | grep consensus | cut -d. -f1 | xargs -I {} screen -S {} -X quit

# Emergency cleanup - kill all processes on consensus ports
sudo lsof -ti:9000-9004 | xargs sudo kill -9
```

### Post-Simulation Analysis
After completion, analyze results:

```bash
# View simulation summary
grep "Simulation completed" logs/node_*.log

# Check final blockchain states
grep "final.*height" logs/node_*.log

# Analyze consensus metrics
grep -E "(blocks_created|forks_resolved|finality_time)" logs/node_*.log
```

## Educational Value

This simulator demonstrates key blockchain concepts:

- **Distributed Consensus**: How nodes agree on blockchain state
- **Network Partitions**: Byzantine fault tolerance in practice  
- **Fork Resolution**: How different consensus algorithms handle conflicts
- **Finality**: When transactions become irreversible
- **Performance Trade-offs**: Security vs. speed in different algorithms

Perfect for:
- Blockchain course assignments
- Research into consensus algorithms
- Understanding distributed systems
- Experimenting with network conditions

## Contributing and Development

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt pytest black flake8

# Run code formatting
black src/ --line-length 88

# Run linting
flake8 src/ --max-line-length 88

# Run tests
python -m pytest test_consensus_integration.py -v
```

### Adding New Consensus Algorithms
1. Extend `src/consensus/base.py`
2. Implement required methods
3. Add configuration file
4. Create test scenarios
5. Update scripts and documentation

### Extending Network Scenarios
1. Modify `src/simulator/scenarios.py`
2. Add new scenario types
3. Update scripts to support new scenarios
4. Test with various seeds

## License and Citation

This project is for educational and research purposes. 

When using this simulator for research or academic work, please cite:
```
Blockchain Consensus Simulator
A multi-algorithm blockchain simulator with network condition testing
[Year] [Institution/Author]
```

## Support and Community

- **Issues**: Create GitHub issues for bugs or feature requests
- **Documentation**: This README and inline code comments
- **Examples**: See `scripts/demo_*.sh` for working examples
- **Logs**: Check `logs/` directory for detailed execution traces

**Happy simulating! 🔗⛓️**
