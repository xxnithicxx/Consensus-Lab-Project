import time
import logging
import threading
from typing import Dict, Optional, Set
from ..core.blockchain import Blockchain
from ..core.block import Block
from ..core.transaction import Transaction
from ..consensus.base import ConsensusAlgorithm
from ..consensus.pow import ProofOfWork
from ..consensus.hybrid import HybridConsensus
from .messages import NetworkMessage, MessageType
from .socket_network import SocketNetworkSimulator


class SocketNode:
    """
    Socket-based blockchain node that can communicate across processes
    """
    
    def __init__(self, node_id: str, initial_balance: float, consensus_type: str, 
                 consensus_config: dict, network_config: dict):
        """
        Initialize a socket-based blockchain node
        
        Args:
            node_id: Unique identifier for this node
            initial_balance: Initial balance for this node
            consensus_type: Type of consensus ('pow' or 'hybrid')
            consensus_config: Configuration for consensus algorithm
            network_config: Network configuration
        """
        self.node_id = node_id
        self.initial_balance = initial_balance
        self.consensus_type = consensus_type
        self.network_config = network_config
        
        # Initialize blockchain
        self.blockchain = Blockchain(finality_depth=consensus_config.get('finality_depth', 4))
        
        # Initialize consensus algorithm
        self.consensus = self.create_consensus(consensus_type, consensus_config)
        
        # Network state
        self.peers: Set[str] = {'0', '1', '2', '3', '4'}
        self.peers.discard(node_id)  # Remove self
        self.is_running = False
        
        # Socket network
        self.socket_network: Optional[SocketNetworkSimulator] = None
        
        # Threading
        self.process_thread: Optional[threading.Thread] = None
        self.mining_thread: Optional[threading.Thread] = None
        
        # Logging
        self.logger = logging.getLogger(f'node_{node_id}')
        
        # Initialize balance
        self.blockchain.balances[node_id] = initial_balance
        
    def create_consensus(self, consensus_type: str, config: dict) -> ConsensusAlgorithm:
        """Create consensus algorithm instance"""
        if consensus_type == 'pow':
            return ProofOfWork(config)
        elif consensus_type == 'hybrid':
            return HybridConsensus(config)
        else:
            raise ValueError(f"Unknown consensus type: {consensus_type}")
    
    def start(self) -> None:
        """Start the node and begin processing"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Initialize socket network
        self.socket_network = SocketNetworkSimulator(self.node_id)
        self.socket_network.start()
        
        # Start message processing thread
        self.process_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.process_thread.start()
        
        # Start mining thread
        self.mining_thread = threading.Thread(target=self._mining_loop, daemon=True)
        self.mining_thread.start()
        
        self.logger.info(f"Socket node {self.node_id} started")
    
    def stop(self) -> None:
        """Stop the node"""
        self.is_running = False
        
        if self.socket_network:
            self.socket_network.stop()
            
        self.logger.info(f"Socket node {self.node_id} stopped")
    
    def send_message(self, message: NetworkMessage) -> None:
        """Send message via socket network"""
        if not self.socket_network:
            return
            
        if message.receiver_id is None:
            # Broadcast message
            self.socket_network.broadcast_message(message)
        else:
            # Direct message
            self.socket_network.send_message(message.receiver_id, message)
    
    def broadcast_transaction(self, transaction: Transaction) -> None:
        """Broadcast transaction to all peers"""
        # Add to our own pending transactions first
        self.blockchain.add_pending_transaction(transaction)
        
        message = NetworkMessage(
            sender_id=self.node_id,
            receiver_id=None,  # Broadcast
            message_type=MessageType.TRANSACTION_BROADCAST,
            payload=transaction
        )
        self.send_message(message)
        
        self.log_event("transaction_broadcast", {
            "hash": transaction.hash,
            "receiver": transaction.receiver,
            "amount": transaction.amount
        })
    
    def propose_block(self, block: Block) -> None:
        """Propose a new block to the network"""
        message = NetworkMessage(
            sender_id=self.node_id,
            receiver_id=None,  # Broadcast
            message_type=MessageType.BLOCK_PROPOSAL,
            payload=block
        )
        self.send_message(message)
        
        self.log_event("block_proposed", {
            "height": block.height,
            "hash": block.hash,
            "transactions": len(block.transactions)
        })
    
    def create_transaction(self, receiver: str, amount: float) -> Optional[Transaction]:
        """Create a new transaction"""
        if self.get_balance() < amount:
            self.logger.warning(f"Insufficient balance for transaction: {amount}")
            return None
        
        transaction = Transaction(
            sender=self.node_id,
            receiver=receiver,
            amount=amount,
            timestamp=time.time()
        )
        
        return transaction
    
    def get_balance(self) -> float:
        """Get current balance of this node"""
        return self.blockchain.get_balance(self.node_id)
    
    def get_blockchain_info(self) -> Dict:
        """Get blockchain information"""
        chain = self.blockchain.main_chain
        latest_block = chain[-1] if chain else None
        
        return {
            "chain_length": len(chain),
            "latest_block_hash": latest_block.hash if latest_block else None,
            "latest_block_height": latest_block.height if latest_block else -1,
            "final_height": self.blockchain.get_finality_height(),
            "balance": self.get_balance(),
            "pending_transactions": len(self.blockchain.pending_transactions)
        }
    
    def set_partition(self, allowed_peers: Set[str]) -> None:
        """Set network partition"""
        if self.socket_network:
            self.socket_network.set_partition(allowed_peers)
    
    def heal_partition(self) -> None:
        """Heal network partition"""
        if self.socket_network:
            self.socket_network.heal_partition()
    
    def log_event(self, event_type: str, data: Dict) -> None:
        """Log an event with structured data"""
        event = {
            'timestamp': time.time(),
            'node_id': self.node_id,
            'event_type': event_type,
            'data': data
        }
        self.logger.info(f"EVENT: {event}")
    
    def _process_loop(self) -> None:
        """Main message processing loop"""
        while self.is_running:
            try:
                if not self.socket_network:
                    time.sleep(0.1)
                    continue
                    
                message = self.socket_network.get_message(timeout=0.1)
                if message:
                    self._handle_message(message)
                    
            except Exception as e:
                self.logger.error(f"Error in process loop: {e}")
                time.sleep(1)
    
    def _handle_message(self, message: NetworkMessage) -> None:
        """Handle received message"""
        try:
            if message.message_type == MessageType.BLOCK_PROPOSAL:
                self._handle_block_proposal(message)
            elif message.message_type == MessageType.TRANSACTION_BROADCAST:
                self._handle_transaction_broadcast(message)
            else:
                self.logger.warning(f"Unknown message type: {message.message_type}")
                
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
    
    def _handle_block_proposal(self, message: NetworkMessage) -> None:
        """Handle block proposal message"""
        try:
            # The payload should already be a Block object due to NetworkMessage.from_dict
            block = message.payload
            if not isinstance(block, Block):
                # Fallback: reconstruct from dict if needed
                block = Block.from_dict(block)
            
            # Validate and add block
            if self.blockchain.is_valid_block(block):
                success = self.blockchain.add_block(block)
                if success:
                    self.logger.info(f"Added block {block.height} from {message.sender_id}")
                    
            self.log_event("block_received", {
                "height": block.height,
                "hash": block.hash,
                "proposer": message.sender_id
            })
            
        except Exception as e:
            self.logger.error(f"Error handling block proposal: {e}")
    
    def _handle_transaction_broadcast(self, message: NetworkMessage) -> None:
        """Handle transaction broadcast message"""
        try:
            # The payload should already be a Transaction object due to NetworkMessage.from_dict
            transaction = message.payload
            if not isinstance(transaction, Transaction):
                # Fallback: reconstruct from dict if needed
                transaction = Transaction.from_dict(transaction)
            
            # Add to pending transactions
            self.blockchain.add_pending_transaction(transaction)
            
            self.log_event("transaction_received", {
                "hash": transaction.hash,
                "sender": transaction.sender,
                "receiver": transaction.receiver,
                "amount": transaction.amount
            })
            
        except Exception as e:
            self.logger.error(f"Error handling transaction broadcast: {e}")
    
    def _mining_loop(self) -> None:
        """Mining loop for consensus algorithms"""
        while self.is_running:
            try:
                # Check if we have pending transactions and can mine
                pending_count = len(self.blockchain.pending_transactions)
                if pending_count > 0:
                    self.logger.debug(f"Attempting to mine block with {pending_count} pending transactions")
                    # Try to mine a block
                    block = self.consensus.mine_block(
                        self.blockchain,
                        self.node_id,
                        max_transactions=10
                    )
                    
                    if block:
                        # Add to our blockchain
                        if self.blockchain.add_block(block):
                            self.logger.info(f"Mined block {block.height} with {len(block.transactions)} transactions")
                            # Broadcast to network
                            self.propose_block(block)
                            
                            self.log_event("block_created", {
                                "height": block.height,
                                "hash": block.hash,
                                "transactions": len(block.transactions)
                            })
                    else:
                        self.logger.debug(f"Mining attempt failed - no block produced")
                
                # Adjust sleep time based on consensus type
                if self.consensus_type == 'pow':
                    time.sleep(0.5)  # PoW mining delay
                else:  # hybrid
                    time.sleep(0.3)  # Hybrid is faster
                
            except Exception as e:
                self.logger.error(f"Error in mining loop: {e}")
                time.sleep(1)
