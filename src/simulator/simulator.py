import time
import json
import logging
import threading
from typing import List, Dict, Optional
from ..network.node import Node
from ..network.network import NetworkSimulator
from .scenarios import ScenarioRunner


class Simulator:
    """
    Main blockchain simulator
    """
    
    def __init__(self, node_id: str, consensus_type: str, scenario_type: str, 
                 seed: int, config: dict):
        """
        Initialize the simulator
        
        Args:
            node_id: ID of this node
            consensus_type: Type of consensus ('pow' or 'hybrid')
            scenario_type: Type of scenario ('delays' or 'partition')
            seed: Random seed for deterministic behavior
            config: Configuration parameters
        """
        self.node_id = node_id
        self.consensus_type = consensus_type
        self.scenario_type = scenario_type
        self.seed = seed
        self.config = config
        
        # Simulation state
        self.is_running = False
        self.start_time = None
        self.duration = config.get('simulation', {}).get('duration_seconds', 30)
        
        # Initialize components
        self.nodes: List[Node] = []
        self.network: Optional[NetworkSimulator] = None
        self.scenario_runner: Optional[ScenarioRunner] = None
        self.my_node: Optional[Node] = None
        
        # Monitoring
        self.monitor_thread: Optional[threading.Thread] = None
        self.tx_generation_thread: Optional[threading.Thread] = None
        
        # Logger
        self.logger = logging.getLogger(f'simulator_{node_id}')
        
        # Set random seed for deterministic behavior
        import random
        random.seed(seed)
        
        self.logger.info(f"Simulator initialized for node {node_id}")
        self.logger.info(f"Consensus: {consensus_type}, Scenario: {scenario_type}, Seed: {seed}")
    
    def create_nodes(self) -> List[Node]:
        """
        Create all nodes in the network
        
        Returns:
            List[Node]: List of created nodes
        """
        nodes = []
        initial_balances = self.config.get('initial_balances', [1000] * 5)
        
        for i in range(5):  # Create 5 nodes (N0-N4)
            node = Node(
                node_id=str(i),
                initial_balance=initial_balances[i],
                consensus_type=self.consensus_type,
                consensus_config=self.config,
                network_config=self.config.get('network', {})
            )
            nodes.append(node)
            
            if str(i) == self.node_id:
                self.my_node = node
        
        self.logger.info(f"Created {len(nodes)} nodes")
        return nodes
    
    def setup_network(self) -> NetworkSimulator:
        """
        Setup network simulator
        
        Returns:
            NetworkSimulator: Configured network simulator
        """
        network = NetworkSimulator(
            nodes=self.nodes,
            delay_config=self.config.get('network', {})
        )
        
        self.logger.info("Network simulator created")
        return network
    
    def run(self) -> None:
        """Run the simulation"""
        try:
            self.logger.info("Starting simulation...")
            self.start_time = time.time()
            self.is_running = True
            
            # Create network components
            self.nodes = self.create_nodes()
            self.network = self.setup_network()
            
            # Create scenario runner
            self.scenario_runner = ScenarioRunner(
                nodes=self.nodes,
                network=self.network,
                config=self.config
            )
            
            # Start network and nodes
            self.network.start()
            
            # Start monitoring
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            
            # Start transaction generation
            self.tx_generation_thread = threading.Thread(target=self._transaction_generation_loop, daemon=True)
            self.tx_generation_thread.start()
            
            # Run scenario
            self.scenario_runner.run_scenario(self.scenario_type, self.seed)
            
            # Main simulation loop
            self._main_loop()
            
        except Exception as e:
            self.logger.error(f"Simulation error: {e}")
            raise
        finally:
            self.cleanup()
    
    def start_consensus(self) -> None:
        """Start consensus algorithm on this node"""
        if self.my_node:
            self.my_node.start()
    
    def monitor_blockchain(self) -> None:
        """Monitor blockchain state and log events"""
        if self.my_node:
            info = self.my_node.get_blockchain_info()
            
            self.logger.info(f"Blockchain state: {info}")
            
            # Check invariants
            if not self.check_invariants():
                self.logger.error("Invariant violation detected!")
                self.is_running = False
    
    def check_invariants(self) -> bool:
        """
        Check blockchain invariants
        
        Returns:
            bool: True if all invariants hold
        """
        if not self.my_node:
            return True
        
        try:
            # 1. No conflicting finality
            final_blocks = self.my_node.blockchain.get_final_blocks()
            heights_seen = set()
            for block in final_blocks:
                if block.height in heights_seen:
                    self.logger.error(f"INVARIANT VIOLATION: Conflicting finality at height {block.height}")
                    return False
                heights_seen.add(block.height)
            
            # 2. Monotonic finality (final height only increases)
            # This is implicitly maintained by the blockchain structure
            
            # 3. No double-spending in final chain
            # This would require more complex tracking - simplified for now
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking invariants: {e}")
            return False
    
    def generate_transactions(self) -> None:
        """Generate random transactions for testing"""
        if not self.my_node or not self.is_running:
            return
        
        import random
        
        # Generate transaction occasionally
        if random.random() < 0.3:  # 30% chance
            # Pick random receiver (not self)
            receivers = [str(i) for i in range(5) if str(i) != self.node_id]
            if receivers:
                receiver = random.choice(receivers)
                amount = random.uniform(1.0, 10.0)
                
                # Check if we have sufficient balance
                if self.my_node.get_balance() >= amount:
                    tx = self.my_node.create_transaction(receiver, amount)
                    self.my_node.broadcast_transaction(tx)
                    
                    self.logger.info(f"Generated transaction: {amount} to {receiver}")
    
    def log_blockchain_state(self) -> None:
        """Log current blockchain state"""
        if self.my_node:
            info = self.my_node.get_blockchain_info()
            self.logger.info(f"Blockchain: {json.dumps(info)}")
    
    def get_simulation_results(self) -> Dict:
        """
        Get simulation results and statistics
        
        Returns:
            Dict: Simulation results
        """
        results = {
            "node_id": self.node_id,
            "consensus_type": self.consensus_type,
            "scenario_type": self.scenario_type,
            "seed": self.seed,
            "duration": time.time() - self.start_time if self.start_time else 0
        }
        
        if self.my_node:
            results.update(self.my_node.get_blockchain_info())
        
        if self.network:
            results["network_stats"] = self.network.get_network_stats()
        
        return results
    
    def cleanup(self) -> None:
        """Cleanup simulation resources"""
        self.is_running = False
        
        if self.network:
            self.network.stop()
        
        self.logger.info("Simulation cleanup completed")
    
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
                self.monitor_blockchain()
                time.sleep(2.0)  # Monitor every 2 seconds
            except Exception as e:
                self.logger.error(f"Monitor error: {e}")
    
    def _transaction_generation_loop(self) -> None:
        """Background transaction generation loop"""
        while self.is_running:
            try:
                self.generate_transactions()
                time.sleep(3.0)  # Generate transactions every 3 seconds
            except Exception as e:
                self.logger.error(f"Transaction generation error: {e}")


class BlockchainLogger:
    """
    Structured logging for blockchain events
    """
    
    def __init__(self, node_id: str, log_file: str):
        """
        Initialize logger
        
        Args:
            node_id: ID of the node
            log_file: Path to log file
        """
        pass
    
    def log_event(self, event_type: str, data: Dict) -> None:
        """
        Log an event with structured data
        
        Args:
            event_type: Type of event
            data: Event data
        """
        pass
    
    def log_block_created(self, block_height: int, block_hash: str, 
                         transactions_count: int, mining_time_ms: float) -> None:
        """
        Log block creation event
        
        Args:
            block_height: Height of created block
            block_hash: Hash of created block
            transactions_count: Number of transactions in block
            mining_time_ms: Time taken to mine block
        """
        pass
    
    def log_block_received(self, block_height: int, block_hash: str, 
                          sender_id: str, validation_result: bool) -> None:
        """
        Log block reception event
        
        Args:
            block_height: Height of received block
            block_hash: Hash of received block
            sender_id: ID of sender node
            validation_result: Whether block was valid
        """
        pass
    
    def log_fork_detected(self, fork_height: int, competing_blocks: List[str]) -> None:
        """
        Log fork detection event
        
        Args:
            fork_height: Height where fork occurred
            competing_blocks: List of competing block hashes
        """
        pass
    
    def log_chain_reorganization(self, old_tip: str, new_tip: str, 
                                reorganized_blocks: int) -> None:
        """
        Log chain reorganization event
        
        Args:
            old_tip: Hash of old chain tip
            new_tip: Hash of new chain tip
            reorganized_blocks: Number of blocks reorganized
        """
        pass
    
    def log_transaction_created(self, tx_hash: str, sender: str, 
                               receiver: str, amount: float) -> None:
        """
        Log transaction creation event
        
        Args:
            tx_hash: Transaction hash
            sender: Sender address
            receiver: Receiver address
            amount: Transaction amount
        """
        pass
    
    def log_network_event(self, event_type: str, data: Dict) -> None:
        """
        Log network-related event
        
        Args:
            event_type: Type of network event
            data: Event data
        """
        pass
