import pygame
from models import GameState
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, CELL_SIZE, GRID_COLOR, BACKGROUND_COLOR,
    CAPITAL_BORDER_COLOR, MAP_WIDTH, MAP_HEIGHT, LARGE_BATTLE_THRESHOLD, BASE_LIFESPAN
)

class Renderer:
    """Handles all the drawing and rendering for the game."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("KingdomGame")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.font = pygame.font.SysFont(None, 24)
        self.ui_font = pygame.font.SysFont(None, 36)
        
        # Calculate grid offset to center it
        self.grid_width = MAP_WIDTH * CELL_SIZE
        self.grid_height = MAP_HEIGHT * CELL_SIZE
        self.offset_x = (SCREEN_WIDTH - self.grid_width) // 2
        self.offset_y = (SCREEN_HEIGHT - self.grid_height) // 2

    def draw(self, game_state: GameState, current_actions: dict = None):
        """Draws the entire game state to the screen."""
        self.screen.fill(BACKGROUND_COLOR)
        self._draw_tiles(game_state)
        self._draw_grid()
        self._draw_armies(game_state)
        if current_actions:
            self._draw_action_arrows(current_actions)
        self._draw_ui(game_state)
        pygame.display.flip()

    def _draw_grid(self):
        """Draws the map grid lines."""
        for x in range(MAP_WIDTH + 1):
            start_pos = (self.offset_x + x * CELL_SIZE, self.offset_y)
            end_pos = (self.offset_x + x * CELL_SIZE, self.offset_y + self.grid_height)
            pygame.draw.line(self.screen, GRID_COLOR, start_pos, end_pos)
        for y in range(MAP_HEIGHT + 1):
            start_pos = (self.offset_x, self.offset_y + y * CELL_SIZE)
            end_pos = (self.offset_x + self.grid_width, self.offset_y + y * CELL_SIZE)
            pygame.draw.line(self.screen, GRID_COLOR, start_pos, end_pos)

    def _draw_tiles(self, game_state: GameState):
        """Draws the colored tiles and capital borders."""
        for y, row in enumerate(game_state.map):
            for x, tile in enumerate(row):
                rect = pygame.Rect(
                    self.offset_x + x * CELL_SIZE,
                    self.offset_y + y * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                )
                if tile.owner:
                    # Color depth based on army age
                    total_armies = tile.get_total_armies()
                    if total_armies > 0:
                        avg_age = sum(age * count for age, count in enumerate(tile.armies)) / total_armies
                        factor = 1 - (avg_age / BASE_LIFESPAN) * 0.6
                        color = tuple(max(0, min(255, int(c * factor))) for c in tile.owner.color)
                        pygame.draw.rect(self.screen, color, rect)
                    else:
                        pygame.draw.rect(self.screen, tile.owner.color, rect)

                if tile.is_capital:
                    pygame.draw.rect(self.screen, CAPITAL_BORDER_COLOR, rect, 3) # 3 is border width
                
                # Highlight large battles
                if tile.last_turn_battle_size > LARGE_BATTLE_THRESHOLD:
                    pygame.draw.rect(self.screen, (255, 0, 0), rect, 2) # Red border for large battles

    def _draw_action_arrows(self, all_actions: dict):
        """Draws arrows on tiles to indicate the planned actions."""
        actions_to_draw = {}
        # The dictionary can be nested {player_id: actions} or flat {coord: dir}.
        # We flatten it to handle both cases.
        first_key = next(iter(all_actions), None)
        if isinstance(first_key, int):
            # Nested dict: {player_id: {coord: dir}}
            for player_actions in all_actions.values():
                actions_to_draw.update(player_actions)
        else:
            # Flat dict: {coord: dir}
            actions_to_draw = all_actions

        for coord_str, direction in actions_to_draw.items():
            if not isinstance(coord_str, str): continue # Skip if key is not a string coordinate
            x, y = map(int, coord_str.split(','))
            center_x = self.offset_x + x * CELL_SIZE + CELL_SIZE // 2
            center_y = self.offset_y + y * CELL_SIZE + CELL_SIZE // 2
            
            if direction == 'stay':
                # Draw a small circle for 'stay'
                pygame.draw.circle(self.screen, (0,0,0), (center_x, center_y), 5)
                continue

            # Points for an arrow triangle
            arrow_length = CELL_SIZE // 4
            arrow_width = CELL_SIZE // 6
            
            if direction == 'up':
                p1 = (center_x, center_y - arrow_length)
                p2 = (center_x - arrow_width, center_y)
                p3 = (center_x + arrow_width, center_y)
            elif direction == 'down':
                p1 = (center_x, center_y + arrow_length)
                p2 = (center_x - arrow_width, center_y)
                p3 = (center_x + arrow_width, center_y)
            elif direction == 'left':
                p1 = (center_x - arrow_length, center_y)
                p2 = (center_x, center_y - arrow_width)
                p3 = (center_x, center_y + arrow_width)
            elif direction == 'right':
                p1 = (center_x + arrow_length, center_y)
                p2 = (center_x, center_y - arrow_width)
                p3 = (center_x, center_y + arrow_width)
            else:
                continue
                
            pygame.draw.polygon(self.screen, (0, 0, 0), [p1, p2, p3]) # Black arrow

    def _draw_armies(self, game_state: GameState):
        """Draws the army counts on each tile."""
        for y, row in enumerate(game_state.map):
            for x, tile in enumerate(row):
                total_armies = tile.get_total_armies()
                if total_armies > 0:
                    text_surface = self.font.render(str(total_armies), True, (0, 0, 0)) # Black text
                    text_rect = text_surface.get_rect(center=(
                        self.offset_x + x * CELL_SIZE + CELL_SIZE // 2,
                        self.offset_y + y * CELL_SIZE + CELL_SIZE // 2
                    ))
                    self.screen.blit(text_surface, text_rect)

    def _draw_ui(self, game_state: GameState):
        """Draws UI elements like the current turn and player stats."""
        # Turn counter
        turn_text = f"Turn: {game_state.current_turn}"
        text_surface = self.ui_font.render(turn_text, True, (0, 0, 0))
        text_rect = text_surface.get_rect(topleft=(10, 10))
        self.screen.blit(text_surface, text_rect)

        # Player stats
        stats_y_start = SCREEN_HEIGHT - 150
        line_height = 25
        
        # Pre-calculate stats to avoid iterating multiple times
        player_stats = []
        for player in game_state.players:
            if not player.is_defeated:
                territory_size = 0
                total_armies = 0
                for row in game_state.map:
                    for tile in row:
                        if tile.owner and tile.owner.id == player.id:
                            territory_size += 1
                            total_armies += tile.get_total_armies()
                player_stats.append({
                    "name": player.name,
                    "color": player.color,
                    "territory": territory_size,
                    "armies": total_armies
                })
        
        # Header
        header_text = "Player | Territory | Armies"
        header_surface = self.font.render(header_text, True, (50, 50, 50))
        header_rect = header_surface.get_rect(topright=(SCREEN_WIDTH - 10, stats_y_start))
        self.screen.blit(header_surface, header_rect)

        # Display stats for each active player
        for i, stats in enumerate(player_stats):
            y_pos = stats_y_start + (i + 1) * line_height
            
            # Player Name
            name_text = f"{stats['name']}"
            name_surface = self.font.render(name_text, True, stats['color'])
            name_rect = name_surface.get_rect(topright=(SCREEN_WIDTH - 130, y_pos))
            self.screen.blit(name_surface, name_rect)

            # Player Stats
            stats_text = f"| {stats['territory']:>9} | {stats['armies']:>6}"
            stats_surface = self.font.render(stats_text, True, (0, 0, 0))
            stats_rect = stats_surface.get_rect(topleft=name_rect.topright)
            self.screen.blit(stats_surface, stats_rect)

    def quit(self):
        """Quits pygame."""
        pygame.quit()

    def highlight_tile(self, x: int, y: int, flip_display: bool = False):
        """Draws a highlight border around a specific tile."""
        rect = pygame.Rect(
            self.offset_x + x * CELL_SIZE,
            self.offset_y + y * CELL_SIZE,
            CELL_SIZE,
            CELL_SIZE
        )
        pygame.draw.rect(self.screen, (255, 255, 0), rect, 4) # Yellow highlight
        if flip_display:
            pygame.display.flip()
