"""
Blockchain logic implementation
"""

import time
from typing import List, Dict, Optional, Tuple
from .block import Block
from .transaction import Transaction


class Blockchain:
    """
    Main blockchain implementation
    """
    
    def __init__(self, finality_depth: int = 4):
        """
        Initialize blockchain
        
        Args:
            finality_depth: Number of confirmations for finality (k parameter)
        """
        self.finality_depth = finality_depth
        self.main_chain: List[Block] = []
        self.all_blocks: Dict[str, Block] = {}  # hash -> block
        self.pending_transactions: List[Transaction] = []
        self.balances: Dict[str, float] = {}
        
        # Create and add genesis block
        genesis = self.create_genesis_block()
        self.main_chain.append(genesis)
        self.all_blocks[genesis.hash] = genesis
    
    def create_genesis_block(self) -> Block:
        """
        Create the genesis block
        
        Returns:
            Block: Genesis block
        """
        return Block(
            height=0,
            prev_hash="0" * 64,
            transactions=[],
            timestamp=time.time(),
            nonce=0
        )
    
    def get_latest_block(self) -> Block:
        """
        Get the latest block in the main chain
        
        Returns:
            Block: Latest block
        """
        return self.main_chain[-1] if self.main_chain else self.create_genesis_block()
    
    def is_valid_block(self, block: Block) -> bool:
        """
        Validate block structure and transactions
        
        Args:
            block: Block to validate
            
        Returns:
            bool: True if block is valid
        """
        # Check if previous block exists
        if block.height > 0:
            prev_block = self.all_blocks.get(block.prev_hash)
            if prev_block is None:
                return False
            
            # Check height is sequential
            if block.height != prev_block.height + 1:
                return False
        
        # Validate all transactions
        for tx in block.transactions:
            if isinstance(tx, Transaction) and not self.validate_transaction(tx):
                return False
        
        return True
    
    def add_block(self, block: Block) -> bool:
        """
        Add block to the blockchain and handle forks
        
        Args:
            block: Block to add
            
        Returns:
            bool: True if block was added successfully
        """
        if not self.is_valid_block(block):
            return False
        
        # Add to all blocks
        self.all_blocks[block.hash] = block
        
        # Check if this extends the main chain
        if block.prev_hash == self.get_latest_block().hash:
            self.main_chain.append(block)
            # Update balances when new block is added to main chain
            self.update_balances_from_block(block)
        else:
            # Fork detected - need to resolve
            self.resolve_forks()
            # After fork resolution, recalculate all balances
            self.recalculate_balances()
        
        return True
    
    def get_final_blocks(self) -> List[Block]:
        """
        Return blocks that are final (depth >= k)
        
        Returns:
            List[Block]: List of final blocks
        """
        chain_length = len(self.main_chain)
        if chain_length <= self.finality_depth:
            return self.main_chain[:1]  # Only genesis is final
        
        final_count = chain_length - self.finality_depth
        return self.main_chain[:final_count]
    
    def get_chain_length(self) -> int:
        """
        Get the length of the main chain
        
        Returns:
            int: Chain length
        """
        return len(self.main_chain)
    
    def get_finality_height(self) -> int:
        """
        Get the height of the highest finalized block
        
        Returns:
            int: Height of the highest finalized block
        """
        chain_length = len(self.main_chain)
        if chain_length <= self.finality_depth:
            return 0  # Only genesis is final
        
        return chain_length - self.finality_depth - 1
    
    def resolve_forks(self) -> None:
        """
        Resolve forks using the longest chain rule
        """
        # Find all possible chains starting from genesis
        all_chains = self._find_all_chains()
        
        if not all_chains:
            return
        
        # Select longest chain (ties broken by hash)
        best_chain = max(all_chains, key=lambda chain: (len(chain), chain[-1].hash))
        
        # Update main chain if a longer one is found
        if len(best_chain) > len(self.main_chain):
            self.main_chain = best_chain
    
    def _find_all_chains(self) -> List[List[Block]]:
        """Find all valid chains from genesis"""
        if not self.main_chain:
            return []
        
        chains = []
        genesis = self.main_chain[0]
        
        def build_chain(current_chain: List[Block], last_block: Block):
            chains.append(current_chain[:])  # Copy current chain
            
            # Find all blocks that extend this chain
            for block in self.all_blocks.values():
                if block.prev_hash == last_block.hash and block not in current_chain:
                    current_chain.append(block)
                    build_chain(current_chain, block)
                    current_chain.pop()
        
        build_chain([genesis], genesis)
        return chains
    
    def get_balance(self, address: str) -> float:
        """
        Get current balance for an address
        
        Args:
            address: Address to check balance for
            
        Returns:
            float: Current balance
        """
        return self.balances.get(address, 0.0)
    
    def validate_transaction(self, transaction: Transaction) -> bool:
        """
        Validate a transaction against the current state
        
        Args:
            transaction: Transaction to validate
            
        Returns:
            bool: True if transaction is valid
        """
        # Check for positive amount
        if transaction.amount <= 0:
            return False
        
        # Check sender has sufficient balance
        sender_balance = self.get_balance(transaction.sender)
        if sender_balance < transaction.amount:
            return False
        
        # Check for double spending in pending transactions
        for pending_tx in self.pending_transactions:
            if (pending_tx.sender == transaction.sender and 
                pending_tx.hash != transaction.hash):
                # This is a simplified check
                continue
        
        return True
    
    def add_pending_transaction(self, transaction: Transaction) -> None:
        """
        Add transaction to pending pool
        
        Args:
            transaction: Transaction to add
        """
        if self.validate_transaction(transaction):
            self.pending_transactions.append(transaction)
    
    def get_pending_transactions(self, max_count: int = 10) -> List[Transaction]:
        """
        Get pending transactions for block creation
        
        Args:
            max_count: Maximum number of transactions to return
            
        Returns:
            List[Transaction]: List of pending transactions
        """
        # Return up to max_count transactions (don't remove them yet)
        selected = self.pending_transactions[:max_count]
        return selected
    
    def remove_transactions(self, transactions: List[Transaction]) -> None:
        """
        Remove transactions from pending pool after successful mining
        
        Args:
            transactions: Transactions to remove
        """
        tx_hashes = {tx.hash for tx in transactions}
        self.pending_transactions = [
            tx for tx in self.pending_transactions 
            if tx.hash not in tx_hashes
        ]
    
    def update_balances_from_block(self, block: Block) -> None:
        """
        Update balances from a newly added block
        
        Args:
            block: Block to process transactions from
        """
        for tx in block.transactions:
            if isinstance(tx, Transaction):
                # Deduct from sender
                sender_balance = self.balances.get(tx.sender, 0.0)
                self.balances[tx.sender] = sender_balance - tx.amount
                
                # Add to receiver
                receiver_balance = self.balances.get(tx.receiver, 0.0)
                self.balances[tx.receiver] = receiver_balance + tx.amount
    
    def recalculate_balances(self) -> None:
        """
        Recalculate all balances from scratch based on the main chain
        """
        # Reset balances to initial values
        initial_balances = {node_id: balance for node_id, balance in self.balances.items()}
        
        # Process all transactions in the main chain
        for block in self.main_chain[1:]:  # Skip genesis block
            self.update_balances_from_block(block)
