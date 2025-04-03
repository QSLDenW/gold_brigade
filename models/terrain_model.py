# models/terrain_model.py

class Terrain:
    def __init__(self, name, movement_cost, defense_bonus):
        self.name = name
        self.movement_cost = movement_cost
        self.defense_bonus = defense_bonus

class TerrainFactory:
    def __init__(self):
        # Define terrain templates
        self.terrain_templates = {
            "plains": {"name": "Plains", "movement_cost": 1, "defense_bonus": 0},
            "forest": {"name": "Forest", "movement_cost": 2, "defense_bonus": 2},
            "mountain": {"name": "Mountain", "movement_cost": 3, "defense_bonus": 3},
            "river": {"name": "River", "movement_cost": 4, "defense_bonus": 1},
            "road": {"name": "Road", "movement_cost": 0.5, "defense_bonus": 0},
            "urban": {"name": "Urban", "movement_cost": 1.5, "defense_bonus": 4}
        }
    
    def create_terrain(self, terrain_type):
        """Create a terrain from a template type"""
        if terrain_type not in self.terrain_templates:
            raise ValueError(f"Unknown terrain type: {terrain_type}")
        
        template = self.terrain_templates[terrain_type]
        return Terrain(
            template["name"],
            template["movement_cost"],
            template["defense_bonus"]
        )
    
    def create_terrain_from_data(self, terrain_data):
        """Create a terrain from network data"""
        return Terrain(
            terrain_data.get("name", "Plains"),
            terrain_data.get("movement_cost", 1),
            terrain_data.get("defense_bonus", 0)
        )