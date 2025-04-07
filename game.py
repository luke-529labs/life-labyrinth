import pygame
import constants
from grid import Grid
import copy
from collections import deque # Needed for persistence spread (BFS)

class Game:
    def __init__(self):
        self.grid = Grid(constants.GRID_WIDTH, constants.GRID_HEIGHT)
        self.phase = constants.SETUP_PHASE
        self.turn = 0
        self.max_turns = constants.NUM_TURNS
        self.blocks_placed = 0
        self.max_blocks = 10 # Allow more blocks for zone placement
        self.outcome_message = "" # Stores win/loss message
        self._setup_level() # Temp level setup

    def reset_level(self):
        """Resets the game state to the beginning of the current level."""
        self.grid = Grid(constants.GRID_WIDTH, constants.GRID_HEIGHT) # Recreate grid
        self.phase = constants.SETUP_PHASE
        self.turn = 0
        self.blocks_placed = 0
        self.outcome_message = ""
        self._setup_level() # Re-apply barriers etc.
        print("Level Reset.")

    def _setup_level(self):
        # Example level setup: Only barriers now, start/goal are zones
        barriers = [
            [7, 5], [8, 5], [9, 5],
            [7, 6], [8, 6], [9, 6],
            [constants.GOAL_COLUMN - 2, 10], # Example barrier near goal
        ]
        for bx, by in barriers:
            self.grid.set_tile_type(bx, by, "barrier")

    def handle_input(self, event):
        if self.phase == constants.SETUP_PHASE and event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                mouse_x, mouse_y = event.pos
                # Ensure click is within grid bounds
                if 0 <= mouse_x < constants.GRID_PIXEL_WIDTH and 0 <= mouse_y < constants.GRID_PIXEL_HEIGHT:
                    grid_x = mouse_x // constants.CELL_SIZE
                    grid_y = mouse_y // constants.CELL_SIZE

                    # Placement logic now entirely handled by grid.place_live_cell
                    if self.blocks_placed < self.max_blocks:
                        if self.grid.place_live_cell(grid_x, grid_y):
                            self.blocks_placed += 1
                        else:
                            print("Cannot place block here (outside start zone, barrier, or goal).")
                    else:
                        print(f"Maximum blocks ({self.max_blocks}) placed.")
                else:
                    # Handle clicks outside the grid (e.g., button clicks)
                    if self.check_start_button_click(event.pos):
                        return # Button click handled

        elif self.phase == constants.GAME_OVER_PHASE and event.type == pygame.MOUSEBUTTONDOWN:
             # Allow clicking anywhere to restart after game over
             self.reset_level()

    def update(self):
        if self.phase == constants.SIMULATION_PHASE:
            if self.turn < self.max_turns:
                live_cell_exists, state_changed = self._step_simulation()
                self.turn += 1

                # Check for win condition (set within _step_simulation)
                # The win flag (`self.outcome_message`) is set when a cell becomes persistent in the goal zone

                # --- Check for Loss Conditions (Order matters) ---
                # 1. No live cells left?
                if not live_cell_exists and not self.outcome_message:
                    print(f"Simulation stopped early at turn {self.turn}. All cells died.")
                    self.outcome_message = "Game Over - All Cells Died!"
                    self.phase = constants.GAME_OVER_PHASE
                # 2. Grid became static (stalemate) and not already won?
                elif not state_changed and not self.outcome_message:
                    print(f"Simulation stopped early at turn {self.turn}. Stalemate reached.")
                    self.outcome_message = "Game Over - Stalemate!"
                    self.phase = constants.GAME_OVER_PHASE

            else:
                 # Max turns reached, check final win condition if not already won
                 if not self.outcome_message:
                     won_at_end = self._check_final_win_condition()
                     if won_at_end:
                         self.outcome_message = "You Win!"
                         print(f"Win condition met at end of simulation.")
                     else:
                        self.outcome_message = "Game Over - Max Turns Reached!"
                        print(f"Simulation finished after {self.max_turns} turns. No win.")
                 self.phase = constants.GAME_OVER_PHASE

    def _spread_persistence(self, start_nodes):
        """Spreads the persistent state to adjacent live cells using BFS."""
        queue = deque(start_nodes)
        visited = set(start_nodes)

        while queue:
            x, y = queue.popleft()

            for i in range(-1, 2):
                for j in range(-1, 2):
                    if i == 0 and j == 0:
                        continue
                    nx, ny = x + i, y + j
                    neighbor_tile = self.grid.get_tile(nx, ny)

                    if neighbor_tile and (nx, ny) not in visited:
                        if neighbor_tile.is_live and not neighbor_tile.is_persistent:
                            neighbor_tile.is_persistent = True
                            visited.add((nx, ny))
                            queue.append((nx, ny))

    def _step_simulation(self):
        """Processes one turn. Returns tuple: (live_cell_exists, state_changed)."""
        next_grid_state = copy.deepcopy(self.grid.tiles)
        newly_persistent = []
        live_cell_found_in_step = False
        state_changed_in_step = False # Track if any non-persistent cell changes state

        for x in range(constants.GRID_WIDTH):
            for y in range(constants.GRID_HEIGHT):
                current_tile = self.grid.get_tile(x, y)
                next_tile_state = next_grid_state[x][y]

                if current_tile.tile_type == "barrier":
                    continue

                if current_tile.is_persistent:
                    next_tile_state.is_live = True # Ensure persistence overrides death
                    live_cell_found_in_step = True
                    continue

                live_neighbors = self.grid.get_live_neighbors(x, y)
                current_state = current_tile.is_live
                next_state = current_state

                # Apply Conway's rules
                if current_state:
                    if live_neighbors < 2 or live_neighbors > 3:
                        next_state = False # Dies
                else:
                    if live_neighbors == 3:
                        next_state = True # Born

                next_tile_state.is_live = next_state

                # --- Track state changes for non-persistent cells ---
                if current_state != next_state:
                    state_changed_in_step = True

                if next_state:
                    live_cell_found_in_step = True

                    # Check for Goal Zone entry & Mark for Persistence
                    if current_tile.is_goal:
                        if not next_tile_state.is_persistent:
                            next_tile_state.is_persistent = True
                            newly_persistent.append((x, y))
                            if not self.outcome_message:
                                self.outcome_message = "You Win!"
                                self.phase = constants.GAME_OVER_PHASE
                            print(f"Goal reached at ({x},{y}) on turn {self.turn + 1}! Win condition met.")

        self.grid.tiles = next_grid_state

        if newly_persistent:
             self._spread_persistence(newly_persistent)
             # Persistence spread itself counts as a state change
             state_changed_in_step = True
             # Ensure live_cell_found is true if persistence activated
             if not live_cell_found_in_step:
                 live_cell_found_in_step = True

        print(f"Turn {self.turn + 1} complete.")
        return (live_cell_found_in_step, state_changed_in_step)

    def _check_final_win_condition(self):
        """Check win condition after simulation ends. Returns True if win."""
        for y in range(constants.GRID_HEIGHT):
            tile = self.grid.get_tile(constants.GOAL_COLUMN, y)
            if tile and tile.is_live:
                return True # Found a live cell, win
        return False # No live cells found in goal column

    def start_simulation(self):
        if self.phase == constants.SETUP_PHASE:
            if self.blocks_placed > 0:
                self.phase = constants.SIMULATION_PHASE
                self.outcome_message = "" # Clear any previous outcome
                print("Starting Simulation Phase...")
            else:
                print("Place at least one block before starting simulation.")

    def draw(self, surface):
        # Adjust view if grid is larger than screen area (basic implementation)
        grid_width_pixels = constants.GRID_WIDTH * constants.CELL_SIZE
        grid_height_pixels = constants.GRID_HEIGHT * constants.CELL_SIZE
        grid_surface = pygame.Surface((grid_width_pixels, grid_height_pixels))

        self.grid.draw(grid_surface)
        surface.blit(grid_surface, (0, 0))

        # --- UI elements --- (Positioned below or to the side)
        ui_y_start = grid_height_pixels + 10
        if ui_y_start > constants.SCREEN_HEIGHT - 80: # Adjusted height check for retry text
             ui_y_start = 10

        font = pygame.font.Font(None, 30)
        font_small = pygame.font.Font(None, 24) # For retry text

        # Phase/Turn Text
        phase_str = ""
        if self.phase == constants.SETUP_PHASE:
            phase_str = "Setup Phase"
        elif self.phase == constants.SIMULATION_PHASE:
             phase_str = f"Simulation Turn: {self.turn}/{self.max_turns}"
        elif self.phase == constants.GAME_OVER_PHASE:
            phase_str = "Simulation Over"
        text_surface = font.render(phase_str, True, constants.WHITE)
        surface.blit(text_surface, (10, ui_y_start))

        # Blocks Placed Text
        blocks_text = f"Blocks Placed: {self.blocks_placed}/{self.max_blocks}"
        blocks_surface = font.render(blocks_text, True, constants.WHITE)
        surface.blit(blocks_surface, (10, ui_y_start + 30))

        # --- Start/Retry Button --- (Position and text changes based on phase)
        button_x = grid_width_pixels + 20
        button_y = 50
        button_visible = True
        if button_x > constants.SCREEN_WIDTH - 170:
            button_x = 10
            button_y = ui_y_start + 60
            if self.phase == constants.GAME_OVER_PHASE: # Avoid overlap with outcome text
                 button_y += 40
                 if ui_y_start == 10: # If UI is already shifted up
                      button_visible = False # Hide button if no space

        if button_visible:
            button_rect = pygame.Rect(button_x, button_y, 150, 50)
            button_color = constants.GRAY # Default
            button_text_str = ""

            if self.phase == constants.SETUP_PHASE:
                button_color = constants.GREEN
                button_text_str = "Start Sim"
            elif self.phase == constants.SIMULATION_PHASE:
                 button_color = constants.DARK_GRAY # Indicate inactive
                 button_text_str = "Running..."
            elif self.phase == constants.GAME_OVER_PHASE:
                 button_color = constants.BLUE # Use blue for Retry
                 button_text_str = "Retry Level"

            pygame.draw.rect(surface, button_color, button_rect)
            button_text = font.render(button_text_str, True, constants.BLACK)
            text_rect = button_text.get_rect(center=button_rect.center)
            surface.blit(button_text, text_rect)

        # --- Outcome Message --- (Displayed only in GAME_OVER_PHASE)
        if self.phase == constants.GAME_OVER_PHASE and self.outcome_message:
            result_color = constants.GREEN if "Win" in self.outcome_message else constants.RED
            result_surface = font.render(self.outcome_message, True, result_color, constants.BLACK)
            result_rect = result_surface.get_rect(center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2))
            surface.blit(result_surface, result_rect)

            # Add "Click to retry" text
            retry_text_surface = font_small.render("Click anywhere to retry", True, constants.WHITE)
            retry_rect = retry_text_surface.get_rect(center=(constants.SCREEN_WIDTH // 2, result_rect.bottom + 20))
            surface.blit(retry_text_surface, retry_rect)


    def check_start_button_click(self, pos):
         # Button logic needs to handle different phases
         if self.phase == constants.SETUP_PHASE or self.phase == constants.GAME_OVER_PHASE:
            grid_width_pixels = constants.GRID_WIDTH * constants.CELL_SIZE
            grid_height_pixels = constants.GRID_HEIGHT * constants.CELL_SIZE
            ui_y_start = grid_height_pixels + 10
            if ui_y_start > constants.SCREEN_HEIGHT - 80: ui_y_start = 10

            button_x = grid_width_pixels + 20
            button_y = 50
            button_visible = True
            if button_x > constants.SCREEN_WIDTH - 170:
                button_x = 10
                button_y = ui_y_start + 60
                if self.phase == constants.GAME_OVER_PHASE:
                     button_y += 40
                     if ui_y_start == 10: button_visible = False

            if button_visible:
                button_rect = pygame.Rect(button_x, button_y, 150, 50)
                if button_rect.collidepoint(pos):
                    if self.phase == constants.SETUP_PHASE:
                        self.start_simulation()
                    elif self.phase == constants.GAME_OVER_PHASE:
                         self.reset_level()
                    return True
         return False 