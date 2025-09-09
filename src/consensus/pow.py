"""
Proof of Work consensus implementation
"""

import time
import hashlib
import logging
import json
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
        
        # Logging setup
        self.logger = logging.getLogger(f'pow_consensus')
        self.log_mode = config.get('logging', {}).get('log_mode', 'structured')  # 'structured' or 'presentation'
    
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
        start_time = time.time()
        
        # Log mining start
        self._log_mining_start(height, proposer_id, len(transactions))
        
        # Create block with initial nonce
        block = Block(
            height=height,
            prev_hash=prev_hash,
            transactions=transactions,
            timestamp=time.time(),
            nonce=0
        )
        
        # Add proposer information
        block.proposer_id = proposer_id
        
        # Mine the block
        mined_block = self._mine_block_pow(block)
        
        # Log mining completion
        total_time_ms = (time.time() - start_time) * 1000
        self._log_block_mined(mined_block, total_time_ms)
        
        return mined_block
    
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
        hash_attempts = 0
        while True:
            # Check timeout
            current_time = time.time()
            if current_time - start_time > self.max_mining_time:
                mining_time_ms = (current_time - start_time) * 1000
                self._log_mining_timeout(block, hash_attempts, mining_time_ms)
                break
            
            # Try current nonce
            block.nonce = nonce
            block.hash = block.calculate_hash()
            hash_attempts += 1
            
            if block.hash.startswith(target):
                # Found valid proof of work
                mining_time_ms = (current_time - start_time) * 1000
                self._log_mining_success(block, hash_attempts, mining_time_ms)
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
        validation_start = time.time()
        is_valid = self.validate_proof(block)
        validation_time_ms = (time.time() - validation_start) * 1000
        
        if is_valid:
            self._log_validation_success(block, proposer_id, validation_time_ms)
        else:
            self._log_validation_failed(block, proposer_id, validation_time_ms)
        
        return is_valid
    
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
        old_difficulty = self.difficulty
        
        # Adjust difficulty based on how far off we are from target
        if avg_time < target_time * 0.5:
            new_difficulty = min(self.difficulty + 1, 8)  # Increase difficulty
        elif avg_time > target_time * 2:
            new_difficulty = max(self.difficulty - 1, 1)  # Decrease difficulty
        else:
            new_difficulty = self.difficulty
        
        # Log difficulty adjustment if changed
        if new_difficulty != old_difficulty:
            self._log_difficulty_adjustment(old_difficulty, new_difficulty, avg_time, target_time)
        
        return new_difficulty
    
    # ======================== LOGGING METHODS ========================
    
    def _log_mining_start(self, height: int, proposer_id: str, tx_count: int) -> None:
        """Log mining start event"""
        if self.log_mode == 'presentation':
            self.logger.info(f"⛏️ HEIGHT {height}: Node-{proposer_id} starting PoW mining (difficulty: {self.difficulty}, txs: {tx_count})")
        else:
            event_data = {
                "event": "mining_start",
                "height": height,
                "proposer_id": proposer_id,
                "difficulty": self.difficulty,
                "transaction_count": tx_count,
                "target": self.get_target(),
                "timestamp": time.time()
            }
            self.logger.info(f"POW_EVENT: {json.dumps(event_data)}")
    
    def _log_mining_success(self, block: Block, attempts: int, mining_time_ms: float) -> None:
        """Log successful mining completion"""
        if self.log_mode == 'presentation':
            hash_rate = attempts / (mining_time_ms / 1000) if mining_time_ms > 0 else 0
            self.logger.info(f"✅ HEIGHT {block.height}: PoW solved! Nonce: {block.nonce}, Attempts: {attempts}, Time: {mining_time_ms:.1f}ms ({hash_rate:.0f} H/s)")
        else:
            event_data = {
                "event": "mining_success",
                "height": block.height,
                "block_hash": block.hash,
                "nonce": block.nonce,
                "attempts": attempts,
                "mining_time_ms": mining_time_ms,
                "difficulty": self.difficulty,
                "hash_rate": attempts / (mining_time_ms / 1000) if mining_time_ms > 0 else 0,
                "timestamp": time.time()
            }
            self.logger.info(f"POW_EVENT: {json.dumps(event_data)}")
    
    def _log_mining_timeout(self, block: Block, attempts: int, mining_time_ms: float) -> None:
        """Log mining timeout"""
        if self.log_mode == 'presentation':
            hash_rate = attempts / (mining_time_ms / 1000) if mining_time_ms > 0 else 0
            self.logger.warning(f"⏰ HEIGHT {block.height}: Mining timeout after {attempts} attempts ({mining_time_ms:.1f}ms, {hash_rate:.0f} H/s)")
        else:
            event_data = {
                "event": "mining_timeout",
                "height": block.height,
                "attempts": attempts,
                "mining_time_ms": mining_time_ms,
                "difficulty": self.difficulty,
                "hash_rate": attempts / (mining_time_ms / 1000) if mining_time_ms > 0 else 0,
                "timestamp": time.time()
            }
            self.logger.warning(f"POW_EVENT: {json.dumps(event_data)}")
    
    def _log_block_mined(self, block: Block, total_time_ms: float) -> None:
        """Log completed block mining"""
        if self.log_mode == 'presentation':
            self.logger.info(f"✨ HEIGHT {block.height}: Block mined by Node-{getattr(block, 'proposer_id', 'unknown')} in {total_time_ms:.1f}ms (hash: {block.hash[:12]}...)")
        else:
            event_data = {
                "event": "block_mined",
                "height": block.height,
                "proposer_id": getattr(block, 'proposer_id', 'unknown'),
                "block_hash": block.hash,
                "total_time_ms": total_time_ms,
                "nonce": block.nonce,
                "transaction_count": len(block.transactions),
                "timestamp": time.time()
            }
            self.logger.info(f"POW_EVENT: {json.dumps(event_data)}")
    
    def _log_validation_success(self, block: Block, proposer_id: str, validation_time_ms: float) -> None:
        """Log successful block validation"""
        if self.log_mode == 'presentation':
            self.logger.info(f"✅ HEIGHT {block.height}: Block from Node-{proposer_id} validated in {validation_time_ms:.2f}ms")
        else:
            event_data = {
                "event": "block_validation_success",
                "height": block.height,
                "proposer_id": proposer_id,
                "block_hash": block.hash,
                "validation_time_ms": validation_time_ms,
                "timestamp": time.time()
            }
            self.logger.info(f"POW_EVENT: {json.dumps(event_data)}")
    
    def _log_validation_failed(self, block: Block, proposer_id: str, validation_time_ms: float) -> None:
        """Log failed block validation"""
        if self.log_mode == 'presentation':
            self.logger.warning(f"❌ HEIGHT {block.height}: Block from Node-{proposer_id} rejected (invalid PoW) in {validation_time_ms:.2f}ms")
        else:
            event_data = {
                "event": "block_validation_failed",
                "height": block.height,
                "proposer_id": proposer_id,
                "block_hash": block.hash,
                "validation_time_ms": validation_time_ms,
                "failure_reason": "invalid_pow",
                "timestamp": time.time()
            }
            self.logger.warning(f"POW_EVENT: {json.dumps(event_data)}")
    
    def _log_difficulty_adjustment(self, old_difficulty: int, new_difficulty: int, avg_time: float, target_time: float) -> None:
        """Log difficulty adjustment"""
        if self.log_mode == 'presentation':
            direction = "increased" if new_difficulty > old_difficulty else "decreased"
            self.logger.info(f"🎯 Difficulty {direction}: {old_difficulty} → {new_difficulty} (avg block time: {avg_time:.1f}s vs target: {target_time:.1f}s)")
        else:
            event_data = {
                "event": "difficulty_adjustment",
                "old_difficulty": old_difficulty,
                "new_difficulty": new_difficulty,
                "average_block_time": avg_time,
                "target_block_time": target_time,
                "adjustment_ratio": avg_time / target_time if target_time > 0 else 0,
                "timestamp": time.time()
            }
            self.logger.info(f"POW_EVENT: {json.dumps(event_data)}")
    
    def _log_partition_event(self, event_type: str, partition_info: dict) -> None:
        """Log partition-related events"""
        if self.log_mode == 'presentation':
            if event_type == 'partition_start':
                self.logger.info(f"🌐 NETWORK PARTITION: Network split detected")
            elif event_type == 'partition_heal':
                self.logger.info(f"🔗 NETWORK HEAL: Partitions reconnecting")
            elif event_type == 'chain_reorganization':
                self.logger.info(f"🔄 CHAIN REORG: Switching to longest chain")
            elif event_type == 'fork_resolution':
                winner_length = partition_info.get('winning_length', 0)
                self.logger.info(f"📏 FORK RESOLVED: Longest chain wins (length: {winner_length})")
        else:
            event_data = {
                "event": f"partition_{event_type}",
                "partition_info": partition_info,
                "timestamp": time.time()
            }
            self.logger.info(f"POW_EVENT: {json.dumps(event_data)}")
    
    def _log_chain_comparison(self, chain_a_length: int, chain_b_length: int, winner: str) -> None:
        """Log chain length comparison for longest chain rule"""
        if self.log_mode == 'presentation':
            self.logger.info(f"📏 CHAIN LENGTH: Chain A: {chain_a_length} vs Chain B: {chain_b_length} → Winner: {winner}")
        else:
            event_data = {
                "event": "chain_length_comparison",
                "chain_a_length": chain_a_length,
                "chain_b_length": chain_b_length,
                "winner": winner,
                "timestamp": time.time()
            }
            self.logger.info(f"POW_EVENT: {json.dumps(event_data)}")
    
    def _log_mining_competition(self, active_miners: int, partition_id: str = None) -> None:
        """Log mining competition status"""
        if self.log_mode == 'presentation':
            partition_text = f" (Partition {partition_id})" if partition_id else ""
            self.logger.info(f"⛏️  MINING COMPETITION: {active_miners} active miners{partition_text}")
        else:
            event_data = {
                "event": "mining_competition",
                "active_miners": active_miners,
                "partition_id": partition_id,
                "timestamp": time.time()
            }
            self.logger.info(f"POW_EVENT: {json.dumps(event_data)}")
