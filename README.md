# Blockchain Simulator Project

A comprehensive blockchain simulator implementing Proof of Work (PoW) and Hybrid consensus mechanisms with socket-based network communication.

## Project Overview

This project simulates blockchain networks with different consensus algorithms under various network conditions to study their behavior, particularly focusing on:

- **Finality properties** under network delays and partitions
- **Fork resolution** mechanisms
- **Consensus safety** and liveness properties
- **Performance comparison** between PoW and Hybrid consensus
- **Real network communication** using TCP sockets

## Architecture

### Directory Structure

```
blockchain-simulator/
├── src/
│   ├── core/                 # Core blockchain components
│   │   ├── block.py         # Block structure
│   │   ├── transaction.py   # Transaction handling
│   │   ├── blockchain.py    # Blockchain logic
│   │   └── crypto.py        # Cryptographic functions
│   ├── consensus/           # Consensus algorithms
│   │   ├── base.py         # Base consensus interface
│   │   ├── pow.py          # Proof of Work
│   │   └── hybrid.py       # Hybrid consensus
│   ├── network/            # Network communication
│   │   ├── socket_node.py  # Socket-based node implementation
│   │   ├── socket_network.py # TCP socket network layer
│   │   └── messages.py     # Message types
│   └── simulator/          # Main simulation logic
│       ├── simulator.py    # Main simulator
│       └── scenarios.py    # Test scenarios
├── scripts/                # Execution scripts
├── config/                 # Configuration files
├── logs/                   # Log output
├── main.py                 # Entry point for socket-based nodes
└── requirements.txt        # Dependencies
```

## Network Communication

This simulator uses **TCP sockets** for real inter-process communication between nodes:

- Each node runs as a separate process
- Nodes communicate via TCP sockets on ports 9000-9004
- Real network delays and partitions can be simulated
- Supports distributed execution across multiple machines

### Node Ports
- Node 0: `localhost:9000`
- Node 1: `localhost:9001`
- Node 2: `localhost:9002`
- Node 3: `localhost:9003`
- Node 4: `localhost:9004`

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

## Quick Start

### Prerequisites
- Python 3.8+
- Linux environment with screen utility
- TCP ports 9000-9004 available
- Basic understanding of blockchain concepts

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd blockchain-simulator

# Install dependencies (minimal requirements)
pip install -r requirements.txt

# Make scripts executable
chmod +x scripts/*.sh
chmod +x scripts/utils/*.sh
```

### Running Simulations

#### 1. PoW with Network Delays
```bash
./scripts/run_pow_delays.sh [seed]
```

#### 2. PoW with Partition & Heal
```bash
./scripts/run_pow_partition.sh [seed]
```

#### 3. Hybrid with Network Delays
```bash
./scripts/run_hybrid_delays.sh [seed]
```

#### 4. Hybrid with Partition & Heal
```bash
./scripts/run_hybrid_partition.sh [seed]
```

### Manual Execution

```bash
# Start network manually
./scripts/start_network.sh <consensus_type> <scenario_type> <seed>

# Example
./scripts/start_network.sh pow delays 42
```

### Single Node Testing

```bash
python main.py --node-id 0 --consensus pow --scenario delays --seed 42
```

## Configuration

### PoW Configuration (`config/pow_config.json`)
```json
{
    "difficulty": 4,
    "block_time_ms": 500,
    "finality_depth": 4,
    "initial_balances": [1000, 1000, 1000, 1000, 1000]
}
```

### Hybrid Configuration (`config/hybrid_config.json`)
```json
{
    "light_difficulty": 2,
    "block_time_ms": 300,
    "stakes": [200, 300, 150, 250, 100],
    "leader_timeout_ms": 1000
}
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

### Common Issues

1. **Terminal not opening**: Ensure gnome-terminal is installed
2. **Permission denied**: Run `chmod +x scripts/*.sh`
3. **Module not found**: Ensure you're in the project directory
4. **Port conflicts**: Each node uses different log files

### Debug Mode

```bash
python main.py --node-id 0 --consensus pow --scenario delays --log-level DEBUG
```

## Future Enhancements

- [ ] Web-based visualization interface
- [ ] Additional consensus algorithms (PBFT, PoS)
- [ ] Byzantine fault simulation
- [ ] Performance optimization
- [ ] Real-time metrics dashboard

## Contributing

1. Fork the repository
2. Create feature branch
3. Implement changes with tests
4. Submit pull request

## License

This project is for educational purposes. See LICENSE file for details.

## Contact

For questions or issues, please create an issue in the repository.
