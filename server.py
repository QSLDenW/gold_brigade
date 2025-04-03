# server.py
import socket
import pickle
import threading
import time
import random
import uuid
import sys
import json
import argparse

# Import message protocol
from network.message_protocol import MessageType, serialize_message, deserialize_message

# Server configuration
DEFAULT_HOST = '0.0.0.0'  # Listen on all available interfaces
DEFAULT_PORT = 5555
BUFFER_SIZE = 4096
MAX_PLAYERS_PER_GAME = 2

class GameServer:
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = {}  # client_id -> client info
        self.games = {}    # game_id -> game info
        self.running = False
        self.games_lock = threading.Lock()
        
        print(f"Golden Brigade Game Server initializing on {host}:{port}...")
    
    def start(self):
        """Start the game server"""
        try:
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            self.server_socket.settimeout(0.5)  # Non-blocking socket
            
            self.running = True
            print(f"Server started on {self.host}:{self.port}")
            
            # Game maintenance thread (cleans up old games)
            maintenance_thread = threading.Thread(target=self._maintenance_task)
            maintenance_thread.daemon = True
            maintenance_thread.start()
            
            # Start accepting client connections
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    print(f"New connection from {client_address}")
                    
                    # Start a new thread to handle this client
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.timeout:
                    # This is expected for non-blocking socket
                    pass
                except Exception as e:
                    print(f"Error accepting connection: {e}")
            
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.shutdown()
    
    def _maintenance_task(self):
        """Background task to cleanup old games and disconnected clients"""
        while self.running:
            try:
                with self.games_lock:
                    # Check for games with no players
                    for game_id in list(self.games.keys()):
                        game = self.games[game_id]
                        
                        # Remove games with no players
                        if len(game["players"]) == 0:
                            del self.games[game_id]
                            print(f"Removed empty game {game_id}")
                        
                        # Check for games that have been waiting too long
                        elif game["state"] == "waiting" and (time.time() - game["created_at"]) > 3600:  # 1 hour
                            # Notify players in this game
                            for player_id in game["players"]:
                                if player_id in self.clients:
                                    self.send_to_client(player_id, {
                                        "type": MessageType.GAME_ENDED,
                                        "reason": "Game timed out while waiting for players"
                                    })
                            
                            # Remove the game
                            del self.games[game_id]
                            print(f"Removed timed-out game {game_id}")
                
                # Sleep to avoid constant CPU usage
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Error in maintenance task: {e}")
    
    def handle_client(self, client_socket, client_address):
        """Handle communication with a client"""
        client_id = None
        game_id = None
        
        try:
            # Configure socket for timeout
            client_socket.settimeout(0.5)
            
            # First message should be client registration
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                return
            
            message = deserialize_message(data)
            
            if message["type"] == MessageType.REGISTER:
                # Register the client
                client_id = str(uuid.uuid4())
                player_name = message.get("name", "Player")
                
                self.clients[client_id] = {
                    "socket": client_socket,
                    "address": client_address,
                    "name": player_name,
                    "game_id": None,
                    "last_activity": time.time()
                }
                
                # Send registration confirmation
                response = {
                    "type": MessageType.REGISTER_RESPONSE,
                    "client_id": client_id,
                    "status": "success"
                }
                client_socket.send(serialize_message(response))
                print(f"Client registered: {player_name} ({client_id})")
                
                # Now handle client messages
                while self.running:
                    try:
                        data = client_socket.recv(BUFFER_SIZE)
                        if not data:
                            break
                        
                        # Update last activity time
                        self.clients[client_id]["last_activity"] = time.time()
                        
                        message = deserialize_message(data)
                        self.process_client_message(client_id, message)
                        
                    except socket.timeout:
                        # This is expected for non-blocking socket
                        pass
                    except Exception as e:
                        print(f"Error receiving data from client {client_id}: {e}")
                        break
            
        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
        finally:
            # Clean up when client disconnects
            if client_id in self.clients:
                # Remove client from game if in one
                game_id = self.clients[client_id].get("game_id")
                if game_id and game_id in self.games:
                    self.leave_game(client_id, game_id)
                
                # Remove client
                del self.clients[client_id]
                print(f"Client {client_id} disconnected")
            
            # Close socket
            try:
                client_socket.close()
            except:
                pass
    
    def process_client_message(self, client_id, message):
        """Process messages from clients"""
        message_type = message.get("type", "")
        
        if message_type == MessageType.CREATE_GAME:
            # Create a new game
            game_id = self.create_game(client_id)
            
            # Send game creation confirmation
            response = {
                "type": MessageType.GAME_CREATED,
                "game_id": game_id
            }
            self.send_to_client(client_id, response)
        
        elif message_type == MessageType.JOIN_GAME:
            # Join existing game
            game_id = message.get("game_id")
            if game_id and game_id in self.games:
                success = self.join_game(client_id, game_id)
                
                if success:
                    # Send game state to all players
                    self.broadcast_game_state(game_id)
                else:
                    # Send failure response
                    response = {
                        "type": MessageType.JOIN_RESPONSE,
                        "status": "failed",
                        "message": "Game is full or no longer available"
                    }
                    self.send_to_client(client_id, response)
            else:
                # Send failure response
                response = {
                    "type": MessageType.JOIN_RESPONSE,
                    "status": "failed",
                    "message": "Game not found"
                }
                self.send_to_client(client_id, response)
        
        elif message_type == MessageType.LIST_GAMES:
            # Send list of available games
            available_games = self.get_available_games()
            
            response = {
                "type": MessageType.GAME_LIST,
                "games": available_games
            }
            self.send_to_client(client_id, response)
        
        elif message_type == MessageType.GAME_ACTION:
            # Process game action
            game_id = self.clients[client_id].get("game_id")
            if game_id and game_id in self.games:
                self.process_game_action(client_id, game_id, message)
                
                # Broadcast updated game state
                self.broadcast_game_state(game_id)
        
        elif message_type == MessageType.CHAT_MESSAGE:
            # Broadcast chat message to all players in the game
            game_id = self.clients[client_id].get("game_id")
            if game_id and game_id in self.games:
                chat_message = {
                    "type": MessageType.CHAT_MESSAGE,
                    "sender": self.clients[client_id]["name"],
                    "message": message.get("message", ""),
                    "timestamp": time.time()
                }
                self.broadcast_to_game(game_id, chat_message, exclude_client=None)
        
        elif message_type == MessageType.DISCONNECT:
            # Client is disconnecting gracefully
            game_id = self.clients[client_id].get("game_id")
            if game_id and game_id in self.games:
                self.leave_game(client_id, game_id)
            
            # This client will be cleaned up when the connection ends
    
    def create_game(self, host_client_id):
        """Create a new game with the client as host"""
        with self.games_lock:
            game_id = str(uuid.uuid4())[:8]  # Short game ID
            
            # Initialize game state
            self.games[game_id] = {
                "id": game_id,
                "host_id": host_client_id,
                "players": {
                    host_client_id: {
                        "name": self.clients[host_client_id]["name"],
                        "faction": "Czech",  # Host is Czech by default
                        "ready": False
                    }
                },
                "state": "waiting",  # waiting, active, finished
                "turn": 0,
                "current_player": None,
                "map": None,  # Will be initialized when game starts
                "units": {},  # Will be populated when game starts
                "created_at": time.time()
            }
            
            # Associate client with this game
            self.clients[host_client_id]["game_id"] = game_id
            
            print(f"Game created: {game_id} by {self.clients[host_client_id]['name']}")
            return game_id
    
    def join_game(self, client_id, game_id):
        """Add client to an existing game"""
        with self.games_lock:
            if game_id not in self.games:
                return False
            
            game = self.games[game_id]
            
            # Check if game is full
            if len(game["players"]) >= MAX_PLAYERS_PER_GAME:
                return False
            
            # Check if game is still waiting for players
            if game["state"] != "waiting":
                return False
            
            # Add player to game
            game["players"][client_id] = {
                "name": self.clients[client_id]["name"],
                "faction": "Austrian",  # Joining player is Austrian by default
                "ready": False
            }
            
            # Associate client with this game
            self.clients[client_id]["game_id"] = game_id
            
            # Send join confirmation
            response = {
                "type": MessageType.JOIN_RESPONSE,
                "status": "success",
                "game_id": game_id,
                "faction": "Austrian"
            }
            self.send_to_client(client_id, response)
            
            # Notify host
            host_message = {
                "type": MessageType.PLAYER_JOINED,
                "player_name": self.clients[client_id]["name"],
                "player_id": client_id
            }
            self.send_to_client(game["host_id"], host_message)
            
            print(f"Player {self.clients[client_id]['name']} joined game {game_id}")
            
            # If we now have maximum players, set game_ready flag
            if len(game["players"]) == MAX_PLAYERS_PER_GAME:
                for player_id in game["players"]:
                    game["players"][player_id]["ready"] = True
            
            return True
    
    def leave_game(self, client_id, game_id):
        """Remove client from a game"""
        with self.games_lock:
            if game_id not in self.games:
                return
            
            game = self.games[game_id]
            
            # Remove player from game
            if client_id in game["players"]:
                del game["players"][client_id]
                
                # Notify other players
                leave_message = {
                    "type": "player_left",
                    "player_name": self.clients[client_id]["name"],
                    "player_id": client_id
                }
                self.broadcast_to_game(game_id, leave_message, exclude_client=client_id)
                
                print(f"Player {self.clients[client_id]['name']} left game {game_id}")
                
                # If host left, end the game
                if client_id == game["host_id"]:
                    # Notify remaining players
                    end_message = {
                        "type": "game_ended",
                        "reason": "Host left the game"
                    }
                    self.broadcast_to_game(game_id, end_message, exclude_client=None)
                    
                    # Remove game
                    del self.games[game_id]
                    print(f"Game {game_id} ended (host left)")
                    
                    # Update client game associations
                    for cid in list(self.clients.keys()):
                        if cid in self.clients and self.clients[cid].get("game_id") == game_id:
                            self.clients[cid]["game_id"] = None
                elif len(game["players"]) == 0:
                    # Last player left, remove the game
                    del self.games[game_id]
                    print(f"Game {game_id} removed (all players left)")
            
            # Update client's game association
            self.clients[client_id]["game_id"] = None
    
    def get_available_games(self):
        """Get list of available games for joining"""
        available_games = []
        
        with self.games_lock:
            for game_id, game in self.games.items():
                if game["state"] == "waiting" and len(game["players"]) < MAX_PLAYERS_PER_GAME:
                    available_games.append({
                        "id": game_id,
                        "host": self.clients[game["host_id"]]["name"],
                        "players": len(game["players"]),
                        "max_players": MAX_PLAYERS_PER_GAME,
                        "created_at": game["created_at"]
                    })
        
        return available_games
    
    def process_game_action(self, client_id, game_id, action_message):
        """Process a game action from a client"""
        with self.games_lock:
            if game_id not in self.games:
                return
            
            game = self.games[game_id]
            
            # Check if it's this player's turn
            if game["state"] == "active" and game["current_player"] != client_id:
                # Not this player's turn
                response = {
                    "type": "action_response",
                    "status": "failed",
                    "message": "Not your turn"
                }
                self.send_to_client(client_id, response)
                return
            
            # Process different action types
            action_type = action_message.get("action", "")
            action_data = action_message.get("data", {})
            
            if action_type == "start_game":
                # Start the game if all players are ready
                if len(game["players"]) == MAX_PLAYERS_PER_GAME:
                    # Initialize game state
                    game["state"] = "active"
                    game["turn"] = 1
                    game["current_player"] = game["host_id"]  # Czech player (host) starts
                    
                    # Initialize map and units based on selected map
                    self.initialize_game_map(game_id, action_data.get("map_type", "standard"))
                    
                    # Notify all players
                    start_message = {
                        "type": "game_started",
                        "first_player": self.clients[game["host_id"]]["name"],
                        "turn": 1
                    }
                    self.broadcast_to_game(game_id, start_message, exclude_client=None)
                    
                    print(f"Game {game_id} started")
                else:
                    # Not enough players
                    response = {
                        "type": "action_response",
                        "status": "failed",
                        "message": "Not enough players to start"
                    }
                    self.send_to_client(client_id, response)
            
            elif action_type == "move_unit":
                # Move a unit on the board
                from_pos = (action_data.get("from_x", 0), action_data.get("from_y", 0))
                to_pos = (action_data.get("to_x", 0), action_data.get("to_y", 0))
                
                # Check if unit exists at from_pos
                unit_key = f"{from_pos[0]},{from_pos[1]}"
                if unit_key in game["units"]:
                    unit = game["units"][unit_key]
                    
                    # Check if it's this player's unit
                    player_faction = game["players"][client_id]["faction"]
                    if unit["faction"] == player_faction:
                        # Check if destination is valid (not detailed here)
                        # In a real implementation, check movement range and terrain
                        
                        # Move the unit
                        del game["units"][unit_key]
                        new_unit_key = f"{to_pos[0]},{to_pos[1]}"
                        game["units"][new_unit_key] = unit
                        game["units"][new_unit_key]["has_moved"] = True
                        
                        # Notify all players of the move
                        move_message = {
                            "type": "unit_moved",
                            "from": from_pos,
                            "to": to_pos,
                            "unit": unit
                        }
                        self.broadcast_to_game(game_id, move_message, exclude_client=None)
                    else:
                        # Not player's unit
                        response = {
                            "type": "action_response",
                            "status": "failed",
                            "message": "Not your unit"
                        }
                        self.send_to_client(client_id, response)
                else:
                    # No unit at that position
                    response = {
                        "type": "action_response",
                        "status": "failed",
                        "message": "No unit at that position"
                    }
                    self.send_to_client(client_id, response)
            
            elif action_type == "attack":
                # Attack another unit
                attacker_pos = (action_data.get("attacker_x", 0), action_data.get("attacker_y", 0))
                defender_pos = (action_data.get("defender_x", 0), action_data.get("defender_y", 0))
                
                # Check if units exist at positions
                attacker_key = f"{attacker_pos[0]},{attacker_pos[1]}"
                defender_key = f"{defender_pos[0]},{defender_pos[1]}"
                
                if attacker_key in game["units"] and defender_key in game["units"]:
                    attacker = game["units"][attacker_key]
                    defender = game["units"][defender_key]
                    
                    # Check if it's player's unit attacking
                    player_faction = game["players"][client_id]["faction"]
                    if attacker["faction"] == player_faction and defender["faction"] != player_faction:
                        # Check if attacker has already attacked
                        if not attacker.get("has_attacked", False):
                            # Perform attack calculations (simplified)
                            attacker_value = attacker["attack"] + random.randint(1, 6)
                            defender_value = defender["defense"] + random.randint(1, 6)
                            
                            if attacker_value > defender_value:
                                # Attack succeeds
                                damage = min(attacker_value - defender_value, 50)
                                defender["health"] -= damage
                                
                                # Check if defender is destroyed
                                if defender["health"] <= 0:
                                    del game["units"][defender_key]
                                    result = "destroyed"
                                else:
                                    result = "damaged"
                            else:
                                # Attack fails
                                result = "missed"
                            
                            # Mark attacker as having attacked
                            attacker["has_attacked"] = True
                            
                            # Notify all players of the attack
                            attack_message = {
                                "type": "attack_result",
                                "attacker": attacker_pos,
                                "defender": defender_pos,
                                "result": result,
                                "damage": damage if result == "damaged" else None
                            }
                            self.broadcast_to_game(game_id, attack_message, exclude_client=None)
                        else:
                            # Unit already attacked
                            response = {
                                "type": "action_response",
                                "status": "failed",
                                "message": "Unit has already attacked this turn"
                            }
                            self.send_to_client(client_id, response)
                    else:
                        # Not player's unit or attacking friendly unit
                        response = {
                            "type": "action_response",
                            "status": "failed",
                            "message": "Invalid attack"
                        }
                        self.send_to_client(client_id, response)
                else:
                    # Units not found
                    response = {
                        "type": "action_response",
                        "status": "failed",
                        "message": "Units not found"
                    }
                    self.send_to_client(client_id, response)
            
            elif action_type == "end_turn":
                # End current player's turn
                if game["current_player"] == client_id:
                    # Determine next player
                    player_ids = list(game["players"].keys())
                    current_index = player_ids.index(client_id)
                    next_index = (current_index + 1) % len(player_ids)
                    next_player = player_ids[next_index]
                    
                    # Update game state
                    game["current_player"] = next_player
                    
                    # Check if we've completed a full round
                    if next_player == game["host_id"]:
                        game["turn"] += 1
                    
                    # Reset unit status for next player
                    for unit_key, unit in game["units"].items():
                        if unit["faction"] == game["players"][next_player]["faction"]:
                            unit["has_moved"] = False
                            unit["has_attacked"] = False
                    
                    # Notify all players
                    turn_message = {
                        "type": "turn_changed",
                        "player": self.clients[next_player]["name"],
                        "player_id": next_player,
                        "turn": game["turn"]
                    }
                    self.broadcast_to_game(game_id, turn_message, exclude_client=None)
                    
                    print(f"Game {game_id} - Turn changed to {self.clients[next_player]['name']}")
                else:
                    # Not this player's turn
                    response = {
                        "type": "action_response",
                        "status": "failed",
                        "message": "Not your turn"
                    }
                    self.send_to_client(client_id, response)
    
    def initialize_game_map(self, game_id, map_type):
        """Initialize map and units for a new game"""
        with self.games_lock:
            if game_id not in self.games:
                return
            
            game = self.games[game_id]
            
            # Set up map terrain (simplified, would be more complex in actual game)
            game["map"] = {
                "width": 20,
                "height": 15,
                "terrain": {}  # Would contain terrain data for each tile
            }
            
            # Create initial units for both players
            game["units"] = {}
            
            # Get player IDs
            player_ids = list(game["players"].keys())
            czech_player_id = game["host_id"]
            austrian_player_id = [pid for pid in player_ids if pid != czech_player_id][0]
            
            # Create Czech units (left side of map)
            game["units"]["1,1"] = {"name": "Czech Infantry", "attack": 3, "defense": 3, "movement": 2, "type": "Infantry", "faction": "Czech", "health": 100}
            game["units"]["2,3"] = {"name": "T-72M4 CZ", "attack": 6, "defense": 5, "movement": 3, "type": "Armor", "faction": "Czech", "health": 100}
            game["units"]["3,5"] = {"name": "DANA Howitzer", "attack": 7, "defense": 2, "movement": 1, "type": "Artillery", "faction": "Czech", "health": 100}
            
            # Create Austrian units (right side of map)
            game["units"]["18,13"] = {"name": "Austrian Infantry", "attack": 3, "defense": 3, "movement": 2, "type": "Infantry", "faction": "Austrian", "health": 100}
            game["units"]["17,11"] = {"name": "Leopard 2A4", "attack": 7, "defense": 5, "movement": 3, "type": "Armor", "faction": "Austrian", "health": 100}
            game["units"]["16,9"] = {"name": "M109 Howitzer", "attack": 7, "defense": 2, "movement": 1, "type": "Artillery", "faction": "Austrian", "health": 100}
    
    def broadcast_game_state(self, game_id):
        """Send current game state to all players in a game"""
        with self.games_lock:
            if game_id not in self.games:
                return
            
            game = self.games[game_id]
            
            # Prepare game state message
            game_state = {
                "type": "game_state",
                "game_id": game_id,
                "state": game["state"],
                "turn": game["turn"],
                "current_player": game["current_player"],
                "current_player_name": self.clients[game["current_player"]]["name"] if game["current_player"] else None,
                "players": {},
                "map": game["map"],
                "units": game["units"]
            }
            
            # Add player info
            for player_id, player_data in game["players"].items():
                game_state["players"][player_id] = {
                    "name": player_data["name"],
                    "faction": player_data["faction"],
                    "ready": player_data["ready"]
                }
            
            # Send to all players
            self.broadcast_to_game(game_id, game_state, exclude_client=None)
    
    def broadcast_to_game(self, game_id, message, exclude_client=None):
        """Send a message to all players in a game"""
        with self.games_lock:
            if game_id not in self.games:
                return
            
            game = self.games[game_id]
            
            for player_id in game["players"]:
                if player_id != exclude_client and player_id in self.clients:
                    self.send_to_client(player_id, message)
    
    def send_to_client(self, client_id, message):
        """Send a message to a specific client"""
        if client_id not in self.clients:
            return
        
        try:
            client_socket = self.clients[client_id]["socket"]
            client_socket.send(pickle.dumps(message))
        except Exception as e:
            print(f"Error sending to client {client_id}: {e}")
    
    def shutdown(self):
        """Clean shutdown of the server"""
        self.running = False
        
        # Close all client connections
        for client_id in list(self.clients.keys()):
            try:
                self.clients[client_id]["socket"].close()
            except:
                pass
        
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print("Server shutdown complete")

if __name__ == "__main__":
    server = GameServer()
    
    try:
        print("Starting Golden Brigade game server...")
        server.start()
    except KeyboardInterrupt:
        print("Server shutting down...")
    finally:
        server.shutdown()