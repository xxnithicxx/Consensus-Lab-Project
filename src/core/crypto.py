"""
Cryptographic functions and utilities
"""

import hashlib
import json
from typing import Any


"""
Cryptographic functions and utilities
"""

import hashlib
import json
import secrets
from typing import Any


def calculate_sha256(data: str) -> str:
    """
    Calculate SHA256 hash of input data
    
    Args:
        data: Data to hash
        
    Returns:
        str: SHA256 hash as hexadecimal string
    """
    return hashlib.sha256(data.encode()).hexdigest()


def hash_object(obj: Any) -> str:
    """
    Hash any object by converting to JSON first
    
    Args:
        obj: Object to hash
        
    Returns:
        str: SHA256 hash of the object
    """
    json_str = json.dumps(obj, sort_keys=True)
    return calculate_sha256(json_str)


def generate_merkle_root(transactions: list) -> str:
    """
    Calculate Merkle root of transaction list
    
    Args:
        transactions: List of transactions
        
    Returns:
        str: Merkle root hash
    """
    if not transactions:
        return "0" * 64
    
    # Convert transactions to hashes
    hashes = []
    for tx in transactions:
        if hasattr(tx, 'hash'):
            hashes.append(tx.hash)
        else:
            hashes.append(calculate_sha256(str(tx)))
    
    # Build Merkle tree
    while len(hashes) > 1:
        new_hashes = []
        for i in range(0, len(hashes), 2):
            if i + 1 < len(hashes):
                combined = hashes[i] + hashes[i + 1]
            else:
                combined = hashes[i] + hashes[i]  # Duplicate if odd number
            new_hashes.append(calculate_sha256(combined))
        hashes = new_hashes
    
    return hashes[0]


def verify_merkle_proof(transaction_hash: str, merkle_proof: list, merkle_root: str) -> bool:
    """
    Verify a Merkle proof
    
    Args:
        transaction_hash: Hash of the transaction
        merkle_proof: List of hashes forming the proof
        merkle_root: Expected Merkle root
        
    Returns:
        bool: True if proof is valid
    """
    current_hash = transaction_hash
    
    for proof_hash in merkle_proof:
        # Try both combinations (proof could be left or right sibling)
        option1 = calculate_sha256(current_hash + proof_hash)
        option2 = calculate_sha256(proof_hash + current_hash)
        
        # Use the lexicographically smaller one for consistency
        current_hash = option1 if option1 < option2 else option2
    
    return current_hash == merkle_root


class SimpleSignature:
    """
    Simple signature implementation for demonstration
    Note: This is not cryptographically secure, only for simulation
    """
    
    @staticmethod
    def sign(message: str, private_key: str) -> str:
        """
        Sign a message with private key
        
        Args:
            message: Message to sign
            private_key: Private key for signing
            
        Returns:
            str: Signature
        """
        signature_data = f"{message}:{private_key}"
        return calculate_sha256(signature_data)
    
    @staticmethod
    def verify(message: str, signature: str, public_key: str) -> bool:
        """
        Verify a signature
        
        Args:
            message: Original message
            signature: Signature to verify
            public_key: Public key for verification
            
        Returns:
            bool: True if signature is valid
        """
        expected_signature = SimpleSignature.sign(message, public_key)
        return signature == expected_signature
    
    @staticmethod
    def generate_keypair() -> tuple:
        """
        Generate a simple key pair
        
        Returns:
            tuple: (private_key, public_key)
        """
        # Generate a random private key
        private_key = secrets.token_hex(32)
        # Public key is derived from private key (simplified)
        public_key = calculate_sha256(private_key)
        return private_key, public_key
