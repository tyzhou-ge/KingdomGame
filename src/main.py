import pygame
import sys
from engine import GameEngine
from models import Player
from agents import RandomAgent, HumanAgent, GreedyAgent, DefensiveAgent, StrategicAgent
from config import PLAYER_COLORS, NUM_PLAYERS
from view import Renderer
from human_agents import get_human_actions


def main():
    """Main function to run the game with Pygame visualization."""
    # Setup players and agents
    players = []
    # Player 1 is Human
    players.append(Player(player_id=1, name="Human", color=PLAYER_COLORS[1], agent=HumanAgent()))
    # players.append(Player(player_id=2, name="Human", color=PLAYER_COLORS[2], agent=HumanAgent()))
    # # Other players are AIs
    # agent_types = [StrategicAgent, GreedyAgent, DefensiveAgent, RandomAgent]
    # for i in range(3, NUM_PLAYERS + 1):
    #     player_name = f"AI Player {i}"
    #     player_color = PLAYER_COLORS[i]
    #     agent = StrategicAgent() if i==3 else RandomAgent()
    #     players.append(Player(player_id=i, name=player_name, color=player_color, agent=agent))
    for i in range(2, NUM_PLAYERS + 1):
        player_name = f"AI Player {i}"
        player_color = PLAYER_COLORS[i]
        agent = StrategicAgent() if i==4 else RandomAgent()
        players.append(Player(player_id=i, name=player_name, color=player_color, agent=agent))

    # Initialize game components
    engine = GameEngine(players)
    renderer = Renderer()
    clock = pygame.time.Clock()

    running = True
    while running and not engine.is_game_over():
        # Event handling for quitting
        # This is now handled inside get_human_actions, but we keep a basic one here for the main loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # --- Decision Making Phase ---
        all_actions = {}
        for player in engine.game_state.players:
            if not player.is_defeated:
                actions = {}
                if isinstance(player.agent, HumanAgent):
                    # Special handling for human player
                    print(f"Waiting for Player {player.id}'s input...")
                    actions = get_human_actions(renderer, engine.game_state, player.id, mode = 'detailed') # mode can be determined inside get_human_actions
                    print(f"Player {player.id}'s input received.")
                else:
                    # AI players
                    actions = player.agent.get_actions(engine.game_state, player.id)
                
                all_actions[player.id] = actions
                player.last_actions = actions # Ensure last_actions is updated

        # --- Execution Phase ---
        # This part is now manually controlled instead of being inside engine.run_turn()
        engine.game_state.current_turn += 1
        print(f"--- Turn {engine.game_state.current_turn} ---")
        engine._generate_resources()
        engine._execute_moves_and_resolve_combats(all_actions)
        engine._apply_attrition()
        engine._check_game_over()


        # Rendering
        renderer.draw(engine.game_state, all_actions)

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
