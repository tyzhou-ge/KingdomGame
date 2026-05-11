import pygame
import sys
from engine import GameEngine
from models import Player
from agents import RandomAgent, HumanAgent, GreedyAgent, DefensiveAgent
from config import PLAYER_COLORS, NUM_PLAYERS
from view import Renderer

def get_human_actions(renderer: Renderer, game_state, player_id):
    """Handles the interactive process of getting actions from a human player."""
    actions = {}
    
    my_tiles = []
    for y, row in enumerate(game_state.map):
        for x, tile in enumerate(row):
            if tile.owner and tile.owner.id == player_id:
                my_tiles.append(tile)

    tile_index = 0
    history = []

    while tile_index < len(my_tiles):
        tile = my_tiles[tile_index]
        x, y = tile.x, tile.y
        
        # Draw the scene with the highlighted tile
        renderer.draw(game_state)
        renderer.highlight_tile(x, y, flip_display=True)
        # pygame.display.flip() # This is now handled inside highlight_tile

        # Wait for keyboard input
        action_made = False
        while not action_made:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    renderer.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    direction = None
                    
                    # --- DEBUG PRINTS to see what Pygame receives ---
                    print(f"DEBUG: event.key={event.key}, key_name='{pygame.key.name(event.key)}', event.unicode='{event.unicode}'")
                    
                    # Use arrow keys for movement, fall back to WASD for compatibility
                    if event.key == pygame.K_UP or event.key == pygame.K_w: direction = "up"
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s: direction = "down"
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a: direction = "left"
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d: direction = "right"
                    elif event.key == pygame.K_SPACE: direction = "stay"
                    elif event.key == pygame.K_LSHIFT or event.key == pygame.K_q: # Undo last action
                        if history:
                            last_coord, _ = history.pop()
                            del actions[last_coord]
                            tile_index -= 1
                        action_made = True # Break inner loop to re-highlight previous tile
                        continue

                    if direction:
                        coord_str = f"{x},{y}"
                        actions[coord_str] = direction
                        history.append((coord_str, direction))
                        tile_index += 1
                        action_made = True
    return actions


def main():
    """Main function to run the game with Pygame visualization."""
    # Setup players and agents
    players = []
    # Player 1 is Human
    players.append(Player(player_id=1, name="Human", color=PLAYER_COLORS[1], agent=HumanAgent()))
    # Other players are AIs
    agent_types = [RandomAgent, GreedyAgent, DefensiveAgent, RandomAgent]
    for i in range(2, NUM_PLAYERS + 1):
        player_name = f"AI Player {i}"
        player_color = PLAYER_COLORS[i]
        # agent = agent_types[i-2]()
        agent = RandomAgent() # For testing, all AIs are random
        players.append(Player(player_id=i, name=player_name, color=player_color, agent=agent))

    # Initialize game components
    engine = GameEngine(players)
    renderer = Renderer()
    clock = pygame.time.Clock()

    running = True
    while running and not engine.is_game_over():
        # Event handling for quitting
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # --- Decision Making Phase ---
        all_actions = {}
        for player in engine.game_state.players:
            if not player.is_defeated:
                if isinstance(player.agent, HumanAgent):
                    # Special handling for human player
                    print("wait for human input...")
                    human_actions = get_human_actions(renderer, engine.game_state, player.id)
                    print("wait for human input... done")
                    all_actions[player.id] = human_actions
                else:
                    # AI players
                    all_actions[player.id] = player.agent.get_actions(engine.game_state, player.id)

        # --- Execution Phase ---
        # This part is now manually controlled instead of being inside engine.run_turn()
        engine.game_state.current_turn += 1
        print(f"--- Turn {engine.game_state.current_turn} ---")
        engine._generate_resources()
        engine._execute_moves_and_resolve_combats(all_actions)
        engine._apply_attrition()
        engine._check_game_over()


        # Rendering
        renderer.draw(engine.game_state)

        # Control game speed
        pygame.time.delay(500) # Pause for 500ms after AI turns

    # Game over loop
    while running:
        # Final render to show the last state
        renderer.draw(engine.game_state)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
    
    renderer.quit()
    sys.exit()

if __name__ == "__main__":
    main()
