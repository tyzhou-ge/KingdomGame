from __future__ import annotations
import typing
from config import BASE_LIFESPAN

if typing.TYPE_CHECKING:
    from agents import BaseAgent

class Tile:
    """Represents a single tile on the game map."""
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.owner: typing.Optional[Player] = None
        # armies[i] is the number of armies with age i
        self.armies: list[int] = [0] * BASE_LIFESPAN
        self.is_capital: bool = False

    def get_total_armies(self) -> int:
        """Returns the total number of armies on this tile."""
        return sum(self.armies)

class Player:
    """Represents a player in the game."""
    def __init__(self, player_id: int, name: str, color: tuple[int, int, int], agent: BaseAgent):
        self.id = player_id
        self.name = name
        self.color = color
        self.agent = agent
        self.capital_pos: tuple[int, int] = (-1, -1)
        self.is_defeated: bool = False

class GameState:
    """Contains the entire state of the game at a point in time."""
    def __init__(self, map_width: int, map_height: int, players: list[Player]):
        self.map: list[list[Tile]] = [
            [Tile(x, y) for x in range(map_width)] for y in range(map_height)
        ]
        self.players = players
        self.current_turn: int = 0

    def get_tile(self, x: int, y: int) -> typing.Optional[Tile]:
        """Gets a tile at a specific coordinate, returns None if out of bounds."""
        if 0 <= y < len(self.map) and 0 <= x < len(self.map[0]):
            return self.map[y][x]
        return None
