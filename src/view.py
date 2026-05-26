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

    def draw(self, game_state: GameState, current_actions: dict = None, fog_of_war_player_id: int = None):
        """Draws the entire game state to the screen. fog_of_war_player_id: 若指定则隐藏其他玩家的格子深浅和军队数。"""
        self.screen.fill(BACKGROUND_COLOR)
        self._draw_tiles(game_state, fog_of_war_player_id)
        self._draw_grid()
        self._draw_armies(game_state, fog_of_war_player_id)
        if current_actions:
            self._draw_action_arrows(current_actions, game_state)
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

    def _draw_tiles(self, game_state: GameState, fog_of_war_player_id: int = None):
        """Draws the colored tiles and capital borders. 支持战争迷雾。"""
        for y, row in enumerate(game_state.map):
            for x, tile in enumerate(row):
                rect = pygame.Rect(
                    self.offset_x + x * CELL_SIZE,
                    self.offset_y + y * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                )
                if tile.owner:
                    show_detail = (fog_of_war_player_id is None) or (tile.owner.id == fog_of_war_player_id)
                    if show_detail:
                        total_armies = tile.get_total_armies()
                        if total_armies > 0:
                            avg_age = sum(age * count for age, count in enumerate(tile.armies)) / total_armies
                            factor = 1 - (avg_age / BASE_LIFESPAN) * 0.6
                            color = tuple(max(0, min(255, int(c * factor))) for c in tile.owner.color)
                            pygame.draw.rect(self.screen, color, rect)
                        else:
                            pygame.draw.rect(self.screen, tile.owner.color, rect)
                    else:
                        # 只显示领地颜色，不显示深浅
                        pygame.draw.rect(self.screen, tile.owner.color, rect)
                if tile.is_capital:
                    pygame.draw.rect(self.screen, CAPITAL_BORDER_COLOR, rect, 3)
                if tile.last_turn_battle_size > LARGE_BATTLE_THRESHOLD:
                    pygame.draw.rect(self.screen, (255, 0, 0), rect, 2)

    def _draw_action_arrows(self, all_actions: dict, game_state: GameState):
        """Draws arrows on tiles to indicate the planned actions. 箭头颜色与领地色相关。"""
        actions_to_draw = {}
        first_key = next(iter(all_actions), None)
        if isinstance(first_key, int):
            for player_actions in all_actions.values():
                actions_to_draw.update(player_actions)
        else:
            actions_to_draw = all_actions

        for coord_str, direction in actions_to_draw.items():
            if not isinstance(coord_str, str): continue
            x, y = map(int, coord_str.split(','))
            tile = game_state.map[y][x]
            color = (0, 0, 0)
            if tile.owner:
                # 箭头颜色为领地色加深
                base = tile.owner.color
                color = tuple(min(255, int(c * 0.7 + 80)) for c in base)
            center_x = self.offset_x + x * CELL_SIZE + CELL_SIZE // 2
            center_y = self.offset_y + y * CELL_SIZE + CELL_SIZE // 2
            if direction == 'stay':
                pygame.draw.circle(self.screen, color, (center_x, center_y), 5)
                continue
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
            pygame.draw.polygon(self.screen, color, [p1, p2, p3])

    def _draw_armies(self, game_state: GameState, fog_of_war_player_id: int = None):
        """Draws the army counts on each tile. 数字右下角且颜色与领地色相关，战争迷雾支持。"""
        for y, row in enumerate(game_state.map):
            for x, tile in enumerate(row):
                if tile.owner:
                    show_detail = (fog_of_war_player_id is None) or (tile.owner.id == fog_of_war_player_id)
                    total_armies = tile.get_total_armies()
                    if total_armies > 0 and show_detail:
                        # 数字颜色为领地色加深
                        base = tile.owner.color
                        color = tuple(min(255, int(c * 0.7 + 80)) for c in base)
                        text_surface = self.font.render(str(total_armies), True, color)
                        # 右下角
                        text_rect = text_surface.get_rect(bottomright=(
                            self.offset_x + (x + 1) * CELL_SIZE - 4,
                            self.offset_y + (y + 1) * CELL_SIZE - 2
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
