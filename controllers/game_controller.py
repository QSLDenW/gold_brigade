import pygame
from models.game_model import GameModel
from network.network_manager import NetworkManager

class GAmeController:
    def __init__(self):
        self.model = GameModel()
        self.network = NetworkManager()
        self.current_view = None
        self.multiplayer = False

        # Game stae
        self.game_state = "main_menu" # Main menu, game, multiplayer menu, etc.
        self.mp_menu_state = "main" #main, host, join, lobby
        self.messages = [] # List of messages to be sent to the server
        self.action_state = "select" # select, move, attack, end_turn

    def set_view(self, view):
        """Sets the current view of the game."""
        self.current_view = view

    # Main game control methods
    def start_game(self, multiplayer=False):
        """Starts a new game."""
        self.multiplayer_mode = multiplayer
        self.model.initialize_game()
        self.game_state = "play"

        if self.current_view:
            self.current_view.switch_to_game_view()

    def end_turn(self):
        """Ends the current player's turn."""
        if self.multiplayer_mode:
            self.network.end_turn()
        else:
            # Singleplayer mode
            self.model.next_player()
            # Update the view
            if self.current_view:
                self.current_view.update_turn_info()

    # Multiplayer methods
    def connect_to_server(self, player_name, server_ip, port):
        """Connects to the game server."""
        success, message = self.network.connect_to_server(player_name, server_ip, port)

        if success:
            self.show_message(message, error=False)

        else:
            self.show_message(message, error=True)

        return success
    
    def create_multiplayer_game(self):
        """Create a new multiplayer lobby."""
        if self.network.connected:
            self.network.create_game()
            self.show_message("Creating your multiplayer game, please wait...", error=False)
            return True
        else:
            self.show_message("You are not connected to a server.", error=True)
            return False
        
    def join_multiplayer_game(self, game_id):
        """Join an existing multiplayer lobby."""
        if self.network.connected:
            self.newtwork.join_game(game_id)
            self.show_message("Joining game, please wait...", error=False)
            return True
        else:
            self.show_message("You are not connected to a server.", error=True)
            return False
        
    def start_multiplayer_game(self, map_type="standard"):
        """Start the multiplayer game (host only)."""
        if self.network.connected and self.network.is_host:
            self.network.start_game(map_type)
            return True
        else:
            return False
        
    def refresh_game_list(self):
        """Request updated list of available games from the server."""
        if self.network.connected:
            self.network.request_game_list()
            return True
        else:
            self.show_message("You are not connected to a server.", error=True)
            return False
        
    def send_chat_message(self, message):
        """Send a chat message in multiplayer."""
        if self.network.connected:
            self.network.send_chat_message(message)
            return True
        else:
            self.show_message("You are not connected to a server.", error=True)
            return False
    
    # Model update methods
    def move_unit(self, from_pos, to_pos):
        """Move a unit on the board"""
        if self.multiplayer_mode:
            self.network.move_unit(from_pos, to_pos)
        else:
            success = self.model.move_unit(from_pos, to_pos)
            if success and self.current_view:
                self.current_view.update_game_view()
                
            return success
    
    def attack(self, attacker_pos, defender_pos):
        """Attack an enemy unit"""
        if self.multiplayer_mode:
            self.network.attack(attacker_pos, defender_pos)
        else:
            result = self.model.attack(attacker_pos, defender_pos)
            if self.current_view:
                self.current_view.update_game_view()
                
            return result
    
    # UI state methods
    def show_main_menu(self):
        """Switch to main menu"""
        self.game_state = "main_menu"
        if self.current_view:
            self.current_view.switch_to_main_menu()
    
    def show_multiplayer_menu(self):
        """Switch to multiplayer menu"""
        self.game_state = "multiplayer_menu"
        self.mp_menu_state = "main"
        if self.current_view:
            self.current_view.switch_to_multiplayer_menu()
    
    def show_message(self, message, error=False):
        """Show a message to the user"""
        self.messages.append({"text": message, "error": error, "time": pygame.time.get_ticks()})
        
        if self.current_view:
            self.current_view.show_message(message, error)
    
    # Network event handlers
    def on_connected_to_server(self):
        """Called when successfully connected to server"""
        self.show_message("Connected to server", error=False)
        # Refresh game list
        self.refresh_game_list()
    
    def on_connection_error(self, message):
        """Called when connection fails"""
        self.show_message(f"Connection error: {message}", error=True)
    
    def on_connection_lost(self):
        """Called when connection to server is lost"""
        self.show_message("Connection to server lost", error=True)
        # Return to main menu
        self.show_main_menu()
    
    def on_game_list_updated(self, games):
        """Called when game list is updated"""
        if self.current_view:
            self.current_view.update_game_list(games)
    
    def on_game_created(self, game_id):
        """Called when a game is successfully created"""
        self.mp_menu_state = "lobby"
        self.show_message(f"Game created! ID: {game_id}", error=False)
        if self.current_view:
            self.current_view.switch_to_game_lobby()
    
    def on_game_joined(self, message):
        """Called when successfully joined a game"""
        self.mp_menu_state = "lobby"
        game_id = message.get("game_id")
        faction = message.get("faction")
        self.show_message(f"Joined game {game_id} as {faction}", error=False)
        if self.current_view:
            self.current_view.switch_to_game_lobby()
    
    def on_join_game_failed(self, message):
        """Called when joining a game fails"""
        self.show_message(f"Failed to join game: {message}", error=True)
    
    def on_player_joined(self, player_name, player_id):
        """Called when a player joins the game"""
        self.show_message(f"Player {player_name} joined the game", error=False)
        if self.current_view:
            self.current_view.update_player_list()
    
    def on_player_left(self, player_name, player_id):
        """Called when a player leaves the game"""
        self.show_message(f"Player {player_name} left the game", error=True)
        if self.current_view:
            self.current_view.update_player_list()
    
    def on_game_started(self, message):
        """Called when the game starts"""
        self.game_state = "play"
        self.multiplayer_mode = True
        self.show_message("Game started!", error=False)
        
        # Initialize the game model from the initial state
        # This will be filled in by the first game state update
        
        if self.current_view:
            self.current_view.switch_to_game_view()
    
    def on_game_state_updated(self, state):
        """Called when game state is updated from server"""
        # Update local model with server state
        self.model.update_from_network(state)
        
        # Update the view
        if self.current_view:
            self.current_view.update_game_view()
    
    def on_turn_changed(self, player_id, player_name, turn):
        """Called when turn changes"""
        is_my_turn = (player_id == self.network.client_id)
        self.model.current_player_index = 0 if is_my_turn else 1
        self.model.turn = turn
        
        message = f"Turn {turn}: {player_name}'s turn"
        if is_my_turn:
            message += " (Your turn)"
        
        self.show_message(message, error=False)
        
        if self.current_view:
            self.current_view.update_turn_info()
    
    def on_unit_moved(self, from_pos, to_pos, unit):
        """Called when a unit is moved"""
        # Update will be handled by game state update
        self.show_message(f"{unit['name']} moved", error=False)
    
    def on_attack_result(self, attacker, defender, result, damage):
        """Called when an attack occurs"""
        # Update will be handled by game state update
        
        message = f"Attack: "
        if result == "destroyed":
            message += "Unit destroyed!"
        elif result == "damaged":
            message += f"Unit took {damage} damage"
        else:
            message += "Attack missed"
        
        self.show_message(message, error=False)
    
    def on_game_ended(self, reason):
        """Called when the game ends"""
        self.show_message(f"Game ended: {reason}", error=True)
        # Return to main menu after a delay
        # In a real implementation, show game over screen first
        pygame.time.delay(3000)
        self.show_main_menu()
    
    def on_action_response(self, status, message):
        """Called when server responds to an action"""
        if status == "failed":
            self.show_message(message, error=True)