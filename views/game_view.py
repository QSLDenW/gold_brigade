# views/game_view.py
import pygame
from utils.helpers import Button, draw_text

class GameView:
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
        
        # Game colors
        self.CZECH_COLOR = (0, 100, 255)  # Blue
        self.AUSTRIAN_COLOR = (255, 50, 50)  # Red
        
        # Terrain colors
        self.TERRAIN_COLORS = {
            "Plains": (180, 230, 180),
            "Forest": (70, 130, 70),
            "Mountain": (160, 160, 160),
            "River": (100, 150, 230),
            "Road": (180, 180, 140),
            "Urban": (200, 150, 150)
        }
        
        # Fonts
        self.title_font = pygame.font.SysFont('Arial', 36, bold=True)
        self.subtitle_font = pygame.font.SysFont('Arial', 24, bold=True)
        self.regular_font = pygame.font.SysFont('Arial', 20)
        self.small_font = pygame.font.SysFont('Arial', 16)
        
        # Game board dimensions
        self.tile_size = 50
        self.board_offset_x = 20
        self.board_offset_y = 80
        
        # Control panel
        self.panel_rect = pygame.Rect(
            self.board_offset_x + self.controller.model.map_width * self.tile_size + 20,
            self.board_offset_y,
            300,
            self.height - 120
        )
        
        # Game controls buttons
        self.buttons = [
            Button(self.panel_rect.x + 20, self.panel_rect.y + self.panel_rect.height - 180, 
                   260, 50, "End Turn", self.GREEN),
            Button(self.panel_rect.x + 20, self.panel_rect.y + self.panel_rect.height - 120, 
                   260, 50, "Main Menu", self.GRAY)
        ]
        
        # Action buttons
        self.action_buttons = [
            Button(self.panel_rect.x + 20, self.panel_rect.y + 280, 120, 40, "Move", self.BLUE),
            Button(self.panel_rect.x + 160, self.panel_rect.y + 280, 120, 40, "Attack", self.RED)
        ]
        
        # Selected unit and valid moves
        self.selected_unit_pos = None
        self.valid_move_positions = []
        self.valid_attack_positions = []
        
        # Game status messages
        self.status_message = ""
        self.message_color = self.BLACK
        self.message_time = 0
    
    def handle_event(self, event):
        """Handle user input events"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check if a tile was clicked
            clicked_pos = self._get_board_position(event.pos)
            if clicked_pos:
                x, y = clicked_pos
                if 0 <= x < self.controller.model.map_width and 0 <= y < self.controller.model.map_height:
                    if self.controller.action_state == "select":
                        # Select a unit
                        if clicked_pos in self.controller.model.units:
                            unit = self.controller.model.units[clicked_pos]
                            if unit.faction == self.controller.model.players[self.controller.model.current_player_index]:
                                self.selected_unit_pos = clicked_pos
                                
                                # Highlight valid moves
                                self._calculate_valid_moves()
                                self._calculate_valid_attacks()
                            else:
                                self.controller.show_message("That's not your unit", error=True)
                        else:
                            self.selected_unit_pos = None
                            self.valid_move_positions = []
                            self.valid_attack_positions = []
                    
                    elif self.controller.action_state == "move":
                        # Move the selected unit
                        if self.selected_unit_pos and clicked_pos in self.valid_move_positions:
                            success = self.controller.move_unit(self.selected_unit_pos, clicked_pos)
                            if success:
                                self.selected_unit_pos = clicked_pos
                                self._calculate_valid_attacks()
                            self.controller.action_state = "select"
                        else:
                            self.controller.show_message("Invalid move", error=True)
                    
                    elif self.controller.action_state == "attack":
                        # Attack with the selected unit
                        if self.selected_unit_pos and clicked_pos in self.valid_attack_positions:
                            result = self.controller.attack(self.selected_unit_pos, clicked_pos)
                            if result.get("success", False):
                                self.controller.show_message(result.get("message", "Attack successful!"), error=False)
                            else:
                                self.controller.show_message(result.get("message", "Attack failed"), error=True)
                            self.controller.action_state = "select"
                        else:
                            self.controller.show_message("Invalid attack target", error=True)
            
            # Check if a button was clicked
            for i, button in enumerate(self.buttons):
                if button.is_clicked(event.pos):
                    if i == 0:  # End Turn
                        self.controller.end_turn()
                        self.selected_unit_pos = None
                        self.valid_move_positions = []
                        self.valid_attack_positions = []
                    elif i == 1:  # Main Menu
                        self.controller.show_main_menu()
            
            # Check if an action button was clicked
            for i, button in enumerate(self.action_buttons):
                if button.is_clicked(event.pos):
                    if i == 0:  # Move
                        if self.selected_unit_pos:
                            self.controller.action_state = "move"
                            self._calculate_valid_moves()
                        else:
                            self.controller.show_message("Select a unit first", error=True)
                    elif i == 1:  # Attack
                        if self.selected_unit_pos:
                            self.controller.action_state = "attack"
                            self._calculate_valid_attacks()
                        else:
                            self.controller.show_message("Select a unit first", error=True)
    
    def update(self):
        """Update the view state"""
        # Update button hover states
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.update(mouse_pos)
        for button in self.action_buttons:
            button.update(mouse_pos)
        
        # Check if status message should expire
        if self.status_message and pygame.time.get_ticks() - self.message_time > 3000:
            self.status_message = ""
    
    def draw(self):
        """Draw the game view"""
        # Fill background
        self.screen.fill(self.LIGHT_BLUE)
        
        # Draw game title
        title_text = self.title_font.render("GOLDEN BRIGADE", True, self.BLACK)
        self.screen.blit(title_text, (20, 20))
        
        # Draw turn information
        turn_text = self.subtitle_font.render(
            f"Turn {self.controller.model.turn} - {self.controller.model.players[self.controller.model.current_player_index]}'s Turn",
            True, 
            self.CZECH_COLOR if self.controller.model.players[self.controller.model.current_player_index] == "Czech" else self.AUSTRIAN_COLOR
        )
        self.screen.blit(turn_text, (300, 20))
        
        # Draw game board
        self._draw_game_board()
        
        # Draw control panel
        self._draw_control_panel()
        
        # Draw status message
        if self.status_message:
            message_bg = pygame.Rect(0, self.height - 40, self.width, 40)
            pygame.draw.rect(self.screen, self.LIGHT_GRAY, message_bg)
            message_text = self.subtitle_font.render(self.status_message, True, self.message_color)
            message_rect = message_text.get_rect(center=(self.width//2, self.height - 20))
            self.screen.blit(message_text, message_rect)
    
    def _draw_game_board(self):
        """Draw the game board with terrain and units"""
        # Draw board background
        board_rect = pygame.Rect(
            self.board_offset_x,
            self.board_offset_y,
            self.controller.model.map_width * self.tile_size,
            self.controller.model.map_height * self.tile_size
        )
        pygame.draw.rect(self.screen, self.LIGHT_GRAY, board_rect)
        pygame.draw.rect(self.screen, self.BLACK, board_rect, 2)
        
        # Draw grid and terrain
        for x in range(self.controller.model.map_width):
            for y in range(self.controller.model.map_height):
                pos = (x, y)
                # Draw terrain
                terrain = self.controller.model.terrain.get(pos)
                if terrain:
                    terrain_rect = pygame.Rect(
                        self.board_offset_x + x * self.tile_size,
                        self.board_offset_y + y * self.tile_size,
                        self.tile_size,
                        self.tile_size
                    )
                    terrain_color = self.TERRAIN_COLORS.get(terrain.name, self.LIGHT_GRAY)
                    pygame.draw.rect(self.screen, terrain_color, terrain_rect)
                
                # Draw grid lines
                pygame.draw.rect(self.screen, self.BLACK, (
                    self.board_offset_x + x * self.tile_size,
                    self.board_offset_y + y * self.tile_size,
                    self.tile_size,
                    self.tile_size
                ), 1)
        
        # Highlight valid moves
        for pos in self.valid_move_positions:
            move_rect = pygame.Rect(
                self.board_offset_x + pos[0] * self.tile_size,
                self.board_offset_y + pos[1] * self.tile_size,
                self.tile_size,
                self.tile_size
            )
            pygame.draw.rect(self.screen, (0, 200, 0, 128), move_rect, 3)
        
        # Highlight valid attack targets
        for pos in self.valid_attack_positions:
            attack_rect = pygame.Rect(
                self.board_offset_x + pos[0] * self.tile_size,
                self.board_offset_y + pos[1] * self.tile_size,
                self.tile_size,
                self.tile_size
            )
            pygame.draw.rect(self.screen, (200, 0, 0, 128), attack_rect, 3)
        
        # Draw units
        for pos, unit in self.controller.model.units.items():
            x, y = pos
            unit_rect = pygame.Rect(
                self.board_offset_x + x * self.tile_size + 5,
                self.board_offset_y + y * self.tile_size + 5,
                self.tile_size - 10,
                self.tile_size - 10
            )
            
            # Draw unit circle with faction color
            unit_color = self.CZECH_COLOR if unit.faction == "Czech" else self.AUSTRIAN_COLOR
            pygame.draw.ellipse(self.screen, unit_color, unit_rect)
            pygame.draw.ellipse(self.screen, self.BLACK, unit_rect, 2)
            
            # Draw unit type initial
            unit_label = self.regular_font.render(unit.unit_type[0], True, self.WHITE)
            unit_label_rect = unit_label.get_rect(center=(
                self.board_offset_x + x * self.tile_size + self.tile_size // 2,
                self.board_offset_y + y * self.tile_size + self.tile_size // 2 - 5
            ))
            self.screen.blit(unit_label, unit_label_rect)
            
            # Draw health bar
            health_width = (self.tile_size - 10) * (unit.health / 100)
            health_rect = pygame.Rect(
                self.board_offset_x + x * self.tile_size + 5,
                self.board_offset_y + y * self.tile_size + self.tile_size - 10,
                health_width,
                5
            )
            pygame.draw.rect(self.screen, self.GREEN, health_rect)
            pygame.draw.rect(self.screen, self.BLACK, (
                self.board_offset_x + x * self.tile_size + 5,
                self.board_offset_y + y * self.tile_size + self.tile_size - 10,
                self.tile_size - 10,
                5
            ), 1)
        
        # Highlight selected unit
        if self.selected_unit_pos:
            x, y = self.selected_unit_pos
            selected_rect = pygame.Rect(
                self.board_offset_x + x * self.tile_size,
                self.board_offset_y + y * self.tile_size,
                self.tile_size,
                self.tile_size
            )
            pygame.draw.rect(self.screen, (255, 255, 0), selected_rect, 3)
    
    def _draw_control_panel(self):
        """Draw the control panel with unit info and buttons"""
        # Draw panel background
        pygame.draw.rect(self.screen, self.WHITE, self.panel_rect)
        pygame.draw.rect(self.screen, self.BLACK, self.panel_rect, 2)
        
        # Draw panel title
        panel_title = self.subtitle_font.render("Control Panel", True, self.BLACK)
        self.screen.blit(panel_title, (self.panel_rect.x + 20, self.panel_rect.y + 20))
        
        # Draw selected unit info
        if self.selected_unit_pos and self.selected_unit_pos in self.controller.model.units:
            unit = self.controller.model.units[self.selected_unit_pos]
            
            # Unit name
            unit_name = self.subtitle_font.render(unit.name, True, 
                                                self.CZECH_COLOR if unit.faction == "Czech" else self.AUSTRIAN_COLOR)
            self.screen.blit(unit_name, (self.panel_rect.x + 20, self.panel_rect.y + 60))
            
            # Unit stats
            stats_y = self.panel_rect.y + 100
            stats_data = [
                f"Type: {unit.unit_type}",
                f"Health: {unit.health}%",
                f"Attack: {unit.attack}",
                f"Defense: {unit.defense}",
                f"Movement: {unit.movement}",
                f"Experience: {unit.experience}"
            ]
            
            for stat in stats_data:
                stat_text = self.regular_font.render(stat, True, self.BLACK)
                self.screen.blit(stat_text, (self.panel_rect.x + 20, stats_y))
                stats_y += 30
            
            # Status
            status_y = stats_y + 10
            status_data = [
                f"Has moved: {'Yes' if unit.has_moved else 'No'}",
                f"Has attacked: {'Yes' if unit.has_attacked else 'No'}"
            ]
            
            for status in status_data:
                status_text = self.regular_font.render(status, True, 
                                                    self.RED if "Yes" in status else self.GREEN)
                self.screen.blit(status_text, (self.panel_rect.x + 20, status_y))
                status_y += 30
            
            # Action buttons
            for button in self.action_buttons:
                button.draw(self.screen)
        else:
            # No unit selected
            no_unit_text = self.regular_font.render("No unit selected", True, self.GRAY)
            self.screen.blit(no_unit_text, (self.panel_rect.x + 20, self.panel_rect.y + 80))
        
        # Draw game controls
        for button in self.buttons:
            button.draw(self.screen)
    
    def _get_board_position(self, screen_pos):
        """Convert screen coordinates to board position"""
        x, y = screen_pos
        
        # Check if click is within board bounds
        if (self.board_offset_x <= x < self.board_offset_x + self.controller.model.map_width * self.tile_size and
            self.board_offset_y <= y < self.board_offset_y + self.controller.model.map_height * self.tile_size):
            
            # Convert to board coordinates
            board_x = (x - self.board_offset_x) // self.tile_size
            board_y = (y - self.board_offset_y) // self.tile_size
            
            return (board_x, board_y)
        
        return None
    
    def _calculate_valid_moves(self):
        """Calculate valid movement positions for the selected unit"""
        if not self.selected_unit_pos or self.selected_unit_pos not in self.controller.model.units:
            self.valid_move_positions = []
            return
        
        unit = self.controller.model.units[self.selected_unit_pos]
        
        # If unit has already moved, no valid moves
        if unit.has_moved:
            self.valid_move_positions = []
            return
        
        # Get valid movement positions
        valid_moves = []
        movement_range = unit.movement
        
        # Check all positions within movement range
        for dx in range(-movement_range, movement_range + 1):
            for dy in range(-movement_range, movement_range + 1):
                # Skip the unit's current position
                if dx == 0 and dy == 0:
                    continue
                
                # Check if position is within movement range (Manhattan distance)
                if abs(dx) + abs(dy) > movement_range:
                    continue
                
                # Calculate target position
                target_x = self.selected_unit_pos[0] + dx
                target_y = self.selected_unit_pos[1] + dy
                target_pos = (target_x, target_y)
                
                # Check if position is within map bounds
                if (0 <= target_x < self.controller.model.map_width and
                    0 <= target_y < self.controller.model.map_height):
                    
                    # Check if position is not occupied by another unit
                    if target_pos not in self.controller.model.units:
                        valid_moves.append(target_pos)
        
        self.valid_move_positions = valid_moves
    
    def _calculate_valid_attacks(self):
        """Calculate valid attack targets for the selected unit"""
        if not self.selected_unit_pos or self.selected_unit_pos not in self.controller.model.units:
            self.valid_attack_positions = []
            return
        
        unit = self.controller.model.units[self.selected_unit_pos]
        
        # If unit has already attacked, no valid attacks
        if unit.has_attacked:
            self.valid_attack_positions = []
            return
        
        # Get attack range based on unit type
        if unit.unit_type == "Artillery":
            attack_range = 4
        elif unit.unit_type == "Missile":
            attack_range = 5
        elif unit.unit_type == "Air":
            attack_range = 6
        else:
            attack_range = 1  # Infantry and Armor have range 1
        
        valid_attacks = []
        
        # Check all positions within attack range
        for dx in range(-attack_range, attack_range + 1):
            for dy in range(-attack_range, attack_range + 1):
                # Skip the unit's current position
                if dx == 0 and dy == 0:
                    continue
                
                # Check if position is within attack range (Manhattan distance)
                if abs(dx) + abs(dy) > attack_range:
                    continue
                
                # Calculate target position
                target_x = self.selected_unit_pos[0] + dx
                target_y = self.selected_unit_pos[1] + dy
                target_pos = (target_x, target_y)
                
                # Check if position is within map bounds
                if (0 <= target_x < self.controller.model.map_width and
                    0 <= target_y < self.controller.model.map_height):
                    
                    # Check if position contains an enemy unit
                    if target_pos in self.controller.model.units:
                        target_unit = self.controller.model.units[target_pos]
                        if target_unit.faction != unit.faction:
                            valid_attacks.append(target_pos)
        
        self.valid_attack_positions = valid_attacks
    
    def show_message(self, message, error=False):
        """Display a status message"""
        self.status_message = message
        self.message_color = self.RED if error else self.GREEN
        self.message_time = pygame.time.get_ticks()
    
    def update_game_view(self):
        """Update the game view after model changes"""
        # Reset selections
        self.selected_unit_pos = None
        self.valid_move_positions = []
        self.valid_attack_positions = []
    
    def update_turn_info(self):
        """Update turn information"""
        # This doesn't need any special handling as we read directly from the model
        pass
    
    def switch_to_game_view(self):
        """Switch to the game view"""
        # Reset state when switching to game view
        self.selected_unit_pos = None
        self.valid_move_positions = []
        self.valid_attack_positions = []
        self.status_message = ""
        self.controller.action_state = "select"