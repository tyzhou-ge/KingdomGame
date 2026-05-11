import pygame
import sys
from view import Renderer
# Note: We may need to import GameState and Player for type hinting in the future
# from models import GameState, Player 

def get_detailed_actions(renderer: Renderer, game_state, player_id):
    """
    Handles the classic, detailed, tile-by-tile action input from a human player.
    """
    print("Detailed actions")
    actions = {}
    
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
        
        renderer.draw(game_state)
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
                    elif event.key == pygame.K_q: # Undo last action
                        if history:
                            last_coord, _ = history.pop()
                            del actions[last_coord]
                            tile_index -= 1
                        action_made = True
                        continue

                    if direction:
                        coord_str = f"{x},{y}"
                        actions[coord_str] = direction
                        history.append((coord_str, direction))
                        tile_index += 1
                        action_made = True
    return actions

def get_uniform_direction_action(renderer: Renderer, game_state, player_id):
    """
    A simple input mode where the player chooses one direction for all their units.
    """
    print("Uniform direction actions")

    direction = None
    while not direction:
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

    actions = {}
    for y, row in enumerate(game_state.map):
        for x, tile in enumerate(row):
            if tile.owner and tile.owner.id == player_id:
                coord_str = f"{x},{y}"
                actions[coord_str] = direction
    return actions

def get_human_actions(renderer: Renderer, game_state, player_id, mode):
    """
    Asks the player to choose an input mode and returns the actions accordingly.
    """
    print("start get actions")
    # Default to detailed mode if only a few tiles
    num_tiles = sum(1 for r in game_state.map for t in r if t.owner and t.owner.id == player_id)
    if num_tiles < 5:
        return get_detailed_actions(renderer, game_state, player_id)

    if mode == 'detailed':
        return get_detailed_actions(renderer, game_state, player_id)
    elif mode == 'uniform':
        return get_uniform_direction_action(renderer, game_state, player_id)
    else:
        print(f"Unknown input mode: {mode}. Defaulting to detailed mode.")
    
    return {} # Should not be reached
