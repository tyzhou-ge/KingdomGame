from engine import GameEngine
from models import Player
from agents import RandomAgent
from config import PLAYER_COLORS, MAP_WIDTH, MAP_HEIGHT

def print_map(game_state):
    """Prints a text representation of the map to the console."""
    header = "   " + "".join([f" {x:<2}" for x in range(MAP_WIDTH)])
    print(header)
    print("  +" + "---"*MAP_WIDTH + "+")

    for y, row in enumerate(game_state.map):
        p_row = f"{y:<2}|"
        a_row = "  |"
        for tile in row:
            if tile.owner:
                p_row += f" {tile.owner.id} "
                if tile.is_capital:
                    p_row = p_row[:-2] + "* " # Mark capital
            else:
                p_row += " . "
            a_row += f"{tile.get_total_armies():^3}"
        p_row += "|"
        a_row += "|"
        print(p_row)
        print(a_row)
    
    print("  +" + "---"*MAP_WIDTH + "+")
    print("Legend: P=Player ID, A=Armies, *=Capital")
    print("-" * 40)


def main():
    """Main function to run the game in text mode."""
    # Setup players and agents
    players = []
    for i in range(1, 6):
        print(f"Setting up Player {i}...")
        player_name = f"Player {i}"
        player_color = PLAYER_COLORS[i]
        agent = RandomAgent()
        players.append(Player(player_id=i, name=player_name, color=player_color, agent=agent))

    # Initialize and run the game engine
    engine = GameEngine(players)
    
    print("Initial Map State:")
    print_map(engine.game_state)

    while not engine.is_game_over():
        input("Press Enter to run the next turn...")
        engine.run_turn()
        print_map(engine.game_state)

if __name__ == "__main__":
    main()
