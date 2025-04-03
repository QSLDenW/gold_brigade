# views/multiplayer_view.py
import pygame
from utils.helpers import Button, InputField, draw_text

class MultiplayerView:
    def __init__(self, screen, controller):
        self.screen = screen
        self.controller = controller
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (150, 150, 150)
        self.LIGHT_GRAY = (200, 200, 200)
        self.GREEN = (100, 200, 100)
        self.BLUE = (0, 100, 255)
        self.RED = (255, 0, 0)
        self.LIGHT_BLUE = (173, 216, 230)
        
        # Fonts
        self.title_font = pygame.font.SysFont('Arial', 48, bold=True)
        self.subtitle_font = pygame.font.SysFont('Arial', 36, bold=True)
        self.regular_font = pygame.font.SysFont('Arial', 24)
        
        # Main multiplayer menu buttons
        self.main_buttons = [
            Button(self.width//2 - 200, self.height//2 - 100, 400, 80, "Host Game", self.GREEN),
            Button(self.width//2 - 200, self.height//2, 400, 80, "Join Game", self.BLUE),
            Button(self.width//2 - 200, self.height//2 + 100, 400, 80, "Back", self.GRAY)
        ]
        
        # Input fields for host menu
        self.host_name_input = InputField(self.width//2 - 200, 290, 400, 40, "Player", self.regular_font)
        self.host_port_input = InputField(self.width//2 - 200, 390, 400, 40, "5555", self.regular_font)
        
        # Host menu buttons
        self.host_buttons = [
            Button(self.width//2 - 200, 460, 190, 60, "Host Game", self.GREEN),
            Button(self.width//2 + 10, 460, 190, 60, "Back", self.GRAY)
        ]
        
        # Input fields for join menu
        self.join_name_input = InputField(self.width//2 - 200, 250, 400, 40, "Player", self.regular_font)
        self.join_ip_input = InputField(self.width//2 - 200, 350, 400, 40, "127.0.0.1", self.regular_font)
        self.join_port_input = InputField(self.width//2 - 200, 450, 400, 40, "5555", self.regular_font)
        
        # Join menu buttons
        self.join_buttons = [
            Button(self.width//2 - 200, 520, 190, 60, "Join Game", self.GREEN),
            Button(self.width//2 + 10, 520, 190, 60, "Back", self.GRAY)
        ]
        
        # Game list for join menu
        self.available_games = []
        self.selected_game_id = None
        
        # Lobby buttons
        self.lobby_buttons = [
            Button(self.width//2 - 150, self.height - 150, 300, 60, "Start Game", self.GREEN),
            Button(self.width//2 - 150, self.height - 80, 300, 60, "Back to Menu", self.GRAY)
        ]
        
        # Chat input for lobby
        self.chat_input = InputField(self.width//2, self.height - 200, self.width//3, 40, "", self.regular_font)
        self.chat_active = False
        
        # Status message
        self.status_message = ""
        self.message_color = self.BLACK
        self.message_time = 0
    
    def handle_event(self, event):
        """Handle user input events"""
        if self.controller.mp_menu_state == "main":
            self._handle_main_menu_event(event)
        elif self.controller.mp_menu_state == "host":
            self._handle_host_menu_event(event)
        elif self.controller.mp_menu_state == "join":
            self._handle_join_menu_event(event)
        elif self.controller.mp_menu_state == "lobby":
            self._handle_lobby_event(event)
    
    def _handle_main_menu_event(self, event):
        """Handle events for the main multiplayer menu"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, button in enumerate(self.main_buttons):
                if button.is_clicked(pygame.mouse.get_pos()):
                    if i == 0:  # Host Game
                        self.controller.mp_menu_state = "host"
                    elif i == 1:  # Join Game
                        self.controller.mp_menu_state = "join"
                        # Refresh game list
                        self.controller.refresh_game_list()
                    elif i == 2:  # Back
                        self.controller.show_main_menu()
    
    def _handle_host_menu_event(self, event):
        """Handle events for the host game menu"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check for input field clicks
            if self.host_name_input.is_clicked(pygame.mouse.get_pos()):
                self.host_name_input.active = True
                self.host_port_input.active = False
            elif self.host_port_input.is_clicked(pygame.mouse.get_pos()):
                self.host_name_input.active = False
                self.host_port_input.active = True
            else:
                # Check for button clicks
                for i, button in enumerate(self.host_buttons):
                    if button.is_clicked(pygame.mouse.get_pos()):
                        if i == 0:  # Host Game
                            if not self.host_name_input.text:
                                self.controller.show_message("Please enter your name", error=True)
                            else:
                                # Connect to server
                                success = self.controller.connect_to_server(
                                    self.host_name_input.text,
                                    "127.0.0.1",  # Local server
                                    self.host_port_input.text
                                )
                                
                                if success:
                                    # Create a game
                                    self.controller.create_multiplayer_game()
                        elif i == 1:  # Back
                            self.controller.mp_menu_state = "main"
        
        elif event.type == pygame.KEYDOWN:
            # Handle text input
            if self.host_name_input.active:
                self.host_name_input.handle_key_event(event)
            elif self.host_port_input.active:
                self.host_port_input.handle_key_event(event)
    
    def _handle_join_menu_event(self, event):
        """Handle events for the join game menu"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check for input field clicks
            if self.join_name_input.is_clicked(pygame.mouse.get_pos()):
                self.join_name_input.active = True
                self.join_ip_input.active = False
                self.join_port_input.active = False
            elif self.join_ip_input.is_clicked(pygame.mouse.get_pos()):
                self.join_name_input.active = False
                self.join_ip_input.active = True
                self.join_port_input.active = False
            elif self.join_port_input.is_clicked(pygame.mouse.get_pos()):
                self.join_name_input.active = False
                self.join_ip_input.active = False
                self.join_port_input.active = True
            else:
                # Check for button clicks
                for i, button in enumerate(self.join_buttons):
                    if button.is_clicked(pygame.mouse.get_pos()):
                        if i == 0:  # Join Game
                            if not self.join_name_input.text:
                                self.controller.show_message("Please enter your name", error=True)
                            elif not self.join_ip_input.text:
                                self.controller.show_message("Please enter the server IP", error=True)
                            elif not self.selected_game_id:
                                self.controller.show_message("Please select a game to join", error=True)
                            else:
                                # Connect to server
                                success = self.controller.connect_to_server(
                                    self.join_name_input.text,
                                    self.join_ip_input.text,
                                    self.join_port_input.text
                                )
                                
                                if success:
                                    # Join the selected game
                                    self.controller.join_multiplayer_game(self.selected_game_id)
                        elif i == 1:  # Back
                            self.controller.mp_menu_state = "main"
                
                # Check for game list clicks
                y_pos = 250
                for i, game in enumerate(self.available_games):
                    game_rect = pygame.Rect(self.width//2 + 50, y_pos + i * 40, 300, 30)
                    if game_rect.collidepoint(pygame.mouse.get_pos()):
                        self.selected_game_id = game["id"]
        
        elif event.type == pygame.KEYDOWN:
            # Handle text input
            if self.join_name_input.active:
                self.join_name_input.handle_key_event(event)
            elif self.join_ip_input.active:
                self.join_ip_input.handle_key_event(event)
            elif self.join_port_input.active:
                self.join_port_input.handle_key_event(event)
    
    def _handle_lobby_event(self, event):
        """Handle events for the game lobby"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check if chat input field is clicked
            if self.chat_input.is_clicked(pygame.mouse.get_pos()):
                self.chat_input.active = True
                self.chat_active = True
            else:
                # Check for button clicks
                if hasattr(self.controller.network, 'game_ready') and self.controller.network.game_ready:
                    if hasattr(self.controller.network, 'is_host') and self.controller.network.is_host:
                        if self.lobby_buttons[0].is_clicked(pygame.mouse.get_pos()):  # Start Game
                            self.controller.start_multiplayer_game()
                
                if self.lobby_buttons[1].is_clicked(pygame.mouse.get_pos()):  # Back to Menu
                    self.controller.network.disconnect()
                    self.controller.mp_menu_state = "main"
        
        elif event.type == pygame.KEYDOWN:
            # Handle chat input
            if self.chat_active:
                if event.key == pygame.K_RETURN:
                    # Send chat message
                    if self.chat_input.text:
                        self.controller.send_chat_message(self.chat_input.text)
                        self.chat_input.text = ""
                else:
                    self.chat_input.handle_key_event(event)
    
    def update(self):
        """Update the view state"""
        # Update button hover states
        mouse_pos = pygame.mouse.get_pos()
        
        if self.controller.mp_menu_state == "main":
            for button in self.main_buttons:
                button.update(mouse_pos)
        
        elif self.controller.mp_menu_state == "host":
            for button in self.host_buttons:
                button.update(mouse_pos)
        
        elif self.controller.mp_menu_state == "join":
            for button in self.join_buttons:
                button.update(mouse_pos)
        
        elif self.controller.mp_menu_state == "lobby":
            for button in self.lobby_buttons:
                button.update(mouse_pos)
    
    def draw(self):
        """Draw the view"""
        # Fill background
        self.screen.fill(self.LIGHT_BLUE)
        
        # Draw the appropriate submenu
        if self.controller.mp_menu_state == "main":
            self._draw_main_menu()
        elif self.controller.mp_menu_state == "host":
            self._draw_host_menu()
        elif self.controller.mp_menu_state == "join":
            self._draw_join_menu()
        elif self.controller.mp_menu_state == "lobby":
            self._draw_lobby()
    
    def _draw_main_menu(self):
        """Draw the main multiplayer menu"""
        # Title
        title_text = self.title_font.render("GOLDEN BRIGADE MULTIPLAYER", True, self.BLACK)
        title_rect = title_text.get_rect(center=(self.width//2, 100))
        self.screen.blit(title_text, title_rect)
        
        # Subtitle
        subtitle_text = self.subtitle_font.render("Select Multiplayer Mode", True, self.BLACK)
        subtitle_rect = subtitle_text.get_rect(center=(self.width//2, 160))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Draw buttons
        for button in self.main_buttons:
            button.draw(self.screen)
    
    def _draw_host_menu(self):
        """Draw the host game menu"""
        # Title
        title_text = self.title_font.render("HOST A MULTIPLAYER GAME", True, self.BLACK)
        title_rect = title_text.get_rect(center=(self.width//2, 100))
        self.screen.blit(title_text, title_rect)
        
        # Try to get local IP
        ip_address = self.controller.network.get_local_ip() if hasattr(self.controller, 'network') else "127.0.0.1"
        
        # IP info
        ip_text = self.subtitle_font.render(f"Your IP Address: {ip_address}", True, self.BLACK)
        ip_rect = ip_text.get_rect(center=(self.width//2, 180))
        self.screen.blit(ip_text, ip_rect)
        
        info_text = self.regular_font.render("Share your IP address with your opponent to allow them to connect.", True, self.BLACK)
        info_rect = info_text.get_rect(center=(self.width//2, 220))
        self.screen.blit(info_text, info_rect)
        
        # Player name field
        name_label = self.subtitle_font.render("Your Name:", True, self.BLACK)
        self.screen.blit(name_label, (self.width//2 - 200, 250))
        self.host_name_input.draw(self.screen)
        
        # Port field
        port_label = self.subtitle_font.render("Port (default: 5555):", True, self.BLACK)
        self.screen.blit(port_label, (self.width//2 - 200, 350))
        self.host_port_input.draw(self.screen)
        
        # Draw buttons
        for button in self.host_buttons:
            button.draw(self.screen)
        
        # Draw status message
        if self.status_message:
            message_text = self.regular_font.render(self.status_message, True, self.message_color)
            message_rect = message_text.get_rect(center=(self.width//2, 550))
            self.screen.blit(message_text, message_rect)
    
    def _draw_join_menu(self):
        """Draw the join game menu"""
        # Title
        title_text = self.title_font.render("JOIN A MULTIPLAYER GAME", True, self.BLACK)
        title_rect = title_text.get_rect(center=(self.width//2, 100))
        self.screen.blit(title_text, title_rect)
        
        # Instruction
        info_text = self.regular_font.render("Enter the host's IP address and port to join their game.", True, self.BLACK)
        info_rect = info_text.get_rect(center=(self.width//2, 160))
        self.screen.blit(info_text, info_rect)
        
        # Player name field
        name_label = self.subtitle_font.render("Your Name:", True, self.BLACK)
        self.screen.blit(name_label, (self.width//2 - 200, 210))
        self.join_name_input.draw(self.screen)
        
        # IP address field
        ip_label = self.subtitle_font.render("Host IP Address:", True, self.BLACK)
        self.screen.blit(ip_label, (self.width//2 - 200, 310))
        self.join_ip_input.draw(self.screen)
        
        # Port field
        port_label = self.subtitle_font.render("Port (default: 5555):", True, self.BLACK)
        self.screen.blit(port_label, (self.width//2 - 200, 410))
        self.join_port_input.draw(self.screen)
        
        # Draw buttons
        for button in self.join_buttons:
            button.draw(self.screen)
        
        # Draw game list
        games_label = self.subtitle_font.render("Available Games:", True, self.BLACK)
        self.screen.blit(games_label, (self.width//2 + 50, 210))
        
        if not self.available_games:
            no_games_text = self.regular_font.render("No games available", True, self.GRAY)
            self.screen.blit(no_games_text, (self.width//2 + 50, 250))
        else:
            y_pos = 250
            for i, game in enumerate(self.available_games):
                game_text = f"{game['host']} ({game['players']}/{game['max_players']})"
                color = self.GREEN if game["id"] == self.selected_game_id else self.BLACK
                game_label = self.regular_font.render(game_text, True, color)
                self.screen.blit(game_label, (self.width//2 + 50, y_pos + i * 40))
                
                # Draw selection box
                if game["id"] == self.selected_game_id:
                    select_rect = pygame.Rect(self.width//2 + 40, y_pos + i * 40 - 2, 320, 34)
                    pygame.draw.rect(self.screen, self.LIGHT_BLUE, select_rect, 2)
        
        # Draw status message
        if self.status_message:
            message_text = self.regular_font.render(self.status_message, True, self.message_color)
            message_rect = message_text.get_rect(center=(self.width//2, 600))
            self.screen.blit(message_text, message_rect)
    
    def _draw_lobby(self):
        """Draw the game lobby screen"""
        # Title
        title_text = self.title_font.render("GAME LOBBY", True, self.BLACK)
        title_rect = title_text.get_rect(center=(self.width//2, 80))
        self.screen.blit(title_text, title_rect)
        
        # Connection info
        if hasattr(self.controller, 'network'):
            if self.controller.network.is_host:
                ip_address = self.controller.network.get_local_ip()
                status_text = self.regular_font.render(f"Hosting game on {ip_address}:{self.host_port_input.text}", True, self.BLACK)
            else:
                status_text = self.regular_font.render(f"Connected to {self.join_ip_input.text}:{self.join_port_input.text}", True, self.BLACK)
            
            status_rect = status_text.get_rect(center=(self.width//2, 130))
            self.screen.blit(status_text, status_rect)
        
        # Draw players section
        players_label = self.subtitle_font.render("Players:", True, self.BLACK)
        self.screen.blit(players_label, (self.width//4, 180))
        
        # Get players from network manager
        if hasattr(self.controller, 'network'):
            players = self.controller.network.players
            y_pos = 230
            for i, (player_id, player_info) in enumerate(players.items()):
                player_name = player_info.get("name", "Unknown")
                faction = player_info.get("faction", "Unknown")
                
                player_text = self.regular_font.render(f"{i+1}. {player_name} - {faction}", True, self.BLACK)
                self.screen.blit(player_text, (self.width//4, y_pos + i * 40))
        
        # Game status
        if hasattr(self.controller, 'network') and self.controller.network.game_ready:
            ready_text = self.subtitle_font.render("All players connected! Ready to start.", True, self.GREEN)
        else:
            ready_text = self.subtitle_font.render("Waiting for players to connect...", True, self.BLACK)
        
        ready_rect = ready_text.get_rect(center=(self.width//2, 350))
        self.screen.blit(ready_text, ready_rect)
        
        # Draw chat section
        chat_label = self.subtitle_font.render("Chat:", True, self.BLACK)
        self.screen.blit(chat_label, (self.width*3//4 - 100, 180))
        
        # Chat box
        chat_box_rect = pygame.Rect(self.width*3//4 - 200, 230, 400, 300)
        pygame.draw.rect(self.screen, self.WHITE, chat_box_rect)
        pygame.draw.rect(self.screen, self.BLACK, chat_box_rect, 2)
        
        # Draw chat messages
        if hasattr(self.controller, 'network'):
            chat_messages = self.controller.network.chat_messages
            y_offset = 10
            for msg in chat_messages[-10:]:  # Show last 10 messages
                sender = msg.get("sender", "Unknown")
                text = msg.get("message", "")
                
                chat_text = self.regular_font.render(f"{sender}: {text}", True, self.BLACK)
                self.screen.blit(chat_text, (chat_box_rect.x + 10, chat_box_rect.y + y_offset))
                y_offset += 30
        
        # Chat input
        self.chat_input.set_position(self.width*3//4 - 200, self.height - 200)
        self.chat_input.draw(self.screen)
        
        # Start game button (only for host and when game is ready)
        if hasattr(self.controller, 'network') and self.controller.network.game_ready:
            if hasattr(self.controller, 'network') and self.controller.network.is_host:
                self.lobby_buttons[0].draw(self.screen)
        
        # Back button
        self.lobby_buttons[1].draw(self.screen)
        
        # Draw status message
        if self.status_message:
            message_text = self.regular_font.render(self.status_message, True, self.message_color)
            message_rect = message_text.get_rect(center=(self.width//2, self.height - 50))
            self.screen.blit(message_text, message_rect)
    
    def show_message(self, message, error=False):
        """Display a status message"""
        self.status_message = message
        self.message_color = self.RED if error else self.GREEN
        self.message_time = pygame.time.get_ticks()
    
    def update_game_list(self, games):
        """Update the list of available games"""
        self.available_games = games
    
    def update_player_list(self):
        """Update the player list in the lobby"""
        # This will be reflected automatically from the network manager's player data
        pass
    
    def switch_to_game_lobby(self):
        """Switch to the game lobby view"""
        # This is handled by the controller updating mp_menu_state
        pass
    
    def switch_to_multiplayer_menu(self):
        """Switch to the multiplayer menu"""
        # Reset input fields
        self.host_name_input.active = False
        self.host_port_input.active = False
        self.join_name_input.active = False
        self.join_ip_input.active = False
        self.join_port_input.active = False
        self.chat_input.active = False
        self.chat_active = False