# network/message_protocol.py
import json # For JSON serialization
import pickle # For serialization of messages

# Message types
class MessageType:
    # Client to server messages
    REGISTER = "register"
    CREATE_GAME = "create_game"
    JOIN_GAME = "join_game"
    LIST_GAMES = "list_games"
    GAME_ACTION = "game_action"
    CHAT_MESSAGE = "chat"
    DISCONNECT = "disconnect"
    
    # Server to client messages
    REGISTER_RESPONSE = "register_response" 
    GAME_STATE = "game_state"
    GAME_LIST = "game_list"
    GAME_CREATED = "game_created"
    JOIN_RESPONSE = "join_response"
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"
    GAME_STARTED = "game_started"
    TURN_CHANGED = "turn_changed"
    UNIT_MOVED = "unit_moved"
    ATTACK_RESULT = "attack_result"
    GAME_ENDED = "game_ended"
    ACTION_RESPONSE = "action_response"

# Action types for GAME_ACTION messages
class ActionType:
    START_GAME = "start_game"
    MOVE_UNIT = "move_unit"
    ATTACK = "attack"
    END_TURN = "end_turn"

class Message:
    @staticmethod
    def register(player_name):
        return {
            "type": MessageType.REGISTER,
            "name": player_name
        }
    
    @staticmethod
    def create_game():
        return {
            "type": MessageType.CREATE_GAME
        }
    
    @staticmethod 
    def join_game(game_id):
        return {
            "type": MessageType.JOIN_GAME,
            "game_id": game_id
        }
    
    @staticmethod
    def list_games():
        return {
            "type": MessageType.LIST_GAMES
        }
    
    @staticmethod
    def move_unit(from_pos, to_pos):
        return {
            "type": MessageType.GAME_ACTION,
            "action": ActionType.MOVE_UNIT,
            "data": {
                "from_x": from_pos[0],
                "from_y": from_pos[1],
                "to_x": to_pos[0],
                "to_y": to_pos[1]
            }
        }
    
    @staticmethod
    def attack(attacker_pos, defender_pos):
        return {
            "type": MessageType.GAME_ACTION,
            "action": ActionType.ATTACK,
            "data": {
                "attacker_x": attacker_pos[0],
                "attacker_y": attacker_pos[1],
                "defender_x": defender_pos[0],
                "defender_y": defender_pos[1]
            }
        }
    
    @staticmethod
    def end_turn():
        return {
            "type": MessageType.GAME_ACTION,
            "action": ActionType.END_TURN,
            "data": {}
        }
    
    @staticmethod
    def start_game(map_type="standard"):
        return {
            "type": MessageType.GAME_ACTION,
            "action": ActionType.START_GAME,
            "data": {
                "map_type": map_type
            }
        }
    
    @staticmethod
    def chat_message(message_text):
        return {
            "type": MessageType.CHAT_MESSAGE,
            "message": message_text
        }
    
    @staticmethod
    def disconnect():
        return {
            "type": MessageType.DISCONNECT
        }

def serialize_message(message):
    """Serialize message for transmission"""
    return pickle.dumps(message)

def deserialize_message(data):
    """Deserialize received message"""
    return pickle.loads(data)