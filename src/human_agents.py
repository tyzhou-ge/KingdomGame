import pygame
import sys
import copy
from view import Renderer
from models import GameState, Player 

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
    """
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

    # 3. Call the specific input handler, passing the calculated defaults to it
    if num_tiles < 5:
        return get_detailed_actions(renderer, game_state, player_id, default_actions)

    if mode == 'detailed':
        return get_detailed_actions(renderer, game_state, player_id, default_actions)
    elif mode == 'uniform':
        return get_uniform_direction_action(renderer, game_state, player_id, default_actions)
    else:
        print(f"Unknown input mode: {mode}. Defaulting to detailed mode.")
        return get_detailed_actions(renderer, game_state, player_id, default_actions)
