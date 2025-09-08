"""
Message types for network communication
"""

import time
from enum import Enum
from typing import Any, Dict, Optional, Union
from ..core.block import Block
from ..core.transaction import Transaction


class MessageType(Enum):
    """Types of messages in the network"""
    BLOCK_PROPOSAL = "block_proposal"
    BLOCK_CONFIRMATION = "block_confirmation"
    TRANSACTION_BROADCAST = "transaction_broadcast"
    CHAIN_REQUEST = "chain_request"
    CHAIN_RESPONSE = "chain_response"
    HEARTBEAT = "heartbeat"
    PARTITION_HEAL = "partition_heal"


class NetworkMessage:
    """
    Represents a message in the network
    """
    
    def __init__(self, sender_id: str, receiver_id: Optional[str], message_type: MessageType, 
                 payload: Any, timestamp: Optional[float] = None):
        """
        Initialize a network message
        
        Args:
            sender_id: ID of sending node
            receiver_id: ID of receiving node (None for broadcast)
            message_type: Type of message
            payload: Message payload
            timestamp: Message timestamp
        """
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.message_type = message_type
        self.payload = payload
        self.timestamp = timestamp if timestamp is not None else time.time()
    
    def to_dict(self) -> Dict:
        """
        Convert message to dictionary
        
        Returns:
            Dict: Message as dictionary
        """
        payload_dict = self.payload
        if hasattr(self.payload, 'to_dict'):
            payload_dict = self.payload.to_dict()
        elif isinstance(self.payload, list):
            payload_dict = [item.to_dict() if hasattr(item, 'to_dict') else item for item in self.payload]
        
        return {
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'message_type': self.message_type.value,
            'payload': payload_dict,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """
        Create message from dictionary
        
        Args:
            data: Message data as dictionary
            
        Returns:
            NetworkMessage: New message instance
        """
        message_type = MessageType(data['message_type'])
        
        # Reconstruct payload based on message type
        payload = data['payload']
        if message_type == MessageType.BLOCK_PROPOSAL and isinstance(payload, dict):
            payload = Block.from_dict(payload)
        elif message_type == MessageType.TRANSACTION_BROADCAST and isinstance(payload, dict):
            payload = Transaction.from_dict(payload)
        elif message_type == MessageType.CHAIN_RESPONSE and isinstance(payload, list):
            payload = [Block.from_dict(block_data) if isinstance(block_data, dict) else block_data 
                      for block_data in payload]
        
        return cls(
            sender_id=data['sender_id'],
            receiver_id=data['receiver_id'],
            message_type=message_type,
            payload=payload,
            timestamp=data['timestamp']
        )


class BlockProposal(NetworkMessage):
    """Message for proposing a new block"""
    
    def __init__(self, sender_id: str, block: Block, timestamp: Optional[float] = None):
        """
        Initialize block proposal message
        
        Args:
            sender_id: ID of proposing node
            block: Block being proposed
            timestamp: Message timestamp
        """
        super().__init__(
            sender_id=sender_id,
            receiver_id=None,  # Broadcast
            message_type=MessageType.BLOCK_PROPOSAL,
            payload=block,
            timestamp=timestamp
        )


class TransactionBroadcast(NetworkMessage):
    """Message for broadcasting a transaction"""
    
    def __init__(self, sender_id: str, transaction: Transaction, timestamp: Optional[float] = None):
        """
        Initialize transaction broadcast message
        
        Args:
            sender_id: ID of sending node
            transaction: Transaction being broadcast
            timestamp: Message timestamp
        """
        super().__init__(
            sender_id=sender_id,
            receiver_id=None,  # Broadcast
            message_type=MessageType.TRANSACTION_BROADCAST,
            payload=transaction,
            timestamp=timestamp
        )


class ChainRequest(NetworkMessage):
    """Message requesting chain synchronization"""
    
    def __init__(self, sender_id: str, receiver_id: str, from_height: int, timestamp: Optional[float] = None):
        """
        Initialize chain request message
        
        Args:
            sender_id: ID of requesting node
            receiver_id: ID of target node
            from_height: Starting height for chain request
            timestamp: Message timestamp
        """
        super().__init__(
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=MessageType.CHAIN_REQUEST,
            payload={'from_height': from_height},
            timestamp=timestamp
        )


class ChainResponse(NetworkMessage):
    """Message responding with chain data"""
    
    def __init__(self, sender_id: str, receiver_id: str, blocks: list, timestamp: Optional[float] = None):
        """
        Initialize chain response message
        
        Args:
            sender_id: ID of responding node
            receiver_id: ID of requesting node
            blocks: List of blocks being sent
            timestamp: Message timestamp
        """
        super().__init__(
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=MessageType.CHAIN_RESPONSE,
            payload=blocks,
            timestamp=timestamp
        )
