import pygame
import constants

class Tile:
    def __init__(self, x, y, tile_type="empty", is_live=False, is_goal=False):
        self.x = x
        self.y = y
        self.tile_type = tile_type # empty, barrier (start/end are now zones)
        self.is_live = is_live
        self.is_goal = is_goal
        self.is_persistent = False # Added for the persistence mechanic
        self.rect = pygame.Rect(x * constants.CELL_SIZE,
                                y * constants.CELL_SIZE,
                                constants.CELL_SIZE, constants.CELL_SIZE)

    def draw(self, surface):
        # Base color (empty/dead)
        base_color = constants.DARK_GRAY
        border_color = constants.LIGHT_GRAY
        border_thickness = 1

        # Modify base/border for zones
        if self.is_goal:
            base_color = constants.BLUE
        elif self.x < constants.START_ZONE_WIDTH and self.tile_type == "empty":
             base_color = (20, 50, 20) # Dark green hint for start zone
        elif self.tile_type == "barrier":
            base_color = constants.GRAY

        pygame.draw.rect(surface, base_color, self.rect)

        # Draw live cell indicator
        if self.is_live:
            inner_color = constants.YELLOW if self.is_persistent else constants.WHITE
            inner_rect = self.rect.inflate(-constants.CELL_SIZE // 4, -constants.CELL_SIZE // 4)
            pygame.draw.rect(surface, inner_color, inner_rect)

        # Draw border unless it's a barrier
        if self.tile_type != "barrier":
            pygame.draw.rect(surface, border_color, self.rect, border_thickness)


class Grid:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # Initialize tiles, mark goal column tiles
        self.tiles = [
            [Tile(x, y, is_goal=(x == constants.GOAL_COLUMN))
             for y in range(height)]
            for x in range(width)
        ]
        # Remove specific start/end tile pos - handled by zones now
        # self.start_tile_pos = None
        # self.end_tile_pos = None

    def set_tile_type(self, x, y, tile_type):
        # Simplified: primarily used for barriers now
        if 0 <= x < self.width and 0 <= y < self.height:
            # Prevent overwriting goal tiles with barriers (optional rule)
            if not self.tiles[x][y].is_goal:
                 self.tiles[x][y].tile_type = tile_type
            # Remove specific start/end tile setting
            # if tile_type == "start":
            #     self.start_tile_pos = (x, y)
            # elif tile_type == "end":
            #     self.end_tile_pos = (x, y)

    def get_tile(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[x][y]
        return None

    def place_live_cell(self, x, y):
        # --- Restrict placement to start zone and non-barrier tiles ---
        if x < constants.START_ZONE_WIDTH:
            tile = self.get_tile(x, y)
            # Can only place on 'empty' tiles (not barriers or goal tiles)
            if tile and tile.tile_type == "empty" and not tile.is_goal:
                tile.is_live = True
                return True
        return False

    def draw(self, surface):
        for x in range(self.width):
            for y in range(self.height):
                self.tiles[x][y].draw(surface)

    def get_live_neighbors(self, x, y):
        count = 0
        for i in range(-1, 2):
            for j in range(-1, 2):
                if i == 0 and j == 0:
                    continue
                nx, ny = x + i, y + j
                neighbor = self.get_tile(nx, ny)
                # Count live neighbors, persistent or not
                if neighbor and neighbor.is_live:
                    count += 1
        return count 