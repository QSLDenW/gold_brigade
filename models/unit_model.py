# models/unit_model.py

class Unit:
    def __init__(self, name, attack, defense, movement, unit_type, faction, health=100, experience=0):
        self.name = name
        self.attack = attack
        self.defense = defense
        self.movement = movement
        self.unit_type = unit_type
        self.faction = faction
        self.health = health
        self.experience = experience
        self.has_moved = False
        self.has_attacked = False
    
    def reset_turn(self):
        """Reset unit status for a new turn"""
        self.has_moved = False
        self.has_attacked = False

class UnitFactory:
    def __init__(self):
        # Define unit templates
        self.unit_templates = {
            # Czech units
            "czech_infantry": {"name": "Czech Infantry", "attack": 3, "defense": 3, "movement": 2, "unit_type": "Infantry"},
            "czech_tank": {"name": "T-72M4 CZ", "attack": 6, "defense": 5, "movement": 3, "unit_type": "Armor"},
            "czech_artillery": {"name": "DANA Howitzer", "attack": 7, "defense": 2, "movement": 1, "unit_type": "Artillery"},
            "czech_air": {"name": "L-159 ALCA", "attack": 8, "defense": 3, "movement": 4, "unit_type": "Air"},
            "czech_missile": {"name": "RBS-70 SAM", "attack": 6, "defense": 2, "movement": 1, "unit_type": "Missile"},
            "czech_drone": {"name": "ScanEagle UAV", "attack": 4, "defense": 1, "movement": 3, "unit_type": "Drone"},
            
            # Austrian units
            "austrian_infantry": {"name": "Austrian Infantry", "attack": 3, "defense": 3, "movement": 2, "unit_type": "Infantry"},
            "austrian_tank": {"name": "Leopard 2A4", "attack": 7, "defense": 5, "movement": 3, "unit_type": "Armor"},
            "austrian_artillery": {"name": "M109 Howitzer", "attack": 7, "defense": 2, "movement": 1, "unit_type": "Artillery"},
            "austrian_air": {"name": "Eurofighter Typhoon", "attack": 9, "defense": 4, "movement": 5, "unit_type": "Air"},
            "austrian_missile": {"name": "Mistral SAM", "attack": 6, "defense": 2, "movement": 1, "unit_type": "Missile"},
            "austrian_drone": {"name": "Tracker UAV", "attack": 4, "defense": 1, "movement": 3, "unit_type": "Drone"}
        }
    
    def create_unit(self, unit_type, faction, health=100, experience=0):
        """Create a unit from a template type"""
        if unit_type not in self.unit_templates:
            raise ValueError(f"Unknown unit type: {unit_type}")
        
        template = self.unit_templates[unit_type]
        return Unit(
            template["name"],
            template["attack"],
            template["defense"],
            template["movement"],
            template["unit_type"],
            faction,
            health,
            experience
        )
    
    def create_unit_from_data(self, unit_data):
        """Create a unit from network data"""
        return Unit(
            unit_data.get("name", "Unknown"),
            unit_data.get("attack", 0),
            unit_data.get("defense", 0),
            unit_data.get("movement", 0),
            unit_data.get("type", "Infantry"),
            unit_data.get("faction", "Czech"),
            unit_data.get("health", 100),
            unit_data.get("experience", 0)
        )