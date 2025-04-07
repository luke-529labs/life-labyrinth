import pygame
import constants

class CraftBox:
    def __init__(self):
        self.size_index = constants.DEFAULT_CRAFT_BOX_SIZE_INDEX
        self.grid_width, self.grid_height = constants.CRAFT_BOX_SIZES[self.size_index]
        self.cell_size = constants.CRAFT_GRID_CELL_SIZE
        self.grid_state = [[False for _ in range(self.grid_height)] for _ in range(self.grid_width)]
        self.grid_pixel_width = self.grid_width * self.cell_size
        self.grid_pixel_height = self.grid_height * self.cell_size
        # Position - will be centered on screen
        self.x_offset = (constants.SCREEN_WIDTH - self.grid_pixel_width - constants.CRAFT_UI_AREA_WIDTH) // 2
        self.y_offset = (constants.SCREEN_HEIGHT - self.grid_pixel_height) // 2

        self.active = False # Is the craft box currently being shown?
        self.selected_pattern = None # Stores the currently edited pattern for placement

    def activate(self):
        self.active = True
        self._resize_grid(self.size_index) # Reset to default size when activated
        print("Crafting phase activated.")

    def deactivate(self):
        self.active = False
        print("Crafting phase deactivated.")

    def _resize_grid(self, size_index):
        self.size_index = size_index
        self.grid_width, self.grid_height = constants.CRAFT_BOX_SIZES[self.size_index]
        self.grid_state = [[False for _ in range(self.grid_height)] for _ in range(self.grid_width)]
        self.grid_pixel_width = self.grid_width * self.cell_size
        self.grid_pixel_height = self.grid_height * self.cell_size
        self.x_offset = (constants.SCREEN_WIDTH - self.grid_pixel_width - constants.CRAFT_UI_AREA_WIDTH) // 2
        self.y_offset = (constants.SCREEN_HEIGHT - self.grid_pixel_height) // 2
        print(f"Craft box resized to {self.grid_width}x{self.grid_height}")

    def handle_click(self, pos):
        mouse_x, mouse_y = pos
        # Check click on grid
        if (self.x_offset <= mouse_x < self.x_offset + self.grid_pixel_width and
            self.y_offset <= mouse_y < self.y_offset + self.grid_pixel_height):
            grid_x = (mouse_x - self.x_offset) // self.cell_size
            grid_y = (mouse_y - self.y_offset) // self.cell_size
            if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
                self.grid_state[grid_x][grid_y] = not self.grid_state[grid_x][grid_y]
                print(f"Toggled cell ({grid_x}, {grid_y}) to {self.grid_state[grid_x][grid_y]}")
                return True # Click handled
        # TODO: Check click on UI buttons (resize, save, exit)
        return False # Click not handled by grid

    def get_pattern(self):
        """Returns the current pattern as a list of relative (x, y) coordinates of live cells."""
        pattern = []
        for x in range(self.grid_width):
            for y in range(self.grid_height):
                if self.grid_state[x][y]:
                    pattern.append((x, y))
        return pattern

    def draw(self, surface):
        if not self.active:
            return

        # Draw background slightly dimmed (optional)
        # overlay = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
        # overlay.fill((0, 0, 0, 180))
        # surface.blit(overlay, (0, 0))

        # Draw grid background
        grid_bg_rect = pygame.Rect(self.x_offset, self.y_offset, self.grid_pixel_width, self.grid_pixel_height)
        pygame.draw.rect(surface, constants.CRAFT_GRID_BG_COLOR, grid_bg_rect)

        # Draw cells and grid lines
        for x in range(self.grid_width):
            for y in range(self.grid_height):
                rect = pygame.Rect(self.x_offset + x * self.cell_size,
                                   self.y_offset + y * self.cell_size,
                                   self.cell_size, self.cell_size)
                # Draw cell state
                cell_color = constants.WHITE if self.grid_state[x][y] else constants.DARK_GRAY
                pygame.draw.rect(surface, cell_color, rect)
                # Draw grid line
                pygame.draw.rect(surface, constants.LIGHT_GRAY, rect, 1)

        # TODO: Draw UI buttons (resize, save, exit) 