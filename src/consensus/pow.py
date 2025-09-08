"""
Proof of Work consensus implementation
"""

import time
import hashlib
from typing import List, Optional
from .base import ConsensusAlgorithm
from ..core.block import Block
from ..core.transaction import Transaction


class ProofOfWork(ConsensusAlgorithm):
    """
    Proof of Work consensus mechanism
    """
    
    def __init__(self, config: dict):
        """
        Initialize PoW consensus
        
        Args:
            config: Configuration containing difficulty and other parameters
        """
        super().__init__(config)
        self.difficulty = config.get('difficulty', 4)
        self.max_mining_time = config.get('mining', {}).get('max_mining_time_ms', 2000) / 1000.0
    
    def can_propose_block(self, node_id: str, height: int) -> bool:
        """
        In PoW, any node can propose a block
        
        Args:
            node_id: ID of the node
            height: Block height
            
        Returns:
            bool: Always True for PoW
        """
        return True
    
    def create_block(self, height: int, prev_hash: str, transactions: List[Transaction], proposer_id: str) -> Block:
        """
        Create and mine a new block using PoW
        
        Args:
            height: Block height
            prev_hash: Previous block hash
            transactions: Transactions to include
            proposer_id: ID of the proposing node
            
        Returns:
            Block: Mined block
        """
        # Create block with initial nonce
        block = Block(
            height=height,
            prev_hash=prev_hash,
            transactions=transactions,
            timestamp=time.time(),
            nonce=0
        )
        
        # Mine the block
        return self._mine_block_pow(block)
    
    def _mine_block_pow(self, block: Block) -> Block:
        """
        Mine a block by solving the hash puzzle
        
        Args:
            block: Block to mine
            
        Returns:
            Block: Mined block with valid proof of work
        """
        target = self.get_target()
        start_time = time.time()
        
        nonce = 0
        while True:
            # Check timeout
            if time.time() - start_time > self.max_mining_time:
                break
            
            # Try current nonce
            block.nonce = nonce
            block.hash = block.calculate_hash()
            
            if block.hash.startswith(target):
                # Found valid proof of work
                return block
            
            nonce += 1
        
        # Return block even if not fully mined (for simulation purposes)
        return block
    
    def validate_block(self, block: Block, proposer_id: str) -> bool:
        """
        Validate PoW for a block
        
        Args:
            block: Block to validate
            proposer_id: ID of the proposing node
            
        Returns:
            bool: True if PoW is valid
        """
        return self.validate_proof(block)
    
    def validate_proof(self, block: Block) -> bool:
        """
        Validate the proof of work for a block
        
        Args:
            block: Block to validate
            
        Returns:
            bool: True if PoW is valid
        """
        target = self.get_target()
        
        # Recalculate hash to verify
        calculated_hash = block.calculate_hash()
        
        # Check if hash matches stored hash and meets difficulty
        return (calculated_hash == block.hash and 
                block.hash.startswith(target))
    
    def select_best_chain(self, chains: List[List[Block]]) -> List[Block]:
        """
        Select the longest valid chain
        
        Args:
            chains: List of competing chains
            
        Returns:
            List[Block]: Longest chain
        """
        if not chains:
            return []
        
        # Filter to only valid chains
        valid_chains = []
        for chain in chains:
            if self._is_valid_chain(chain):
                valid_chains.append(chain)
        
        if not valid_chains:
            return chains[0] if chains else []
        
        # Return longest chain (ties broken by latest block hash)
        return max(valid_chains, key=lambda chain: (len(chain), chain[-1].hash))
    
    def _is_valid_chain(self, chain: List[Block]) -> bool:
        """Validate an entire chain"""
        for i, block in enumerate(chain):
            if i == 0:
                # Genesis block validation
                continue
            
            # Check previous hash links
            if block.prev_hash != chain[i-1].hash:
                return False
            
            # Check proof of work
            if not self.validate_proof(block):
                return False
        
        return True
    
    def get_target(self) -> str:
        """
        Get the target string for proof of work
        
        Returns:
            str: Target string (difficulty number of zeros)
        """
        return "0" * self.difficulty
    
    def calculate_difficulty(self, recent_blocks: List[Block]) -> int:
        """
        Adjust difficulty based on recent block times
        
        Args:
            recent_blocks: Recent blocks for difficulty calculation
            
        Returns:
            int: New difficulty level
        """
        if len(recent_blocks) < 2:
            return self.difficulty
        
        # Calculate average block time for recent blocks
        time_diffs = []
        for i in range(1, len(recent_blocks)):
            time_diff = recent_blocks[i].timestamp - recent_blocks[i-1].timestamp
            time_diffs.append(time_diff)
        
        avg_time = sum(time_diffs) / len(time_diffs)
        target_time = self.get_block_time_ms() / 1000.0
        
        # Adjust difficulty based on how far off we are from target
        if avg_time < target_time * 0.5:
            return min(self.difficulty + 1, 8)  # Increase difficulty
        elif avg_time > target_time * 2:
            return max(self.difficulty - 1, 1)  # Decrease difficulty
        
        return self.difficulty
