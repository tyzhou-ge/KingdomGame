import pygame
from models import GameState
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, CELL_SIZE, GRID_COLOR, BACKGROUND_COLOR,
    CAPITAL_BORDER_COLOR, MAP_WIDTH, MAP_HEIGHT
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

    def draw(self, game_state: GameState):
        """Draws the entire game state to the screen."""
        self.screen.fill(BACKGROUND_COLOR)
        self._draw_tiles(game_state)
        self._draw_grid()
        self._draw_armies(game_state)
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
                    pygame.draw.rect(self.screen, tile.owner.color, rect)
                
                if tile.is_capital:
                    pygame.draw.rect(self.screen, CAPITAL_BORDER_COLOR, rect, 3) # 3 is border width

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
        """Draws UI elements like the current turn."""
        turn_text = f"Turn: {game_state.current_turn}"
        text_surface = self.ui_font.render(turn_text, True, (0, 0, 0))
        text_rect = text_surface.get_rect(topleft=(10, 10))
        self.screen.blit(text_surface, text_rect)

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
