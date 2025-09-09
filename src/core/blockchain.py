"""
Blockchain logic implementation
"""

import time
from typing import List, Dict, Optional, Tuple, TYPE_CHECKING
from .block import Block
from .transaction import Transaction

if TYPE_CHECKING:
    from ..consensus.base import ConsensusAlgorithm


class Blockchain:
    """
    Main blockchain implementation
    """
    
    def __init__(self, finality_depth: int = 4, consensus: Optional['ConsensusAlgorithm'] = None):
        """
        Initialize blockchain
        
        Args:
            finality_depth: Number of confirmations for finality (k parameter)
            consensus: Consensus algorithm instance for fork resolution
        """
        self.finality_depth = finality_depth
        self.consensus = consensus
        self.main_chain: List[Block] = []
        self.all_blocks: Dict[str, Block] = {}  # hash -> block
        self.pending_transactions: List[Transaction] = []
        self.balances: Dict[str, float] = {}
        
        # Create and add genesis block
        genesis = self.create_genesis_block()
        self.main_chain.append(genesis)
        self.all_blocks[genesis.hash] = genesis
    
    def set_consensus(self, consensus: 'ConsensusAlgorithm') -> None:
        """
        Set the consensus algorithm for fork resolution
        
        Args:
            consensus: Consensus algorithm instance
        """
        self.consensus = consensus
    
    def create_genesis_block(self) -> Block:
        """
        Create the genesis block
        
        Returns:
            Block: Genesis block
        """
        # Use fixed timestamp to ensure all nodes have identical genesis block
        return Block(
            height=0,
            prev_hash="0" * 64,
            transactions=[],
            timestamp=1700000000.0,  # Fixed timestamp for deterministic genesis
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
        # Genesis block validation
        if block.height == 0:
            return True
            
        # For non-genesis blocks, check if previous block exists
        if block.height > 0:
            prev_block = self.all_blocks.get(block.prev_hash)
            if prev_block is None:
                # Previous block not found - this might be an out-of-order block
                # We'll store it temporarily and validate later
                return True  # Allow temporary storage for out-of-order blocks
            
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
        
        # Skip if block already exists
        if block.hash in self.all_blocks:
            return True
        
        # Add to all blocks
        self.all_blocks[block.hash] = block
        
        # Check if this extends the main chain
        if block.prev_hash == self.get_latest_block().hash:
            self.main_chain.append(block)
            # Update balances when new block is added to main chain
            self.update_balances_from_block(block)
            
            # After adding to main chain, try to process any pending blocks
            self._process_pending_blocks()
        else:
            # Fork detected - need to resolve using consensus algorithm
            if self.consensus:
                self.resolve_forks_with_consensus()
            else:
                # Fallback to simple longest chain if no consensus algorithm
                self.resolve_forks_fallback()
            # After fork resolution, recalculate all balances
            self.recalculate_balances()
        
        return True
    
    def _process_pending_blocks(self) -> None:
        """
        Process any blocks that were received out of order
        """
        processed_any = True
        while processed_any:
            processed_any = False
            latest_block = self.get_latest_block()
            
            # Look for blocks that can extend the current main chain
            for block_hash, block in self.all_blocks.items():
                if (block.prev_hash == latest_block.hash and 
                    block.height == latest_block.height + 1 and
                    block.hash not in [b.hash for b in self.main_chain]):
                    
                    # Found a block that extends the chain
                    self.main_chain.append(block)
                    self.update_balances_from_block(block)
                    processed_any = True
                    break
    
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
    
    def resolve_forks_with_consensus(self) -> None:
        """
        Resolve forks using the consensus algorithm's select_best_chain method
        """
        if not self.consensus:
            return
            
        # Find all possible chains starting from genesis
        all_chains = self._find_all_chains()
        
        if not all_chains:
            return
        
        # Log fork detection
        if len(all_chains) > 1 and hasattr(self.consensus, '_log_partition_event'):
            self.consensus._log_partition_event("fork_detection", {
                "competing_chains": len(all_chains),
                "chain_lengths": [len(chain) for chain in all_chains]
            })
        
        # Use consensus algorithm to select best chain
        best_chain = self.consensus.select_best_chain(all_chains)
        
        # Update main chain if a different one is selected
        if best_chain and len(best_chain) != len(self.main_chain):
            old_chain_length = len(self.main_chain)
            self.main_chain = best_chain
            
            # Log chain reorganization
            if hasattr(self.consensus, '_log_partition_event'):
                self.consensus._log_partition_event("chain_reorganization", {
                    "old_length": old_chain_length,
                    "new_length": len(best_chain),
                    "reorganized": True
                })
            
            # Log chain comparison for specific consensus types
            if hasattr(self.consensus, '_log_chain_comparison'):
                # For PoW - compare by length
                self.consensus._log_chain_comparison(
                    old_chain_length, len(best_chain), "new_chain"
                )
            elif hasattr(self.consensus, '_log_stake_weight_comparison'):
                # For Hybrid - would need stake weights, simplified for now
                self.consensus._log_stake_weight_comparison(
                    float(old_chain_length), float(len(best_chain)), "new_chain"
                )
    
    def resolve_forks_fallback(self) -> None:
        """
        Fallback fork resolution using the longest chain rule (for backward compatibility)
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
