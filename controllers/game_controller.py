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
    
    