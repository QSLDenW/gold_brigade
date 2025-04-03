# models/game_model.py
import random
from models.unit_model import Unit, UnitFactory
from models.terrain_model import Terrain, TerrainFactory

class GameModel:
    def __init__(self):
        self.map_width = 20
        self.map_height = 15
        self.terrain = {}  # (x, y) -> Terrain
        self.units = {}    # (x, y) -> Unit
        self.players = []  # List of players
        self.current_player_index = 0
        self.turn = 1
        self.max_turns = 20
        self.selected_unit_pos = None
        self.game_over = False
        self.winner = None
    
    def initialize_game(self):
        """Initialize a new game"""
        # Create terrain
        self._create_terrain()
        
        # Create units
        self._create_units()
        
        # Reset game state
        self.current_player_index = 0
        self.turn = 1
        self.game_over = False
        self.winner = None
    
    def _create_terrain(self):
        """Create terrain for the map"""
        terrain_factory = TerrainFactory()
        
        # Default to plains
        for x in range(self.map_width):
            for y in range(self.map_height):
                self.terrain[(x, y)] = terrain_factory.create_terrain("plains")
        
        # Add some forests
        for _ in range(30):
            x = random.randint(0, self.map_width - 1)
            y = random.randint(0, self.map_height - 1)
            self.terrain[(x, y)] = terrain_factory.create_terrain("forest")
        
        # Add some mountains
        for _ in range(20):
            x = random.randint(0, self.map_width - 1)
            y = random.randint(0, self.map_height - 1)
            self.terrain[(x, y)] = terrain_factory.create_terrain("mountain")
        
        # Add a river
        river_y = self.map_height // 2
        for x in range(self.map_width):
            self.terrain[(x, river_y)] = terrain_factory.create_terrain("river")
        
        # Add a road
        road_x = self.map_width // 2
        for y in range(self.map_height):
            self.terrain[(road_x, y)] = terrain_factory.create_terrain("road")
    
    def _create_units(self):
        """Create units for both players"""
        unit_factory = UnitFactory()
        
        # Create Czech units (left side of map)
        self.units[(1, 1)] = unit_factory.create_unit("czech_infantry", "Czech")
        self.units[(2, 3)] = unit_factory.create_unit("czech_tank", "Czech")
        self.units[(3, 5)] = unit_factory.create_unit("czech_artillery", "Czech")
        self.units[(1, 7)] = unit_factory.create_unit("czech_air", "Czech")
        self.units[(2, 9)] = unit_factory.create_unit("czech_missile", "Czech")
        
        # Create Austrian units (right side of map)
        self.units[(self.map_width-2, self.map_height-2)] = unit_factory.create_unit("austrian_infantry", "Austrian")
        self.units[(self.map_width-3, self.map_height-4)] = unit_factory.create_unit("austrian_tank", "Austrian")
        self.units[(self.map_width-4, self.map_height-6)] = unit_factory.create_unit("austrian_artillery", "Austrian")
        self.units[(self.map_width-2, self.map_height-8)] = unit_factory.create_unit("austrian_air", "Austrian")
        self.units[(self.map_width-3, self.map_height-10)] = unit_factory.create_unit("austrian_missile", "Austrian")
        
        # Create players
        self.players = ["Czech", "Austrian"]
    
    def next_player(self):
        """Move to the next player's turn"""
        # Switch to next player
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        
        # If we've gone through all players, advance the turn
        if self.current_player_index == 0:
            self.turn += 1
            
            # Reset all units for the new turn
            for unit_pos, unit in self.units.items():
                unit.reset_turn()
            
            # Check for game over conditions
            if self.turn > self.max_turns:
                self._check_game_over()
        
        return self.current_player_index
    
    def move_unit(self, from_pos, to_pos):
        """Move a unit from one position to another"""
        # Check if unit exists at from_pos
        if from_pos not in self.units:
            return False
        
        # Check if destination is valid
        if to_pos in self.units:
            return False
        
        # Check if destination is within map bounds
        if (to_pos[0] < 0 or to_pos[0] >= self.map_width or
            to_pos[1] < 0 or to_pos[1] >= self.map_height):
            return False
        
        # Get the unit and terrain
        unit = self.units[from_pos]
        terrain = self.terrain.get(to_pos, None)
        
        # Check if unit has already moved
        if unit.has_moved:
            return False
        
        # Check if it's this player's unit
        if unit.faction != self.players[self.current_player_index]:
            return False
        
        # Check movement range
        dx = abs(to_pos[0] - from_pos[0])
        dy = abs(to_pos[1] - from_pos[1])
        if dx + dy > unit.movement:
            return False
        
        # Move the unit
        self.units[to_pos] = unit
        del self.units[from_pos]
        
        # Mark the unit as having moved
        unit.has_moved = True
        
        return True
    
    def attack(self, attacker_pos, defender_pos):
        """Resolve an attack between two units"""
        # Check if units exist at positions
        if attacker_pos not in self.units or defender_pos not in self.units:
            return {"success": False, "message": "Invalid unit positions"}
        
        # Get the units
        attacker = self.units[attacker_pos]
        defender = self.units[defender_pos]
        
        # Check if it's attacker's turn
        if attacker.faction != self.players[self.current_player_index]:
            return {"success": False, "message": "Not your unit"}
        
        # Check if attacker has already attacked
        if attacker.has_attacked:
            return {"success": False, "message": "Unit has already attacked this turn"}
        
        # Check if defender is an enemy
        if attacker.faction == defender.faction:
            return {"success": False, "message": "Cannot attack friendly units"}
        
        # Check attack range
        dx = abs(defender_pos[0] - attacker_pos[0])
        dy = abs(defender_pos[1] - attacker_pos[1])
        attack_range = self._get_attack_range(attacker)
        if dx + dy > attack_range:
            return {"success": False, "message": "Target out of range"}
        
        # Get terrain for defense bonus
        terrain = self.terrain.get(defender_pos, None)
        defense_bonus = terrain.defense_bonus if terrain else 0
        
        # Perform attack
        attack_roll = random.randint(1, 6) + attacker.attack
        defense_roll = random.randint(1, 6) + defender.defense + defense_bonus
        
        # Mark the attacker as having attacked
        attacker.has_attacked = True
        
        # Determine result
        if attack_roll > defense_roll:
            # Attack succeeds
            damage = min(attack_roll - defense_roll, 50)
            defender.health -= damage
            
            # Check if defender is destroyed
            if defender.health <= 0:
                del self.units[defender_pos]
                
                # Award experience to attacker
                attacker.experience += 2
                if attacker.experience >= 10 and attacker.experience < 20:
                    attacker.attack += 1
                elif attacker.experience >= 20:
                    attacker.defense += 1
                
                result = {"success": True, "result": "destroyed", "message": f"{defender.name} destroyed!"}
            else:
                result = {"success": True, "result": "damaged", "damage": damage, 
                          "message": f"{defender.name} damaged! Health: {defender.health}%"}
        else:
            # Attack fails
            result = {"success": True, "result": "missed", "message": "Attack missed!"}
        
        # Check if game is over (one player has no units left)
        self._check_game_over()
        
        return result
    
    def _get_attack_range(self, unit):
        """Get the attack range for a unit based on type"""
        if unit.unit_type == "Artillery":
            return 4
        elif unit.unit_type == "Missile":
            return 5
        elif unit.unit_type == "Air":
            return 6
        else:
            return 1  # Infantry and Armor have range 1
    
    def _check_game_over(self):
        """Check if the game is over"""
        # Count units for each faction
        unit_counts = {"Czech": 0, "Austrian": 0}
        for unit in self.units.values():
            unit_counts[unit.faction] += 1
        
        # Check if either faction has no units left
        for faction, count in unit_counts.items():
            if count == 0:
                self.game_over = True
                self.winner = "Austrian" if faction == "Czech" else "Czech"
                return True
        
        # Check if max turns reached
        if self.turn > self.max_turns:
            self.game_over = True
            
            # Determine winner based on unit count
            if unit_counts["Czech"] > unit_counts["Austrian"]:
                self.winner = "Czech"
            elif unit_counts["Austrian"] > unit_counts["Czech"]:
                self.winner = "Austrian"
            else:
                self.winner = None  # It's a tie
            
            return True
        
        return False
    
    def update_from_network(self, state):
        """Update the model from network game state"""
        # Update map dimensions
        if "map" in state and state["map"]:
            self.map_width = state["map"].get("width", self.map_width)
            self.map_height = state["map"].get("height", self.map_height)
            
            # Update terrain if provided
            if "terrain" in state["map"]:
                self.terrain = {}
                terrain_factory = TerrainFactory()
                
                for pos_str, terrain_data in state["map"]["terrain"].items():
                    x, y = map(int, pos_str.split(","))
                    self.terrain[(x, y)] = terrain_factory.create_terrain_from_data(terrain_data)
        
        # Update units
        if "units" in state:
            self.units = {}
            unit_factory = UnitFactory()
            
            for pos_str, unit_data in state["units"].items():
                x, y = map(int, pos_str.split(","))
                self.units[(x, y)] = unit_factory.create_unit_from_data(unit_data)
        
        # Update turn and player info
        self.turn = state.get("turn", self.turn)
        
        # Update current player
        current_player_id = state.get("current_player")
        if current_player_id:
            # Determine if it's the local player's turn
            # This would need to know which player ID corresponds to which faction
            pass