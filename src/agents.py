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
