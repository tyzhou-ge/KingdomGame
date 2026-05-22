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

class StrategicAgent(BaseAgent):
    """A strategic agent with advanced logic as described in algorithm.md."""
    def get_actions(self, game_state: GameState, player_id: int) -> dict[str, str]:
        from collections import deque
        actions = {}
        player = next((p for p in game_state.players if p.id == player_id), None)
        if not player or player.is_defeated:
            return {}

        # Helper: Manhattan distance
        def manhattan(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        # Helper: BFS for shortest path
        def bfs(start, goals, passable_fn):
            queue = deque([(start, [])])
            visited = set([start])
            while queue:
                (x, y), path = queue.popleft()
                if (x, y) in goals:
                    return path + [(x, y)]
                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nx, ny = x+dx, y+dy
                    if 0 <= nx < len(game_state.map[0]) and 0 <= ny < len(game_state.map):
                        if (nx, ny) not in visited and passable_fn(nx, ny):
                            visited.add((nx, ny))
                            queue.append(((nx, ny), path + [(x, y)]))
            return None

        my_tiles = []
        border_tiles = []
        neutral_border_tiles = []
        enemy_border_tiles = []
        for y, row in enumerate(game_state.map):
            for x, tile in enumerate(row):
                if tile.owner and tile.owner.id == player_id:
                    my_tiles.append((x, y))
                    # Check neighbors
                    is_border = False
                    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nx, ny = x+dx, y+dy
                        neighbor = game_state.get_tile(nx, ny)
                        if neighbor:
                            if not neighbor.owner:
                                is_border = True
                                neutral_border_tiles.append((x, y))
                            elif neighbor.owner.id != player_id:
                                is_border = True
                                enemy_border_tiles.append((x, y))
                    if is_border:
                        border_tiles.append((x, y))

        # 1. 全局扫描：有敌人相邻？
        if enemy_border_tiles:
            # 战争状态
            # 首都圈防御
            capital_x, capital_y = player.capital_pos
            for x, y in enemy_border_tiles:
                dist = manhattan((x, y), (capital_x, capital_y))
                # 检查是否在绝对防御圈内
                if dist <= 2:
                    # 检查是否在敌方到首都的最短路径上
                    # 找所有敌方格子
                    enemy_tiles = [(ex, ey) for ey, row in enumerate(game_state.map) for ex, t in enumerate(row) if t.owner and t.owner.id != player_id]
                    on_path = False
                    for ex, ey in enemy_tiles:
                        path = bfs((ex, ey), {(capital_x, capital_y)}, lambda nx, ny: game_state.get_tile(nx, ny).owner and game_state.get_tile(nx, ny).owner.id != player_id or (nx, ny)==(capital_x, capital_y))
                        if path and (x, y) in path:
                            on_path = True
                            break
                    if on_path:
                        actions[f"{x},{y}"] = "stay"
                        continue
                # 其他边境格子进攻相邻敌人
                for dx, dy, dir in [(-1,0,"left"),(1,0,"right"),(0,-1,"up"),(0,1,"down")]:
                    nx, ny = x+dx, y+dy
                    neighbor = game_state.get_tile(nx, ny)
                    if neighbor and neighbor.owner and neighbor.owner.id != player_id:
                        actions[f"{x},{y}"] = dir
                        break
            # 首都圈安全评估
            safe = True
            for dx in range(-3,4):
                for dy in range(-3,4):
                    nx, ny = capital_x+dx, capital_y+dy
                    if 0 <= nx < len(game_state.map[0]) and 0 <= ny < len(game_state.map):
                        tile = game_state.get_tile(nx, ny)
                        if not (tile.owner and tile.owner.id == player_id):
                            safe = False
            if safe:
                # 斩首行动
                # 找最近敌方首都
                enemy_capitals = [(p.capital_pos, p.id) for p in game_state.players if p.id != player_id and not p.is_defeated]
                my_capital = player.capital_pos
                min_dist = float('inf')
                target_cap = None
                for pos, eid in enemy_capitals:
                    d = manhattan(my_capital, pos)
                    if d < min_dist:
                        min_dist = d
                        target_cap = pos
                # 所有己方格子向目标首都进军
                for x, y in my_tiles:
                    if f"{x},{y}" not in actions:
                        path = bfs((x, y), {target_cap}, lambda nx, ny: True)
                        if path and len(path) > 1:
                            nx, ny = path[1]
                            if nx > x: actions[f"{x},{y}"] = "right"
                            elif nx < x: actions[f"{x},{y}"] = "left"
                            elif ny > y: actions[f"{x},{y}"] = "down"
                            elif ny < y: actions[f"{x},{y}"] = "up"
                        else:
                            actions[f"{x},{y}"] = "stay"
            else:
                # 其他己方格子向最近边境集结
                for x, y in my_tiles:
                    if f"{x},{y}" not in actions:
                        # 向最近边境格子移动
                        if border_tiles:
                            path = bfs((x, y), set(border_tiles), lambda nx, ny: game_state.get_tile(nx, ny).owner and game_state.get_tile(nx, ny).owner.id == player_id)
                            if path and len(path) > 1:
                                nx2, ny2 = path[1]
                                if nx2 > x: actions[f"{x},{y}"] = "right"
                                elif nx2 < x: actions[f"{x},{y}"] = "left"
                                elif ny2 > y: actions[f"{x},{y}"] = "down"
                                elif ny2 < y: actions[f"{x},{y}"] = "up"
                            else:
                                actions[f"{x},{y}"] = "stay"
        else:
            # 和平扩张
            # 前线格子向最近中立格扩张
            neutral_tiles = [(x, y) for y, row in enumerate(game_state.map) for x, t in enumerate(row) if not t.owner]
            for x, y in neutral_border_tiles:
                if neutral_tiles:
                    path = bfs((x, y), set(neutral_tiles), lambda nx, ny: not game_state.get_tile(nx, ny).owner or game_state.get_tile(nx, ny).owner.id == player_id)
                    if path and len(path) > 1:
                        nx, ny = path[1]
                        if nx > x: actions[f"{x},{y}"] = "right"
                        elif nx < x: actions[f"{x},{y}"] = "left"
                        elif ny > y: actions[f"{x},{y}"] = "down"
                        elif ny < y: actions[f"{x},{y}"] = "up"
                    else:
                        actions[f"{x},{y}"] = "stay"
            # 内部格子向最近前线集结
            for x, y in my_tiles:
                if f"{x},{y}" not in actions:
                    if border_tiles:
                        path = bfs((x, y), set(border_tiles), lambda nx, ny: game_state.get_tile(nx, ny).owner and game_state.get_tile(nx, ny).owner.id == player_id)
                        if path and len(path) > 1:
                            nx2, ny2 = path[1]
                            if nx2 > x: actions[f"{x},{y}"] = "right"
                            elif nx2 < x: actions[f"{x},{y}"] = "left"
                            elif ny2 > y: actions[f"{x},{y}"] = "down"
                            elif ny2 < y: actions[f"{x},{y}"] = "up"
                        else:
                            actions[f"{x},{y}"] = "stay"
        return actions
