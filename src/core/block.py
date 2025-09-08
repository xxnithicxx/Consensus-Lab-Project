"""
Block structure implementation
"""

import time
import hashlib
import json
from typing import List


class Block:
    """
    Represents a block in the blockchain
    """
    
    def __init__(self, height: int, prev_hash: str, transactions: List, timestamp: float = None, nonce: int = 0):
        """
        Initialize a new block
        
        Args:
            height: Block height in the chain
            prev_hash: Hash of previous block
            transactions: List of transactions in this block
            timestamp: Block creation timestamp
            nonce: Proof of work nonce value
        """
        self.height = height
        self.prev_hash = prev_hash
        self.transactions = transactions or []
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.nonce = nonce
        self.proposer_id: str = ""  # ID of the node that proposed this block
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """
        Calculate SHA256 hash of the block
        
        Returns:
            str: Hash of the block
        """
        block_data = {
            'height': self.height,
            'prev_hash': self.prev_hash,
            'transactions': [tx.to_dict() if hasattr(tx, 'to_dict') else str(tx) for tx in self.transactions],
            'timestamp': self.timestamp,
            'nonce': self.nonce
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def to_dict(self) -> dict:
        """
        Convert block to dictionary representation
        
        Returns:
            dict: Block as dictionary
        """
        return {
            'height': self.height,
            'prev_hash': self.prev_hash,
            'transactions': [tx.to_dict() if hasattr(tx, 'to_dict') else str(tx) for tx in self.transactions],
            'timestamp': self.timestamp,
            'nonce': self.nonce,
            'proposer_id': getattr(self, 'proposer_id', ''),
            'hash': self.hash
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """
        Create block from dictionary
        
        Args:
            data: Block data as dictionary
            
        Returns:
            Block: New block instance
        """
        # Import here to avoid circular imports
        from .transaction import Transaction
        
        transactions = []
        for tx_data in data.get('transactions', []):
            if isinstance(tx_data, dict):
                transactions.append(Transaction.from_dict(tx_data))
            else:
                # Handle simple string transactions for testing
                transactions.append(tx_data)
        
        block = cls(
            height=data['height'],
            prev_hash=data['prev_hash'],
            transactions=transactions,
            timestamp=data['timestamp'],
            nonce=data['nonce']
        )
        block.proposer_id = data.get('proposer_id', '')
        block.hash = data['hash']
        return block
    
    def __str__(self) -> str:
        """String representation of the block"""
        return f"Block(height={self.height}, hash={self.hash[:8]}..., txs={len(self.transactions)})"
