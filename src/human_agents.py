import pygame
import sys
import copy
from view import Renderer
from models import GameState, Player 


def get_free_roam_actions(renderer: Renderer, game_state: GameState, player_id: int, initial_actions: dict):
    """
    FREE_ROAM模式详细逻辑：

    1. 决策开始时，高亮玩家的首都格子。
    2. 玩家可以通过方向键（↑↓←→）在己方领土格子之间移动高亮框：
        - 只有目标格子属于自己时，才允许移动高亮框，否则高亮框不动。
    3. 玩家可以使用 w、a、s、d、space 键为当前高亮格子设置行军方向：
        - w ：设置为“up”
        - s ：设置为“down”
        - a ：设置为“left”
        - d ：设置为“right”
        - space：设置为“stay”
    4. 玩家可以随时按 Enter 键结束本回合的决策。
    5. 在决策结束时：
        - 所有未被手动指定的己方格子，自动继承上一回合的指令（即 initial_actions 中的默认值）。
        - 对于那些从首都无法通过己方领土连通的“孤岛”地块，如果玩家没有手动为它们指定方向，则为它们分配一个随机方向（up/down/left/right/stay）。
    6. 整个过程中，每次有操作都应实时刷新渲染（高亮和箭头）。
    7. 返回值为所有己方格子的指令字典。
    """
    import random
    player = next((p for p in game_state.players if p.id == player_id), None)
    if not player:
        return {}
    # 1. 获取己方所有格子
    my_tiles = []
    tile_map = {}
    for y, row in enumerate(game_state.map):
        for x, tile in enumerate(row):
            if tile.owner and tile.owner.id == player_id:
                my_tiles.append((x, y))
                tile_map[(x, y)] = tile
    if not my_tiles:
        return {}
    # 2. 决策开始时高亮首都
    cx, cy = player.capital_pos
    current = (cx, cy)
    actions = dict(initial_actions)
    # 3. 主循环
    # 新增：方向键长按/短按状态追踪
    key_states = {pygame.K_UP: None, pygame.K_DOWN: None, pygame.K_LEFT: None, pygame.K_RIGHT: None}
    key_last_move = {k: 0 for k in key_states}
    MOVE_INTERVAL = 200  # ms
    clock = pygame.time.Clock()
    while True:
        need_render = False
        finished = False
        now = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                renderer.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                # 记录按下时间
                if event.key in key_states:
                    if key_states[event.key] is None:
                        key_states[event.key] = now
                        key_last_move[event.key] = now
                # 设置当前格子的指令（wsad/space）
                if event.key == pygame.K_w:
                    actions[f"{current[0]},{current[1]}"] = "up"
                    need_render = True
                elif event.key == pygame.K_s:
                    actions[f"{current[0]},{current[1]}"] = "down"
                    need_render = True
                elif event.key == pygame.K_a:
                    actions[f"{current[0]},{current[1]}"] = "left"
                    need_render = True
                elif event.key == pygame.K_d:
                    actions[f"{current[0]},{current[1]}"] = "right"
                    need_render = True
                elif event.key == pygame.K_SPACE:
                    actions[f"{current[0]},{current[1]}"] = "stay"
                    need_render = True
                elif event.key == pygame.K_RETURN:
                    finished = True
            elif event.type == pygame.KEYUP:
                if event.key in key_states:
                    # 松开时判断短按
                    if key_states[event.key] is not None:
                        duration = now - key_states[event.key]
                        if duration < MOVE_INTERVAL:
                            dx, dy = 0, 0
                            if event.key == pygame.K_UP:
                                dy = -1
                            elif event.key == pygame.K_DOWN:
                                dy = 1
                            elif event.key == pygame.K_LEFT:
                                dx = -1
                            elif event.key == pygame.K_RIGHT:
                                dx = 1
                            nx, ny = current[0] + dx, current[1] + dy
                            if (nx, ny) in tile_map:
                                current = (nx, ny)
                                need_render = True
                        key_states[event.key] = None
        # 长按逻辑
        for k in key_states:
            if key_states[k] is not None:
                if now - key_states[k] >= MOVE_INTERVAL:
                    if now - key_last_move[k] >= MOVE_INTERVAL:
                        dx, dy = 0, 0
                        if k == pygame.K_UP:
                            dy = -1
                        elif k == pygame.K_DOWN:
                            dy = 1
                        elif k == pygame.K_LEFT:
                            dx = -1
                        elif k == pygame.K_RIGHT:
                            dx = 1
                        nx, ny = current[0] + dx, current[1] + dy
                        if (nx, ny) in tile_map:
                            current = (nx, ny)
                            need_render = True
                            key_last_move[k] = now
        if need_render or finished:
            renderer.draw(game_state, actions, fog_of_war_player_id=player_id)
            renderer.highlight_tile(current[0], current[1], flip_display=True)
            pygame.display.flip()
        if finished:
            break
    # 4. 处理孤岛地块（无法从首都到达的格子）
    visited = set()
    queue = [player.capital_pos]
    while queue:
        x, y = queue.pop(0)
        if (x, y) in visited:
            continue
        visited.add((x, y))
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = x+dx, y+dy
            if (nx, ny) in tile_map and (nx, ny) not in visited:
                queue.append((nx, ny))
    unreachable = [pos for pos in my_tiles if pos not in visited]
    directions = ["up", "down", "left", "right", "stay"]
    for x, y in unreachable:
        if f"{x},{y}" not in actions or actions[f"{x},{y}"] == initial_actions.get(f"{x},{y}", "stay"):
            actions[f"{x},{y}"] = random.choice(directions)
    return actions


def get_detailed_actions(renderer: Renderer, game_state: GameState, player_id: int, initial_actions: dict):
    """
    Handles the classic, detailed, tile-by-tile action input from a human player.
    Receives the initial_actions dictionary with pre-filled defaults.
    """
    actions = initial_actions
    
    my_tiles = []
    for y, row in enumerate(game_state.map):
        for x, tile in enumerate(row):
            if tile.owner and tile.owner.id == player_id:
                my_tiles.append(tile)

    if not my_tiles:
        return {}

    tile_index = 0
    history = []

    while tile_index < len(my_tiles):
        tile = my_tiles[tile_index]
        x, y = tile.x, tile.y
        coord_str = f"{x},{y}"
        
        # Draw the board with current actions, including defaults
        print(f"####### rendering with default actions: {actions} #######")
        renderer.draw(game_state, actions)
        renderer.highlight_tile(x, y, flip_display=True)

        action_made = False
        while not action_made:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    renderer.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    direction = None
                    
                    if event.key == pygame.K_UP or event.key == pygame.K_w: direction = "up"
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s: direction = "down"
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a: direction = "left"
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d: direction = "right"
                    elif event.key == pygame.K_SPACE: direction = "stay"
                    elif event.key == pygame.K_RETURN: # ENTER key
                        # Use the default action (which is already in the actions dict)
                        direction = actions.get(coord_str, "stay")
                    elif event.key == pygame.K_q: # Undo last action
                        if history:
                            last_coord, last_direction = history.pop()
                            # This undo logic might need refinement if we want to revert to the *original* default
                            actions[last_coord] = last_direction 
                            tile_index -= 1
                        action_made = True
                        continue

                    if direction:
                        history.append((coord_str, actions.get(coord_str))) # Save old action for undo
                        actions[coord_str] = direction
                        tile_index += 1
                        action_made = True
    return actions

def get_uniform_direction_action(renderer: Renderer, game_state: GameState, player_id: int, initial_actions: dict):
    """
    A simple input mode where the player chooses one direction for all their units.
    Receives the initial_actions dictionary with pre-filled defaults.
    """
    default_actions = initial_actions

    # Show default actions first
    renderer.draw(game_state, default_actions)
    pygame.display.flip()

    direction = None
    use_defaults = False
    while not direction and not use_defaults:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                renderer.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_w: direction = "up"
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s: direction = "down"
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a: direction = "left"
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d: direction = "right"
                elif event.key == pygame.K_SPACE: direction = "stay"
                elif event.key == pygame.K_RETURN: # ENTER key
                    use_defaults = True

    if use_defaults:
        return default_actions

    actions = {}
    for y, row in enumerate(game_state.map):
        for x, tile in enumerate(row):
            if tile.owner and tile.owner.id == player_id:
                coord_str = f"{x},{y}"
                actions[coord_str] = direction
    return actions

def get_human_actions(renderer: Renderer, game_state: GameState, player_id: int, mode: str):
    """
    Calculates default actions and then calls the appropriate input mode function.
    Now supports HUMAN_INPUT_MODE from config.py, including FREE_ROAM mode.
    """
    from config import HUMAN_INPUT_MODE
    player = next((p for p in game_state.players if p.id == player_id), None)
    if not player:
        return {}

    # 1. Centralized logic to determine default actions
    default_actions = copy.deepcopy(player.last_actions)
    num_tiles = 0
    for y, row in enumerate(game_state.map):
        for x, tile in enumerate(row):
            if tile.owner and tile.owner.id == player_id:
                num_tiles += 1
                coord_str = f"{x},{y}"
                if coord_str not in default_actions:
                    default_actions[coord_str] = "stay"

    # 2. Show the correct default actions on screen once before asking for input
    print(f"####### rendering with default actions: {default_actions} #######")
    renderer.draw(game_state, default_actions)
    pygame.display.flip()

    # 3. Determine input mode
    input_mode = HUMAN_INPUT_MODE if HUMAN_INPUT_MODE else mode
    print(f"Using input mode: {input_mode} ")

    if num_tiles < 5:
        return get_detailed_actions(renderer, game_state, player_id, default_actions)

    if input_mode == 'detailed':
        return get_detailed_actions(renderer, game_state, player_id, default_actions)
    elif input_mode == 'uniform':
        return get_uniform_direction_action(renderer, game_state, player_id, default_actions)
    elif input_mode == 'FREE_ROAM':
        return get_free_roam_actions(renderer, game_state, player_id, default_actions)
    else:
        print(f"Unknown input mode: {input_mode}. Defaulting to detailed mode.")
        return get_detailed_actions(renderer, game_state, player_id, default_actions)
