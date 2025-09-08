"""
Transaction handling implementation
"""

import time
import hashlib
import json
from typing import Optional


class Transaction:
    """
    Represents a transaction in the blockchain
    """
    
    def __init__(self, sender: str, receiver: str, amount: float, timestamp: float = None):
        """
        Initialize a new transaction
        
        Args:
            sender: Sender's address
            receiver: Receiver's address
            amount: Amount to transfer
            timestamp: Transaction timestamp
        """
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.signature = None
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """
        Calculate hash of the transaction
        
        Returns:
            str: Hash of the transaction
        """
        tx_data = {
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': self.amount,
            'timestamp': self.timestamp
        }
        tx_string = json.dumps(tx_data, sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()
    
    def sign(self, private_key: str) -> None:
        """
        Sign the transaction with private key
        
        Args:
            private_key: Private key for signing
        """
        # Simple signature implementation for this simulator
        # In reality, this would use proper cryptographic signing
        signature_data = f"{self.hash}:{private_key}"
        self.signature = hashlib.sha256(signature_data.encode()).hexdigest()
    
    def verify_signature(self, public_key: str) -> bool:
        """
        Verify transaction signature
        
        Args:
            public_key: Public key for verification
            
        Returns:
            bool: True if signature is valid
        """
        if self.signature is None:
            return False
        
        # Simple verification for this simulator
        # In reality, this would use proper cryptographic verification
        expected_signature_data = f"{self.hash}:{public_key}"
        expected_signature = hashlib.sha256(expected_signature_data.encode()).hexdigest()
        return self.signature == expected_signature
    
    def to_dict(self) -> dict:
        """
        Convert transaction to dictionary
        
        Returns:
            dict: Transaction as dictionary
        """
        return {
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': self.amount,
            'timestamp': self.timestamp,
            'signature': self.signature,
            'hash': self.hash
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """
        Create transaction from dictionary
        
        Args:
            data: Transaction data as dictionary
            
        Returns:
            Transaction: New transaction instance
        """
        tx = cls(
            sender=data['sender'],
            receiver=data['receiver'],
            amount=data['amount'],
            timestamp=data['timestamp']
        )
        tx.signature = data.get('signature')
        tx.hash = data['hash']
        return tx
    
    def __str__(self) -> str:
        """String representation of the transaction"""
        return f"Tx({self.sender} -> {self.receiver}: {self.amount})"
