import pygame
import sys
from engine import GameEngine
from models import Player
from agents import RandomAgent
from config import PLAYER_COLORS, NUM_PLAYERS
from view import Renderer

def main():
    """Main function to run the game with Pygame visualization."""
    # Setup players and agents
    players = []
    for i in range(1, NUM_PLAYERS + 1):
        player_name = f"Player {i}"
        player_color = PLAYER_COLORS[i]
        agent = RandomAgent()
        players.append(Player(player_id=i, name=player_name, color=player_color, agent=agent))

    # Initialize game components
    engine = GameEngine(players)
    renderer = Renderer()
    clock = pygame.time.Clock()

    running = True
    while running and not engine.is_game_over():
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Game logic update
        engine.run_turn()

        # Rendering
        renderer.draw(engine.game_state)

        # Control game speed
        clock.tick(2) # Run 1 turn per second

    # Game over loop
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
    
    renderer.quit()
    sys.exit()

if __name__ == "__main__":
    main()
