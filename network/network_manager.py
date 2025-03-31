import socket 
import threading 
import time 
import pickle 
from network.message_protocol import Message, MessageType, serialize_message, deserialize_message


# Network constants
DEFAULT_SERVER = "5.189.149.215" # Default server address
DEFAULT_PORT = 5555 # Default port for the server
BUFFER_SIZE = 4096 # Size of the buffer for receiving messages

class NetworkManager:
    def __init__(self, game_controller):
        self.controller =game_controller # Reference to the game controller
        self.server_soket = None # Socket for the server connection
        self.client_id = None # ID of the client
        self.plyaer_name = "Player" # Name of the player
        self.conneted = False # Flag to check if the client is connected
        self.running = False # Flag to check if the network manager is running
        self.game_id = None # ID of the game
        self.my_faction = None # Faction of the player

        # Game state info
        self.players = {} # Dictionary to store player information
        self.is_host = False # Flag to check if the player is the host
        self.game_state = {} # Dictionary to store the game state
        self.chat_messages = [] # List to store chat messages
        self.available_games = [] # List to store available games

        
        # Register message handlers
        self.message_handlers = {
            MessageType.REGISTER_RESPONSE: self._handle_register_response,
            MessageType.GAME_STATE: self._handle_game_state,
            MessageType.GAME_LIST: self._handle_game_list,
            MessageType.GAME_CREATED: self._handle_game_created,
            MessageType.JOIN_RESPONSE: self._handle_join_response,
            MessageType.PLAYER_JOINED: self._handle_player_joined,
            MessageType.PLAYER_LEFT: self._handle_player_left,
            MessageType.GAME_STARTED: self._handle_game_started,
            MessageType.TURN_CHANGED: self._handle_turn_changed,
            MessageType.UNIT_MOVED: self._handle_unit_moved,
            MessageType.ATTACK_RESULT: self._handle_attack_result,
            MessageType.GAME_ENDED: self._handle_game_ended,
            MessageType.ACTION_RESPONSE: self._handle_action_response,
        }

    def connect_to_server(self, player_name, server_ip=DEFAULT_SERVER, port=DEFAULT_PORT):
        """Connect to the game server"""
        try:
            self.player_name = player_name # Set the player name

            # Create a socket for the server connection
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.connect((server_ip, port)) # Connect to the server

            # Register the player with the server
            register_msg = Message.register(player_name) # Create a register message
            self.send_message(register_msg) # Send the register message

            # Start the network thread to listen for incoming messages
            self.running = True # Set the running flag to True
            self.recieve_thread = threading.Thread(target=self._receive_from_server) # Create a thread for receiving messages
            self.recieve_thread.daemon = True # Set the thread as a daemon
            self.recieve_thread.start() # Start the thread

            return True, f"Connectong to server {server_ip}:{port} as {player_name}, Please wait..." # Return success message
        
        except Exception as e:
            print(f"Error connecting to server: {e}") # Print error message
            return False, f"Failed to connect to server: {e}" # Return failure message
    
    def _recieve_from_server(self):
        """Thread function to receive messages from the server"""
        try:
            while self.running:
                try:
                    data = self.server_socket.recv(BUFFER_SIZE) # Receive data from the server
                    if not data:
                        # Connection closed by server
                        self.connected = False # Set connected flag to False
                        self.controller.on_disconnection_lost() # Notify the controller about disconnection
                        break # Break the loop
                        
                    message = deserialize_message(data) # Deserialize the received data
                    self._process_server_message(message) # Process the received message
                
                except socket.timeout:
                    # Non-blocking socket timeout, continue
                    pass # Ignore timeout errors
                
                except Exception as e:
                    print(f"Error receiving data from server: {e}, please try again.") # Print error message
                    self.connected = False # Set connected flag to False
                    self.controller.on_disconnection_lost() # Notify the controller about disconnection
                    break # Break the loop

                # Small delay to prevent high CPU usage(CPU antihogging method)
                time.sleep(0.01) # Sleep for 10ms
            
        except Exception as e:
            print(f"Error in receive thread from server: {e}, please try again") # Print error message

        print("Recieve thread ended") # Print message indicating thread end
    
    def _process_server_message(self, message):
        """Process incoming messages from the server"""
        message_type = message.get("type", "")

        # Call the appropriate handler based on the message type
        if message_type in self.message_handlers:
            self.message_handlers[message_type](message) # Call the message handler
        else:
            print(f"Unknown message type: {message_type}") # Print unknown message type

    def send_message(self, message):
        """Send a message to the server"""
        if not self.server_socket:
            return False # Return False if server socket is not initialized
        
        try:
            data = serialize_message(message) # Serialize the message
            self.server_socket.send(data) # Send the serialized message to the server
            return True # Return True if message sent successfully
        except Exception as e:
            print(f"Error sending message: {e}") # Print error message
            return False # Return False if message sending failed
        
    def create_game(self):
        """Create a new game on the server"""
        return self.send_message(Message.create_game()) # Send create game message to the server
    
    def join_game(self, game_id):
        """Join an existing game"""
        return self.send_message(Message.join_game(game_id)) # Send join game message to the server
    
    def list_games(self):
        """Request the list of available games"""
        return self.send_message(Message.list_games())
    
    def send_chat(self, message_text):
        """Send a chat message to the server"""
        return self.send_message(Message.chat_message(message_text))
    
    def move_unit(self, from_pos, to_pos):
        """Send a move unit action to the server"""
        return self.send_message(Message.move_unit(from_pos, to_pos))
    
    def attack(self, attacker_pos, defender_pos):
        """Send an attack action to the server"""
        return self.send_message(Message.attack(attacker_pos, defender_pos))
    
    def end_turn(self):
        """Send an end turn action to the server"""
        return self.send_message(Message.end_turn())
    
    def start_game(self, map_type="standard"):
        """Send a start game action to the server"""
        return self.send_message(Message.start_game(map_type))
    
    def disconnect(self):
        """Disconnect from the server"""
        if self.connected:
            try:
                self._Send_message(Message.disconnect()) # Send disconnect message to the server
            except:
                pass

            self.running = False # Set running flag to False
            self.connected = False # Set connected flag to False

            try:
                self.server_socket.close() # Close the server socket
            except:
                pass

            print("Disconnected from server") # Print message indicating disconnection

    # Handle incoming messages from the server
    def _handle_register_response(self, message):
        if message.get("status") == "sucess":
            self.client_id = message.get("client_id")
            self.connected = True
            print(f"Registered with server as {self.player_name} (ID: {self.client_id})")
            self.controller.on_connected_to_server()
        else:
            print(f"Registration failed: {message.get('error')}")
            self.controller.on_connection_error(message.get('message', 'Registration failed'))

    def _handle_game_state(self,message):
        self.game_state = message
        self.players = message.get("players", {})
        self.controller.on_game_stae_updated(message)

    def _handle_game_list(self, message):
        self.available_games = message.get("games", [])
        self.controller.on_game_list_updated(self.available_games)

    def _handle_join_response(self, message):
        if message.get("status") == "sucess":
            self.game_id = message.get("game_id")
            self.my_faction = message.get("faction")
            print(f"Joined game {self.game_id} as {self.my_faction}")
            self.controller.on_game_joined(message)
        else:
            print(f"Failed to join game: {message.get('message')}")
            self.controller.on_join_game_failed(message.get('message', 'Failed to join game'))
            

    def _handle_player_joined(self, message):
        player_name = message.get("player_name")
        player_id = message.get("player_id")
        print(f"Player {player_name} (ID: {player_id}) joined the game")
        self.controller.on_player_joined(player_name, player_id)
    
    