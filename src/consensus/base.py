"""
Base consensus interface
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..core.block import Block
from ..core.transaction import Transaction


class ConsensusAlgorithm(ABC):
    """
    Abstract base class for consensus algorithms
    """
    
    def __init__(self, config: dict):
        """
        Initialize consensus algorithm
        
        Args:
            config: Configuration parameters
        """
        self.config = config
    
    @abstractmethod
    def can_propose_block(self, node_id: str, height: int) -> bool:
        """
        Check if node can propose a block at given height
        
        Args:
            node_id: ID of the node
            height: Block height
            
        Returns:
            bool: True if node can propose
        """
        pass
    
    @abstractmethod
    def create_block(self, height: int, prev_hash: str, transactions: List[Transaction], proposer_id: str) -> Block:
        """
        Create a new block using this consensus mechanism
        
        Args:
            height: Block height
            prev_hash: Previous block hash
            transactions: Transactions to include
            proposer_id: ID of the proposing node
            
        Returns:
            Block: New block
        """
        pass
    
    @abstractmethod
    def validate_block(self, block: Block, proposer_id: str) -> bool:
        """
        Validate a block according to consensus rules
        
        Args:
            block: Block to validate
            proposer_id: ID of the proposing node
            
        Returns:
            bool: True if block is valid
        """
        pass
    
    @abstractmethod
    def select_best_chain(self, chains: List[List[Block]]) -> List[Block]:
        """
        Select the best chain from multiple competing chains
        
        Args:
            chains: List of competing chains
            
        Returns:
            List[Block]: Best chain
        """
        pass
    
    def get_block_time_ms(self) -> int:
        """
        Get expected block time in milliseconds
        
        Returns:
            int: Block time in ms
        """
        return self.config.get('block_time_ms', 1000)
    
    def mine_block(self, blockchain, node_id: str, max_transactions: int = 10):
        """
        Mine a new block from the blockchain state
        
        Args:
            blockchain: The blockchain instance
            node_id: ID of the mining node
            max_transactions: Maximum number of transactions to include
            
        Returns:
            Block: New mined block or None if mining failed
        """
        # Check if this node can propose a block
        latest_block = blockchain.get_latest_block()
        next_height = latest_block.height + 1
        
        if not self.can_propose_block(node_id, next_height):
            return None
            
        # Get pending transactions
        transactions = blockchain.get_pending_transactions(max_transactions)
        
        if not transactions:
            return None
            
        # Create and mine the block
        try:
            block = self.create_block(
                height=next_height,
                prev_hash=latest_block.hash,
                transactions=transactions,
                proposer_id=node_id
            )
            # Only remove transactions from pending pool if mining was successful
            blockchain.remove_transactions(transactions)
            return block
        except Exception as e:
            # Don't need to return transactions since we didn't remove them
            raise e