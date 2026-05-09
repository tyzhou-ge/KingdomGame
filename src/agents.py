import random
from abc import ABC, abstractmethod
from models import GameState

class BaseAgent(ABC):
    """Abstract base class for all agents."""
    @abstractmethod
    def get_actions(self, game_state: GameState, player_id: int) -> dict[str, str]:
        """
        Determines the actions for the current turn.

        Args:
            game_state: The current state of the game.
            player_id: The ID of the player this agent controls.

        Returns:
            A dictionary mapping tile coordinates (e.g., "x,y") to a direction
            ("up", "down", "left", "right", "stay").
        """
        pass

class RandomAgent(BaseAgent):
    """An agent that makes random moves."""
    def get_actions(self, game_state: GameState, player_id: int) -> dict[str, str]:
        actions = {}
        player = next((p for p in game_state.players if p.id == player_id), None)
        if not player or player.is_defeated:
            return {}

        directions = ["up", "down", "left", "right", "stay"]
        
        for y, row in enumerate(game_state.map):
            for x, tile in enumerate(row):
                if tile.owner and tile.owner.id == player_id:
                    coord_str = f"{x},{y}"
                    actions[coord_str] = random.choice(directions)
        
        return actions

class HumanAgent(BaseAgent):
    """
    An agent controlled by a human player.
    Its get_actions method is a placeholder; the actual input is handled in the main loop.
    """
    def get_actions(self, game_state: GameState, player_id: int) -> dict[str, str]:
        # This agent doesn't decide on its own.
        # The main game loop will prompt for input when it sees this agent type.
        return {}

class DefensiveAgent(BaseAgent):
    """An agent that prioritizes defending its capital and borders."""
    def get_actions(self, game_state: GameState, player_id: int) -> dict[str, str]:
        actions = {}
        player = next((p for p in game_state.players if p.id == player_id), None)
        if not player or player.is_defeated:
            return {}

        my_tiles = []
        for y, row in enumerate(game_state.map):
            for x, tile in enumerate(row):
                if tile.owner and tile.owner.id == player_id:
                    my_tiles.append(tile)

        for tile in my_tiles:
            x, y = tile.x, tile.y
            # Default action is to stay
            best_move = "stay"
            
            # Move towards the capital if far away
            dist_to_capital = abs(x - player.capital_pos[0]) + abs(y - player.capital_pos[1])
            if dist_to_capital > 3:
                # Simple logic to move towards capital
                if x < player.capital_pos[0]: best_move = "right"
                elif x > player.capital_pos[0]: best_move = "left"
                elif y < player.capital_pos[1]: best_move = "down"
                elif y > player.capital_pos[1]: best_move = "up"
            
            actions[f"{x},{y}"] = best_move
        return actions

class GreedyAgent(BaseAgent):
    """An agent that aggressively expands and attacks weak targets."""
    def get_actions(self, game_state: GameState, player_id: int) -> dict[str, str]:
        actions = {}
        player = next((p for p in game_state.players if p.id == player_id), None)
        if not player or player.is_defeated:
            return {}

        for y, row in enumerate(game_state.map):
            for x, tile in enumerate(row):
                if tile.owner and tile.owner.id == player_id:
                    my_force = tile.get_total_armies()
                    best_move = "stay"
                    weakest_target_force = float('inf')

                    # Check neighbors
                    for direction, (dx, dy) in {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}.items():
                        nx, ny = x + dx, y + dy
                        neighbor = game_state.get_tile(nx, ny)
                        if neighbor:
                            # If neighbor is an enemy and we are stronger
                            if neighbor.owner and neighbor.owner.id != player_id:
                                neighbor_force = neighbor.get_total_armies()
                                # A simple heuristic: attack if we are stronger
                                if my_force > neighbor_force and neighbor_force < weakest_target_force:
                                    weakest_target_force = neighbor_force
                                    best_move = direction
                    
                    actions[f"{x},{y}"] = best_move
        return actions
