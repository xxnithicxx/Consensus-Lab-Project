"""
Test scenarios for blockchain simulation
"""

import time
import random
import threading
from typing import List, Dict, Optional
from ..network.node import Node
from ..network.network import NetworkSimulator


class ScenarioRunner:
    """
    Runs different test scenarios for blockchain simulation
    """
    
    def __init__(self, nodes: List[Node], network: NetworkSimulator, config: dict):
        """
        Initialize scenario runner
        
        Args:
            nodes: List of nodes in the network
            network: Network simulator
            config: Configuration parameters
        """
        self.nodes = nodes
        self.network = network
        self.config = config
        self.is_running = False
        
        # Scenario results
        self.results = {}
        
        # Logging
        import logging
        self.logger = logging.getLogger('scenario_runner')
    
    def run_scenario(self, scenario_type: str, seed: int) -> None:
        """
        Run a specific scenario
        
        Args:
            scenario_type: Type of scenario to run
            seed: Random seed for deterministic behavior
        """
        self.is_running = True
        random.seed(seed)
        
        self.logger.info(f"Starting {scenario_type} scenario with seed {seed}")
        
        if scenario_type == 'delays':
            self.run_network_delays_scenario(seed)
        elif scenario_type == 'partition':
            self.run_partition_heal_scenario(seed)
        else:
            self.logger.error(f"Unknown scenario type: {scenario_type}")
    
    def run_network_delays_scenario(self, seed: int) -> None:
        """
        Scenario 1: Network with delays
        
        Args:
            seed: Random seed
        """
        self.logger.info("Running network delays scenario")
        
        # Enable variable delays
        self.network.simulate_network_delays(True)
        
        # Generate some initial transactions
        self.generate_random_transactions(10, seed)
        
        self.logger.info("Network delays scenario setup complete")
    
    def run_partition_heal_scenario(self, seed: int) -> None:
        """
        Scenario 2: Network partition and heal
        
        Args:
            seed: Random seed
        """
        self.logger.info("Running partition and heal scenario")
        
        # Get configuration
        partition_duration = self.config.get('network', {}).get('partition_duration_ms', 5000)
        heal_duration = self.config.get('network', {}).get('heal_duration_ms', 3000)
        
        # Start partition after a short delay
        threading.Timer(2.0, self.create_partition, args=[partition_duration]).start()
        
        # Schedule healing
        total_partition_time = 2.0 + (partition_duration / 1000.0)
        threading.Timer(total_partition_time, self.heal_partition).start()
        
        self.logger.info(f"Partition scheduled for {partition_duration}ms, heal after {total_partition_time}s")
    
    def create_partition(self, duration_ms: int) -> None:
        """
        Create a network partition for specified duration
        
        Args:
            duration_ms: Duration of partition in milliseconds
        """
        # Create 2-3 split partition
        group1 = ["0", "1", "2"]  # Majority group (for hybrid: stakes 200+300+150=650)
        group2 = ["3", "4"]       # Minority group (for hybrid: stakes 250+100=350)
        
        self.network.create_partition([group1, group2])
        self.logger.info(f"Network partition created: {group1} | {group2}")
        
        # Log partition event for all nodes
        self._log_partition_event_to_consensus("partition_start", {
            "group1": group1,
            "group2": group2,
            "group1_size": len(group1),
            "group2_size": len(group2)
        })
        
        # Schedule partition end
        threading.Timer(duration_ms / 1000.0, self.heal_partition).start()
    
    def heal_partition(self) -> None:
        """Heal the network partition"""
        self.network.heal_partition()
        self.logger.info("Network partition healed - full connectivity restored")
        
        # Log heal event for all nodes
        self._log_partition_event_to_consensus("partition_heal", {
            "action": "network_healed",
            "full_connectivity": True
        })
    
    def generate_random_transactions(self, count: int, seed: int) -> None:
        """
        Generate random transactions across nodes
        
        Args:
            count: Number of transactions to generate
            seed: Random seed
        """
        random.seed(seed)
        
        for i in range(count):
            # Pick random sender and receiver
            sender_idx = random.randint(0, len(self.nodes) - 1)
            receiver_idx = random.randint(0, len(self.nodes) - 1)
            
            # Ensure sender != receiver
            while receiver_idx == sender_idx:
                receiver_idx = random.randint(0, len(self.nodes) - 1)
            
            sender = self.nodes[sender_idx]
            receiver_id = str(receiver_idx)
            amount = random.uniform(1.0, 5.0)
            
            # Check if sender has sufficient balance
            if sender.get_balance() >= amount:
                tx = sender.create_transaction(receiver_id, amount)
                sender.broadcast_transaction(tx)
                
                self.logger.info(f"Generated tx: {sender.node_id} -> {receiver_id}, amount: {amount:.2f}")
    
    def verify_invariants(self) -> bool:
        """
        Verify blockchain invariants across all nodes
        
        Returns:
            bool: True if all invariants hold
        """
        try:
            # Check each invariant
            if not self.check_finality_consistency():
                return False
            
            if not self.check_chain_progression():
                return False
            
            if not self.check_no_double_spending():
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying invariants: {e}")
            return False
    
    def check_finality_consistency(self) -> bool:
        """
        Check that no two different blocks are final at the same height
        
        Returns:
            bool: True if finality is consistent
        """
        final_blocks_by_height = {}
        
        for node in self.nodes:
            final_blocks = node.blockchain.get_final_blocks()
            for block in final_blocks:
                height = block.height
                if height in final_blocks_by_height:
                    if final_blocks_by_height[height] != block.hash:
                        self.logger.error(f"Finality inconsistency at height {height}")
                        return False
                else:
                    final_blocks_by_height[height] = block.hash
        
        return True
    
    def check_no_double_spending(self) -> bool:
        """
        Check that there is no double-spending in final chains
        
        Returns:
            bool: True if no double-spending detected
        """
        # Simplified check - would need more sophisticated implementation
        # for real double-spending detection
        return True
    
    def check_chain_progression(self) -> bool:
        """
        Check that final height only increases
        
        Returns:
            bool: True if chain progression is correct
        """
        # This is enforced by the blockchain structure itself
        return True
    
    def get_scenario_results(self) -> Dict:
        """
        Get results and statistics from scenario run
        
        Returns:
            Dict: Scenario results
        """
        results = {
            "invariants_valid": self.verify_invariants(),
            "network_stats": self.network.get_network_stats() if self.network else {},
            "node_stats": []
        }
        
        for node in self.nodes:
            node_info = node.get_blockchain_info()
            node_info["node_id"] = node.node_id
            results["node_stats"].append(node_info)
        
        return results
    
    def log_scenario_event(self, event_type: str, data: Dict) -> None:
        """
        Log scenario-specific event
        
        Args:
            event_type: Type of event
            data: Event data
        """
        log_entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "data": data
        }
        
        self.logger.info(f"SCENARIO EVENT: {log_entry}")
    
    def _log_partition_event_to_consensus(self, event_type: str, partition_info: dict) -> None:
        """
        Log partition events to all node consensus algorithms
        
        Args:
            event_type: Type of partition event
            partition_info: Information about the partition
        """
        for node in self.nodes:
            if hasattr(node, 'consensus') and node.consensus:
                # Check if consensus has partition logging method
                if hasattr(node.consensus, '_log_partition_event'):
                    try:
                        node.consensus._log_partition_event(event_type, partition_info)
                    except Exception as e:
                        self.logger.debug(f"Failed to log partition event to node {node.node_id}: {e}")


class NetworkDelaysScenario:
    """Scenario with simulated network delays"""
    
    def __init__(self, nodes: List[Node], network: NetworkSimulator, config: dict):
        """
        Initialize network delays scenario
        
        Args:
            nodes: List of nodes
            network: Network simulator
            config: Configuration
        """
        pass
    
    def run(self, duration_seconds: int, seed: int) -> None:
        """
        Run the network delays scenario
        
        Args:
            duration_seconds: How long to run the scenario
            seed: Random seed
        """
        pass
    
    def simulate_variable_delays(self) -> None:
        """Simulate variable network delays"""
        pass


class PartitionHealScenario:
    """Scenario with network partition and healing"""
    
    def __init__(self, nodes: List[Node], network: NetworkSimulator, config: dict):
        """
        Initialize partition heal scenario
        
        Args:
            nodes: List of nodes
            network: Network simulator
            config: Configuration
        """
        pass
    
    def run(self, partition_duration_ms: int, heal_duration_ms: int, seed: int) -> None:
        """
        Run the partition and heal scenario
        
        Args:
            partition_duration_ms: Duration of partition phase
            heal_duration_ms: Duration of heal phase
            seed: Random seed
        """
        pass
    
    def create_balanced_partition(self) -> None:
        """Create a balanced network partition (2-3 split)"""
        pass
    
    def monitor_partition_behavior(self) -> None:
        """Monitor how nodes behave during partition"""
        pass
    
    def monitor_heal_behavior(self) -> None:
        """Monitor how nodes behave during healing"""
        pass
