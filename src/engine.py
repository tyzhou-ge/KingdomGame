import random
import math
from collections import defaultdict

from models import GameState, Player, Tile
from config import (
    MAP_WIDTH, MAP_HEIGHT, NUM_PLAYERS, PLAYER_COLORS,
    CAPITAL_MIN_DISTANCE, BASE_LIFESPAN, SUPPLY_LIMIT
)

class GameEngine:
    """Manages the game logic and state transitions."""

    def __init__(self, players: list[Player]):
        self.game_state = GameState(MAP_WIDTH, MAP_HEIGHT, players)
        self._setup_capitals()

    def _setup_capitals(self):
        """Initializes capital positions for all players according to the rules."""
        
        # Create a list of all possible coordinates and shuffle it to ensure randomness
        all_coords = [(x, y) for x in range(MAP_WIDTH) for y in range(MAP_HEIGHT)]
        random.shuffle(all_coords)

        capitals = []
        for player in self.game_state.players:
            found_pos = False
            for i, (x, y) in enumerate(all_coords):
                # Check distance from other capitals
                is_valid = True
                for c_pos in capitals:
                    dist = abs(x - c_pos[0]) + abs(y - c_pos[1])
                    if dist <= CAPITAL_MIN_DISTANCE:
                        is_valid = False
                        break
                
                if is_valid:
                    capitals.append((x, y))
                    player.capital_pos = (x, y)
                    tile = self.game_state.get_tile(x, y)
                    if tile:
                        tile.owner = player
                        tile.is_capital = True
                        tile.armies[0] = 10 # Start with 10 armies in capital
                    
                    # Remove the used coordinate so it's not considered again
                    all_coords.pop(i)
                    found_pos = True
                    break
            
            if not found_pos:
                raise RuntimeError(f"Could not find a valid capital position for Player {player.id}. "
                                 f"Consider reducing CAPITAL_MIN_DISTANCE or NUM_PLAYERS.")
    
    def run_turn(self):
        """Executes a single turn of the game."""
        self.game_state.current_turn += 1
        print(f"--- Turn {self.game_state.current_turn} ---")

        self._generate_resources()
        all_actions = self._get_player_decisions()
        self._execute_moves_and_resolve_combats(all_actions)
        self._apply_attrition()
        self._check_game_over()

    def _generate_resources(self):
        """Each player territory generates one new army."""
        for row in self.game_state.map:
            for tile in row:
                if tile.owner:
                    tile.armies[0] += 1

    def _get_player_decisions(self) -> dict[int, dict[str, str]]:
        """Collects actions from all non-defeated players."""
        all_actions = {}
        for player in self.game_state.players:
            if not player.is_defeated:
                actions = player.agent.get_actions(self.game_state, player.id)
                all_actions[player.id] = actions
                player.last_actions = actions # Store actions for the next turn
        return all_actions

    def _execute_moves_and_resolve_combats(self, all_actions: dict[int, dict[str, str]]):
        # Structure to hold incoming armies for each tile: defaultdict(lambda: defaultdict(list))
        # Format: { (dest_x, dest_y): { player_id: [armies_list_1, armies_list_2, ...], ... }, ... }
        arrivals = defaultdict(lambda: defaultdict(list))

        # 1. Calculate destinations and gather moving armies
        for player_id, actions in all_actions.items():
            for coord_str, direction in actions.items():
                x, y = map(int, coord_str.split(','))
                tile = self.game_state.get_tile(x, y)
                if not tile or not tile.owner or tile.owner.id != player_id:
                    continue

                dx, dy = 0, 0
                if direction == 'up': dy = -1
                elif direction == 'down': dy = 1
                elif direction == 'left': dx = -1
                elif direction == 'right': dx = 1
                
                dest_x, dest_y = x + dx, y + dy

                # Move armies only if destination is valid
                if 0 <= dest_x < MAP_WIDTH and 0 <= dest_y < MAP_HEIGHT:
                    arrivals[(dest_x, dest_y)][player_id].append(list(tile.armies))
                    tile.armies = [0] * BASE_LIFESPAN # Armies have moved out
                else: # Hit a wall, armies stay
                    arrivals[(x, y)][player_id].append(list(tile.armies))
                    tile.armies = [0] * BASE_LIFESPAN

        # 2. Resolve conflicts and update tiles
        for (x, y), incoming_armies_by_player in arrivals.items():
            dest_tile = self.game_state.get_tile(x, y)
            if not dest_tile: continue

            # Merge all incoming armies for each player
            merged_incoming = {}
            for player_id, armies_lists in incoming_armies_by_player.items():
                total_armies = [0] * BASE_LIFESPAN
                for army_list in armies_lists:
                    for i in range(BASE_LIFESPAN):
                        total_armies[i] += army_list[i]
                merged_incoming[player_id] = total_armies
            
            owner = dest_tile.owner
            owner_id = owner.id if owner else -1

            attacker_ids = [pid for pid in merged_incoming if pid != owner_id]

            if not attacker_ids: # No attackers, only owner's armies (or empty tile)
                if owner_id in merged_incoming:
                    dest_tile.armies = merged_incoming[owner_id]
            else: # Combat
                self._resolve_combat(dest_tile, merged_incoming, owner_id, attacker_ids)

    def _resolve_combat(self, dest_tile: Tile, merged_incoming: dict, owner_id: int, attacker_ids: list[int]):
        # Calculate total attacker strength
        total_attacker_force = 0
        attacker_forces = {}
        for pid in attacker_ids:
            force = sum(merged_incoming[pid])
            total_attacker_force += force
            attacker_forces[pid] = force
        
        # Calculate defender strength
        defender_force = sum(dest_tile.armies)
        if owner_id in merged_incoming: # Reinforcements for defender
            defender_force += sum(merged_incoming[owner_id])

        # Record battle size
        dest_tile.last_turn_battle_size = total_attacker_force + defender_force

        # Apply random factor and rounding
        a_eff = math.ceil(total_attacker_force * random.uniform(0.7, 1.0))
        d_eff = math.ceil(defender_force * random.uniform(0.5, 1.0))

        if a_eff > d_eff: # Attackers win
            winner_id = random.choice(attacker_ids) # Choose a winner among attackers
            winner_player = next(p for p in self.game_state.players if p.id == winner_id)
            
            dest_tile.owner = winner_player
            
            # Calculate losses and remaining armies
            remaining_attacker_force = total_attacker_force - d_eff
            if total_attacker_force > 0:
                survival_ratio = max(0, remaining_attacker_force) / total_attacker_force
            else:
                survival_ratio = 0

            new_armies = [0] * BASE_LIFESPAN
            for pid in attacker_ids:
                for i in range(BASE_LIFESPAN):
                    new_armies[i] += round(merged_incoming[pid][i] * survival_ratio)
            dest_tile.armies = new_armies

        else: # Defenders win
            remaining_defender_force = defender_force - a_eff
            if defender_force > 0:
                survival_ratio = max(0, remaining_defender_force) / defender_force
            else:
                survival_ratio = 0
            
            new_armies = [0] * BASE_LIFESPAN
            # Existing armies on tile
            for i in range(BASE_LIFESPAN):
                new_armies[i] += round(dest_tile.armies[i] * survival_ratio)
            # Reinforcing armies
            if owner_id in merged_incoming:
                for i in range(BASE_LIFESPAN):
                    new_armies[i] += round(merged_incoming[owner_id][i] * survival_ratio)
            dest_tile.armies = new_armies

    def _apply_attrition(self):
        """Applies aging and supply limit penalties to all armies."""
        for row in self.game_state.map:
            for tile in row:
                tile.last_turn_battle_size = 0
                total_armies = tile.get_total_armies()
                aging_speed = 1
                if total_armies > SUPPLY_LIMIT:
                    aging_speed = math.ceil(1 + (total_armies - SUPPLY_LIMIT) / SUPPLY_LIMIT)
                
                new_armies = [0] * BASE_LIFESPAN
                for age, count in enumerate(tile.armies):
                    new_age = age + aging_speed
                    if new_age < BASE_LIFESPAN:
                        new_armies[new_age] += count
                tile.armies = new_armies

    def _check_game_over(self):
        """Checks if any capitals have been captured."""
        active_players = 0
        for player in self.game_state.players:
            if player.is_defeated:
                continue
            
            capital_tile = self.game_state.get_tile(*player.capital_pos)
            if capital_tile and capital_tile.owner and capital_tile.owner.id != player.id:
                print(f"Player {player.name} has been defeated! Their capital was captured by Player {capital_tile.owner.name}.")
                player.is_defeated = True
            
            if not player.is_defeated:
                active_players += 1
        
        if active_players <= 1:
            winner = next((p for p in self.game_state.players if not p.is_defeated), None)
            if winner:
                print(f"Game Over! The winner is Player {winner.name}!")
            else:
                print("Game Over! No winner.")
            return True
        return False

    def is_game_over(self) -> bool:
        """Returns True if the game has ended."""
        return sum(1 for p in self.game_state.players if not p.is_defeated) <= 1
