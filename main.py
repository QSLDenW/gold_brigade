# main.py
import pygame
import sys
import argparse
from controllers.game_controller import GameController
from views.main_menu_view import MainMenuView
from views.game_view import GameView
from views.multiplayer_view import MultiplayerView
from views.map_designer_view import MapDesignerView

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Golden Brigade - Czech vs Austria Strategy Game')
    parser.add_argument('--server', type=str, help='Server IP address for multiplayer')
    parser.add_argument('--port', type=int, default=5555, help='Server port for multiplayer')
    parser.add_argument('--name', type=str, default="Player", help='Player name for multiplayer')
    args = parser.parse_args()
    
    # Initialize pygame
    pygame.init()
    
    # Game constants
    SCREEN_WIDTH = 1920
    SCREEN_HEIGHT = 1080
    TITLE = "Golden Brigade - Czech vs Austria"
    
    # Create window
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    
    # Create controller
    controller = GameController()
    
    # Create views
    main_menu_view = MainMenuView(screen, controller)
    game_view = GameView(screen, controller)
    multiplayer_view = MultiplayerView(screen, controller)
    map_designer_view = MapDesignerView(screen, controller)
    
    # Set initial view
    current_view = main_menu_view
    controller.set_view(current_view)
    
    # If server is specified, connect directly
    if args.server:
        controller.connect_to_server(args.name, args.server, args.port)
        controller.game_state = "multiplayer_menu"
        controller.mp_menu_state = "join"
        current_view = multiplayer_view
        controller.set_view(current_view)
    
    # Main game loop
    clock = pygame.time.Clock()
    running = True
    
    while running:
        # Handle events
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            
            # Pass events to current view
            current_view.handle_event(event)
        
        # Check if view has changed
        if controller.game_state == "main_menu":
            if current_view != main_menu_view:
                current_view = main_menu_view
                controller.set_view(current_view)
        elif controller.game_state == "play":
            if current_view != game_view:
                current_view = game_view
                controller.set_view(current_view)
        elif controller.game_state == "multiplayer_menu":
            if current_view != multiplayer_view:
                current_view = multiplayer_view
                controller.set_view(current_view)
        elif controller.game_state == "designer":
            if current_view != map_designer_view:
                current_view = map_designer_view
                controller.set_view(current_view)
        
        # Update current view
        current_view.update()
        
        # Draw current view
        current_view.draw()
        
        # Update display
        pygame.display.flip()
        
        # Cap the frame rate
        clock.tick(60)
    
    # Clean up
    if hasattr(controller, 'network') and controller.network:
        controller.network.disconnect()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()