"""
Simple TCP socket-based network communication for blockchain nodes
"""

import socket
import json
import threading
import time
import logging
from typing import Dict, Optional, Callable
from queue import Queue, Empty
from .messages import NetworkMessage, MessageType


class SocketServer:
    """Simple TCP server for receiving messages"""
    
    def __init__(self, node_id: str, port: int, message_handler: Callable):
        self.node_id = node_id
        self.port = port
        self.message_handler = message_handler
        self.server_socket: Optional[socket.socket] = None
        self.is_running = False
        self.server_thread: Optional[threading.Thread] = None
        self.logger = logging.getLogger(f'socket_server_{node_id}')
        
    def start(self):
        """Start the TCP server"""
        if self.is_running:
            return
            
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('localhost', self.port))
            self.server_socket.listen(5)
            self.is_running = True
            
            self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
            self.server_thread.start()
            
            self.logger.info(f"Socket server started on port {self.port}")
            
        except Exception as e:
            self.logger.error(f"Failed to start socket server: {e}")
            raise
            
    def stop(self):
        """Stop the TCP server"""
        self.is_running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        self.logger.info("Socket server stopped")
        
    def _server_loop(self):
        """Main server loop to accept connections"""
        while self.is_running and self.server_socket:
            try:
                self.server_socket.settimeout(1.0)  # Timeout to check is_running
                client_socket, address = self.server_socket.accept()
                
                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self._handle_client, 
                    args=(client_socket,), 
                    daemon=True
                )
                client_thread.start()
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.is_running:
                    self.logger.error(f"Server loop error: {e}")
                break
                
    def _handle_client(self, client_socket: socket.socket):
        """Handle individual client connection"""
        try:
            # Receive message length first (4 bytes)
            length_data = self._recv_exact(client_socket, 4)
            if not length_data:
                return
                
            message_length = int.from_bytes(length_data, byteorder='big')
            
            # Receive the actual message
            message_data = self._recv_exact(client_socket, message_length)
            if not message_data:
                return
                
            # Decode and handle message
            message_json = message_data.decode('utf-8')
            message_dict = json.loads(message_json)
            
            # Convert back to NetworkMessage object
            message = NetworkMessage(
                sender_id=message_dict['sender_id'],
                receiver_id=message_dict.get('receiver_id'),
                message_type=MessageType(message_dict['message_type']),
                payload=message_dict['payload'],
                timestamp=message_dict['timestamp']
            )
            
            # Handle the message
            self.message_handler(message)
            
        except Exception as e:
            self.logger.error(f"Error handling client: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
                
    def _recv_exact(self, sock: socket.socket, length: int) -> bytes:
        """Receive exactly 'length' bytes from socket"""
        data = b''
        while len(data) < length:
            chunk = sock.recv(length - len(data))
            if not chunk:
                break
            data += chunk
        return data


class SocketClient:
    """Simple TCP client for sending messages"""
    
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.logger = logging.getLogger(f'socket_client_{node_id}')
        
    def send_message(self, target_port: int, message: NetworkMessage) -> bool:
        """Send message to target node via TCP"""
        try:
            # Convert message to JSON using the message's to_dict method
            message_dict = message.to_dict()
            message_json = json.dumps(message_dict)
            message_bytes = message_json.encode('utf-8')
            
            # Connect and send
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5.0)  # 5 second timeout
                sock.connect(('localhost', target_port))
                
                # Send message length first (4 bytes)
                length_bytes = len(message_bytes).to_bytes(4, byteorder='big')
                sock.send(length_bytes)
                
                # Send the actual message
                sock.send(message_bytes)
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send message to port {target_port}: {e}")
            return False


class SocketNetworkSimulator:
    """
    Network simulator using TCP sockets for inter-process communication
    """
    
    def __init__(self, node_id: str, base_port: int = 9000):
        self.node_id = node_id
        self.base_port = base_port
        self.my_port = base_port + int(node_id)
        
        # Node ports mapping (node_id -> port)
        self.node_ports = {
            '0': base_port + 0,
            '1': base_port + 1, 
            '2': base_port + 2,
            '3': base_port + 3,
            '4': base_port + 4
        }
        
        # Message handling
        self.message_queue: Queue = Queue()
        self.server: Optional[SocketServer] = None
        self.client: Optional[SocketClient] = None
        
        # Network state
        self.is_running = False
        self.partitioned = False
        self.allowed_peers = set(['0', '1', '2', '3', '4'])
        self.allowed_peers.discard(node_id)  # Remove self
        
        # Statistics
        self.messages_sent = 0
        self.messages_received = 0
        
        self.logger = logging.getLogger(f'socket_network_{node_id}')
        
    def start(self):
        """Start the socket network"""
        if self.is_running:
            return
            
        try:
            # Start server to receive messages
            self.server = SocketServer(self.node_id, self.my_port, self._handle_received_message)
            self.server.start()
            
            # Create client for sending messages
            self.client = SocketClient(self.node_id)
            
            self.is_running = True
            self.logger.info(f"Socket network started on port {self.my_port}")
            
            # Wait a bit for all nodes to start their servers
            time.sleep(1.0)
            
        except Exception as e:
            self.logger.error(f"Failed to start socket network: {e}")
            raise
            
    def stop(self):
        """Stop the socket network"""
        self.is_running = False
        
        if self.server:
            self.server.stop()
            
        self.logger.info("Socket network stopped")
        
    def send_message(self, receiver_id: str, message: NetworkMessage) -> bool:
        """Send message to specific receiver"""
        if not self.is_running or not self.client:
            return False
            
        # Check if we can communicate with this receiver
        if self.partitioned and receiver_id not in self.allowed_peers:
            self.logger.debug(f"Cannot send to {receiver_id} - partitioned")
            return False
            
        target_port = self.node_ports.get(receiver_id)
        if not target_port:
            self.logger.error(f"Unknown receiver: {receiver_id}")
            return False
            
        success = self.client.send_message(target_port, message)
        if success:
            self.messages_sent += 1
            self.logger.debug(f"Sent {message.message_type.value} to {receiver_id}")
        
        return success
        
    def broadcast_message(self, message: NetworkMessage) -> int:
        """Broadcast message to all peers"""
        sent_count = 0
        
        for peer_id in self.allowed_peers:
            if self.send_message(peer_id, message):
                sent_count += 1
                
        return sent_count
        
    def get_message(self, timeout: float = 0.1) -> Optional[NetworkMessage]:
        """Get received message from queue"""
        try:
            return self.message_queue.get(timeout=timeout)
        except Empty:
            return None
            
    def set_partition(self, allowed_peers: set):
        """Set network partition - only communicate with allowed peers"""
        self.partitioned = True
        self.allowed_peers = allowed_peers.copy()
        self.allowed_peers.discard(self.node_id)  # Remove self
        self.logger.info(f"Network partitioned. Allowed peers: {self.allowed_peers}")
        
    def heal_partition(self):
        """Heal network partition - communicate with all peers"""
        self.partitioned = False
        self.allowed_peers = {'0', '1', '2', '3', '4'}
        self.allowed_peers.discard(self.node_id)  # Remove self
        self.logger.info("Network partition healed")
        
    def get_stats(self) -> Dict:
        """Get network statistics"""
        return {
            'node_id': self.node_id,
            'port': self.my_port,
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'partitioned': self.partitioned,
            'allowed_peers': list(self.allowed_peers),
            'is_running': self.is_running
        }
        
    def _handle_received_message(self, message: NetworkMessage):
        """Handle message received from socket server"""
        self.messages_received += 1
        self.message_queue.put(message)
        self.logger.debug(f"Received {message.message_type.value} from {message.sender_id}")
