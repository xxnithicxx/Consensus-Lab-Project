"""
Hybrid consensus implementation (Stake-weighted leader selection + Light PoW)
"""

import time
import random
import hashlib
from typing import List, Dict, Optional
from .base import ConsensusAlgorithm
from ..core.block import Block
from ..core.transaction import Transaction


class HybridConsensus(ConsensusAlgorithm):
    """
    Hybrid consensus: Stake-weighted leader selection + Light PoW
    """
    
    def __init__(self, config: dict):
        """
        Initialize Hybrid consensus
        
        Args:
            config: Configuration containing stakes, light_difficulty, etc.
        """
        super().__init__(config)
        self.light_difficulty = config.get('light_difficulty', 2)
        self.stakes = config.get('stakes', [200, 300, 150, 250, 100])
        self.leader_timeout_ms = config.get('leader_timeout_ms', 1000)
        
        # Leader failure handling configuration
        self.max_backup_leaders = config.get('max_backup_leaders', 3)
        self.backup_timeout_multiplier = config.get('backup_timeout_multiplier', 0.5)
        
        # Track height timing for timeout detection
        self.height_start_times: Dict[int, float] = {}
        self.height_proposals: Dict[int, List[str]] = {}  # Track who has proposed for each height
    
    def can_propose_block(self, node_id: str, height: int) -> bool:
        """
        Enhanced block proposal check with leader failure handling
        
        Args:
            node_id: ID of the node
            height: Block height
            
        Returns:
            bool: True if node can propose (primary leader or backup after timeout)
        """
        try:
            node_id_int = int(node_id)
            current_time = time.time()
            
            # Initialize height timing if not seen before
            if height not in self.height_start_times:
                self.height_start_times[height] = current_time
                self.height_proposals[height] = []
            
            # Check if this node is the primary leader
            primary_leader = self.select_leader(height)
            if node_id_int == primary_leader:
                return True
            
            # Check if primary leader has timed out and this node is a backup
            if self.is_leader_timeout_expired(height, self.height_start_times[height]):
                backup_leaders = self.get_backup_leaders(height, primary_leader)
                
                # Check if this node is in the backup leader list
                if node_id_int in backup_leaders:
                    backup_index = backup_leaders.index(node_id_int)
                    backup_timeout = self.get_backup_timeout(backup_index)
                    
                    # Check if it's this backup's turn (previous backups have also timed out)
                    time_elapsed = current_time - self.height_start_times[height]
                    required_time = (self.leader_timeout_ms / 1000.0) + (backup_timeout * backup_index)
                    
                    if time_elapsed >= required_time:
                        return True
            
            return False
            
        except (ValueError, IndexError):
            return False
    
    def select_leader(self, height: int, seed: int = 42) -> int:
        """
        Select leader using stake-weighted random selection
        
        Args:
            height: Block height
            seed: Random seed for deterministic selection
            
        Returns:
            int: ID of selected leader node
        """
        # Use height as seed to ensure deterministic selection
        # across all nodes for the same height
        combined_seed = seed + height
        random.seed(combined_seed)
        
        # Calculate total stake
        total_stake = sum(self.stakes)
        
        # Random selection weighted by stake
        rand_value = random.randint(1, total_stake)
        
        cumulative_stake = 0
        for i, stake in enumerate(self.stakes):
            cumulative_stake += stake
            if rand_value <= cumulative_stake:
                return i
        
        # Fallback to last node
        return len(self.stakes) - 1
    
    def create_block(self, height: int, prev_hash: str, transactions: List[Transaction], proposer_id: str) -> Block:
        """
        Create a new block with light PoW (enhanced with leader tracking)
        
        Args:
            height: Block height
            prev_hash: Previous block hash
            transactions: Transactions to include
            proposer_id: ID of the proposing node
            
        Returns:
            Block: New block with light PoW
        """
        # Track that this node has proposed for this height
        if height not in self.height_proposals:
            self.height_proposals[height] = []
        self.height_proposals[height].append(proposer_id)
        
        # Create block
        block = Block(
            height=height,
            prev_hash=prev_hash,
            transactions=transactions,
            timestamp=time.time(),
            nonce=0
        )
        
        # Add proposer information and current leader context
        block.proposer_id = proposer_id
        block.expected_leader = self.get_current_leader(height)
        block.is_backup_proposal = (int(proposer_id) != self.select_leader(height))
        
        # Perform light PoW
        return self.light_pow(block)
    
    def light_pow(self, block: Block) -> Block:
        """
        Perform lightweight proof of work
        
        Args:
            block: Block to perform light PoW on
            
        Returns:
            Block: Block with valid light PoW
        """
        target = "0" * self.light_difficulty
        
        nonce = 0
        while nonce < 100000:  # Limited iterations for light PoW
            block.nonce = nonce
            block.hash = block.calculate_hash()
            
            if block.hash.startswith(target):
                return block
            
            nonce += 1
        
        # Return block even if light PoW not complete
        return block
    
    def validate_block(self, block: Block, proposer_id: str) -> bool:
        """
        Enhanced block validation with leader failure handling
        
        Args:
            block: Block to validate
            proposer_id: ID of the proposing node
            
        Returns:
            bool: True if block is valid
        """
        # Validate that the proposer was authorized (including backup scenarios)
        if not self.validate_leader_selection_with_timeout(block, block.height):
            return False
        
        # Validate light PoW
        if not self.validate_light_pow(block):
            return False
        
        return True
    
    def validate_leader_selection(self, block: Block, height: int) -> bool:
        """
        Verify that the block was created by the correct leader
        
        Args:
            block: Block to validate
            height: Block height
            
        Returns:
            bool: True if leader selection is valid
        """
        expected_leader = self.select_leader(height)
        
        # Check if proposer is stored in block
        if hasattr(block, 'proposer_id'):
            try:
                proposer_id = int(block.proposer_id)
                return proposer_id == expected_leader
            except (ValueError, AttributeError):
                pass
        
        # If proposer not stored, we can't validate (assume valid for now)
        return True
    
    def validate_leader_selection_with_timeout(self, block: Block, height: int) -> bool:
        """
        Validate leader selection considering timeout scenarios
        
        Args:
            block: Block to validate
            height: Block height
            
        Returns:
            bool: True if leader selection is valid (including backup scenarios)
        """
        if not hasattr(block, 'proposer_id'):
            return True  # Can't validate without proposer info
        
        try:
            proposer_id = int(block.proposer_id)
            primary_leader = self.select_leader(height)
            
            # Check if proposer is primary leader
            if proposer_id == primary_leader:
                return True
            
            # Check if proposer is a valid backup leader
            backup_leaders = self.get_backup_leaders(height, primary_leader)
            if proposer_id in backup_leaders:
                # In a real implementation, you'd validate the timing here
                # For simulation purposes, we accept backup proposals
                return True
            
            return False
            
        except (ValueError, AttributeError):
            return True  # Can't validate, assume valid
    
    def validate_light_pow(self, block: Block) -> bool:
        """
        Validate the light proof of work
        
        Args:
            block: Block to validate
            
        Returns:
            bool: True if light PoW is valid
        """
        target = "0" * self.light_difficulty
        
        # Recalculate hash
        calculated_hash = block.calculate_hash()
        
        return (calculated_hash == block.hash and 
                block.hash.startswith(target))
    
    def select_best_chain(self, chains: List[List[Block]]) -> List[Block]:
        """
        Select chain with highest cumulative stake-weight
        
        Args:
            chains: List of competing chains
            
        Returns:
            List[Block]: Best chain by stake-weight
        """
        if not chains:
            return []
        
        # Filter valid chains and calculate weights
        valid_chains = []
        for chain in chains:
            if self._is_valid_chain(chain):
                weight = self.calculate_chain_weight(chain)
                valid_chains.append((chain, weight))
        
        if not valid_chains:
            return chains[0] if chains else []
        
        # Select chain with highest weight (ties broken by length, then hash)
        best_chain = max(valid_chains, 
                        key=lambda x: (x[1], len(x[0]), x[0][-1].hash if x[0] else ""))
        
        return best_chain[0]
    
    def _is_valid_chain(self, chain: List[Block]) -> bool:
        """Validate an entire chain according to hybrid rules"""
        for i, block in enumerate(chain):
            if i == 0:
                # Genesis block
                continue
            
            # Check block linking
            if block.prev_hash != chain[i-1].hash:
                return False
            
            # Check hybrid consensus rules
            if not self.validate_light_pow(block):
                return False
            
            if not self.validate_leader_selection(block, block.height):
                return False
        
        return True
    
    def calculate_chain_weight(self, chain: List[Block]) -> float:
        """
        Calculate cumulative stake-weight of a chain
        
        Args:
            chain: Chain to calculate weight for
            
        Returns:
            float: Total stake-weight
        """
        total_weight = 0.0
        
        for block in chain:
            if hasattr(block, 'proposer_id'):
                try:
                    proposer_id = int(block.proposer_id)
                    stake = self.get_stake(proposer_id)
                    total_weight += stake
                except (ValueError, IndexError):
                    pass
            else:
                # If no proposer info, assume minimal weight
                total_weight += 1.0
        
        return total_weight
    
    def get_stake(self, node_id: int) -> int:
        """
        Get stake amount for a node
        
        Args:
            node_id: ID of the node
            
        Returns:
            int: Stake amount
        """
        if 0 <= node_id < len(self.stakes):
            return self.stakes[node_id]
        return 0
    
    def is_leader_timeout_expired(self, height: int, start_time: float) -> bool:
        """
        Check if leader timeout has expired for a height
        
        Args:
            height: Block height
            start_time: Time when height started
            
        Returns:
            bool: True if timeout expired
        """
        timeout_seconds = self.leader_timeout_ms / 1000.0
        return (time.time() - start_time) > timeout_seconds
    
    def get_backup_leaders(self, height: int, primary_leader: int) -> List[int]:
        """
        Get ordered list of backup leaders for a given height
        
        Args:
            height: Block height
            primary_leader: ID of primary leader
            
        Returns:
            List[int]: Ordered list of backup leader IDs
        """
        # Create a deterministic but different seed for backup selection
        backup_seed = hash(f"backup_{height}_{primary_leader}") % 1000000
        random.seed(backup_seed)
        
        # Get all nodes except primary leader
        available_nodes = [i for i in range(len(self.stakes)) if i != primary_leader]
        
        # Sort by stake (higher stake = higher priority as backup)
        available_nodes.sort(key=lambda x: self.stakes[x], reverse=True)
        
        # Take up to max_backup_leaders
        return available_nodes[:self.max_backup_leaders]
    
    def get_backup_timeout(self, backup_index: int) -> float:
        """
        Calculate timeout for backup leader at given index
        
        Args:
            backup_index: Index of backup leader (0 = first backup, 1 = second, etc.)
            
        Returns:
            float: Timeout in seconds for this backup
        """
        base_timeout = self.leader_timeout_ms / 1000.0
        return base_timeout * self.backup_timeout_multiplier
    
    def get_current_leader(self, height: int) -> int:
        """
        Get the current active leader for a height (considering timeouts)
        
        Args:
            height: Block height
            
        Returns:
            int: ID of current active leader
        """
        current_time = time.time()
        
        if height not in self.height_start_times:
            self.height_start_times[height] = current_time
            return self.select_leader(height)
        
        start_time = self.height_start_times[height]
        primary_leader = self.select_leader(height)
        
        # Check if primary leader timeout has expired
        if not self.is_leader_timeout_expired(height, start_time):
            return primary_leader
        
        # Check which backup leader should be active
        backup_leaders = self.get_backup_leaders(height, primary_leader)
        time_elapsed = current_time - start_time
        primary_timeout = self.leader_timeout_ms / 1000.0
        
        for i, backup_leader in enumerate(backup_leaders):
            backup_timeout = self.get_backup_timeout(i)
            required_time = primary_timeout + (backup_timeout * (i + 1))
            
            if time_elapsed < required_time:
                return backup_leader
        
        # If all backups have timed out, return the last backup
        return backup_leaders[-1] if backup_leaders else primary_leader
