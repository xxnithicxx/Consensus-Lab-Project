import sys
import os
import argparse
import json
import time
import logging
import signal

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.network.socket_node import SocketNode


def parse_arguments():
    """
    Parse command line arguments
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Socket-based Blockchain Node')
    
    parser.add_argument('--node-id', type=int, required=True,
                        help='Unique identifier for this node (0-4)')
    
    parser.add_argument('--consensus', choices=['pow', 'hybrid'], required=True,
                        help='Consensus algorithm to use')
    
    parser.add_argument('--scenario', choices=['delays', 'partition'], required=True,
                        help='Test scenario to run')
    
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for deterministic behavior')
    
    parser.add_argument('--config-dir', type=str, default='config',
                        help='Directory containing configuration files')
    
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        default='INFO', help='Logging level')
    
    parser.add_argument('--duration', type=int, default=30,
                        help='Simulation duration in seconds')
    
    return parser.parse_args()


def load_config(consensus_type: str, config_dir: str) -> dict:
    """
    Load configuration for the specified consensus type
    
    Args:
        consensus_type: Type of consensus algorithm
        config_dir: Directory containing config files
        
    Returns:
        dict: Configuration parameters
    """
    config_file = os.path.join(config_dir, f"{consensus_type}_config.json")
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Also load network config
        network_config_file = os.path.join(config_dir, "network_config.json")
        with open(network_config_file, 'r') as f:
            network_config = json.load(f)
        
        config['network'].update(network_config)
        
        return config
        
    except FileNotFoundError:
        print(f"Error: Configuration file {config_file} not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in configuration file {config_file}")
        sys.exit(1)


def setup_logging(node_id: int, log_level: str):
    """
    Setup logging for this node
    
    Args:
        node_id: ID of this node
        log_level: Logging level
    """
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Setup logging
    log_file = f'logs/node_{node_id}.log'
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(f'node_{node_id}')
    logger.info(f"Starting socket-based blockchain node {node_id}")
    
    return logger


class SocketSimulator:
    """
    Socket-based simulator for a single node
    """
    
    def __init__(self, node_id: str, consensus_type: str, scenario_type: str, 
                 seed: int, config: dict):
        self.node_id = node_id
        self.consensus_type = consensus_type
        self.scenario_type = scenario_type
        self.seed = seed
        self.config = config
        self.duration = config.get('simulation', {}).get('duration_seconds', 30)
        
        # Create the socket node
        initial_balances = config.get('initial_balances', [1000] * 5)
        self.node = SocketNode(
            node_id=node_id,
            initial_balance=initial_balances[int(node_id)],
            consensus_type=consensus_type,
            consensus_config=config,
            network_config=config.get('network', {})
        )
        
        # Simulation state
        self.is_running = False
        self.start_time = None
        
        # Logger
        self.logger = logging.getLogger(f'simulator_{node_id}')
        
        # Set random seed for deterministic behavior
        import random
        random.seed(seed)
        
        self.logger.info(f"Socket simulator initialized for node {node_id}")
        self.logger.info(f"Consensus: {consensus_type}, Scenario: {scenario_type}, Seed: {seed}")
    
    def run(self) -> None:
        """Run the socket-based simulation"""
        try:
            self.logger.info("Starting socket simulation...")
            self.start_time = time.time()
            self.is_running = True
            
            # Start the node
            self.node.start()
            
            # Apply scenario effects
            self._apply_scenario()
            
            # Start transaction generation
            import threading
            tx_thread = threading.Thread(target=self._transaction_generation_loop, daemon=True)
            tx_thread.start()
            
            # Start monitoring
            monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            monitor_thread.start()
            
            # Main simulation loop
            self._main_loop()
            
        except Exception as e:
            self.logger.error(f"Socket simulation error: {e}")
            raise
        finally:
            self.cleanup()
    
    def cleanup(self) -> None:
        """Cleanup simulation resources"""
        self.is_running = False
        
        if self.node:
            self.node.stop()
        
        self.logger.info("Socket simulation cleanup completed")
    
    def _apply_scenario(self) -> None:
        """Apply scenario-specific network conditions"""
        if self.scenario_type == 'partition':
            # Apply network partition after 10 seconds
            import threading
            def apply_partition():
                time.sleep(10)
                if self.is_running:
                    # Simple partition: nodes 0,1 vs nodes 2,3,4
                    node_id_int = int(self.node_id)
                    if node_id_int <= 1:
                        allowed_peers = {'0', '1'}
                    else:
                        allowed_peers = {'2', '3', '4'}
                    
                    self.node.set_partition(allowed_peers)
                    self.logger.info(f"Applied network partition: {allowed_peers}")
                    
                    # Heal partition after 15 more seconds
                    time.sleep(15)
                    if self.is_running:
                        self.node.heal_partition()
                        self.logger.info("Healed network partition")
            
            partition_thread = threading.Thread(target=apply_partition, daemon=True)
            partition_thread.start()
    
    def _main_loop(self) -> None:
        """Main simulation loop"""
        while self.is_running and self.start_time:
            elapsed = time.time() - self.start_time
            if elapsed >= self.duration:
                self.logger.info(f"Simulation completed after {elapsed:.2f} seconds")
                break
            
            time.sleep(1.0)
    
    def _monitor_loop(self) -> None:
        """Background monitoring loop"""
        while self.is_running:
            try:
                info = self.node.get_blockchain_info()
                self.logger.info(f"Blockchain state: {info}")
                time.sleep(5.0)  # Monitor every 5 seconds to reduce log noise
            except Exception as e:
                self.logger.error(f"Monitor error: {e}")
                time.sleep(2.0)
    
    def _transaction_generation_loop(self) -> None:
        """Background transaction generation loop"""
        import random
        
        while self.is_running:
            try:
                # Generate transaction occasionally
                if random.random() < 0.3:  # 30% chance
                    # Pick random receiver (not self)
                    receivers = [str(i) for i in range(5) if str(i) != self.node_id]
                    if receivers:
                        receiver = random.choice(receivers)
                        amount = round(random.uniform(1.0, 10.0), 2)
                        
                        # Check if we have sufficient balance
                        if self.node.get_balance() >= amount:
                            tx = self.node.create_transaction(receiver, amount)
                            if tx:
                                self.node.broadcast_transaction(tx)
                                self.logger.info(f"Generated transaction: {amount} to {receiver}")
                
                time.sleep(3.0)  # Generate transactions every 3 seconds
            except Exception as e:
                self.logger.error(f"Transaction generation error: {e}")
                time.sleep(3.0)


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\nReceived shutdown signal. Cleaning up...")
    sys.exit(0)


def main():
    """Main function"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger = None
    
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Setup logging
        logger = setup_logging(args.node_id, args.log_level)
        
        # Load configuration
        config = load_config(args.consensus, args.config_dir)
        
        # Update config with command line arguments
        config['simulation']['duration_seconds'] = args.duration
        
        logger.info(f"Configuration loaded for {args.consensus} consensus")
        logger.info(f"Running {args.scenario} scenario with seed {args.seed}")
        
        # Create and start socket simulator
        simulator = SocketSimulator(
            node_id=str(args.node_id),
            consensus_type=args.consensus,
            scenario_type=args.scenario,
            seed=args.seed,
            config=config
        )
        
        logger.info("Starting socket simulation...")
        simulator.run()
        
    except KeyboardInterrupt:
        if logger:
            logger.info("Simulation interrupted by user")
    except Exception as e:
        if logger:
            logger.error(f"Simulation failed: {e}")
        else:
            print(f"Simulation failed: {e}")
        sys.exit(1)
    finally:
        if logger:
            logger.info("Socket simulation ended")


if __name__ == "__main__":
    main()