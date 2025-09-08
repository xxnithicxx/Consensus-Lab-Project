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
    
    def can_propose_block(self, node_id: str, height: int) -> bool:
        """
        Check if node is the selected leader for this height
        
        Args:
            node_id: ID of the node
            height: Block height
            
        Returns:
            bool: True if node is the leader
        """
        try:
            node_id_int = int(node_id)
            selected_leader = self.select_leader(height)
            return node_id_int == selected_leader
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
        Create a new block with light PoW
        
        Args:
            height: Block height
            prev_hash: Previous block hash
            transactions: Transactions to include
            proposer_id: ID of the proposing node
            
        Returns:
            Block: New block with light PoW
        """
        # Create block
        block = Block(
            height=height,
            prev_hash=prev_hash,
            transactions=transactions,
            timestamp=time.time(),
            nonce=0
        )
        
        # Add proposer information to block (store in unused field)
        block.proposer_id = proposer_id
        
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
        Validate block according to hybrid consensus rules
        
        Args:
            block: Block to validate
            proposer_id: ID of the proposing node
            
        Returns:
            bool: True if block is valid
        """
        # Validate leader selection
        if not self.validate_leader_selection(block, block.height):
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
