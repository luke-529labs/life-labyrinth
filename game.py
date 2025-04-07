import pygame
import constants
from grid import Grid
from crafting import CraftBox # Import CraftBox
import copy
from collections import deque # Needed for persistence spread (BFS)

class Game:
    def __init__(self):
        self.grid = Grid(constants.GRID_WIDTH, constants.GRID_HEIGHT)
        self.craft_box = CraftBox() # Initialize CraftBox
        self.saved_patterns = [] # To store saved patterns
        self.mouse_pos = (0, 0) # Store mouse position for drawing pattern preview
        # --- Pattern Selection State ---
        self.selected_pattern_index = None # Index of pattern selected for placement
        self.selected_pattern_rotation = 0 # Degrees: 0, 90, 180, 270

        self.phase = constants.SETUP_PHASE
        self.turn = 0
        self.max_turns = constants.NUM_TURNS
        self.blocks_placed = 0 # Tracks individual blocks placed, maybe less relevant with patterns
        self.max_blocks = 50 # Increased limit, maybe tie to pattern cost later?
        self.outcome_message = ""
        self._setup_level()

    def reset_level(self):
        self.grid = Grid(constants.GRID_WIDTH, constants.GRID_HEIGHT)
        self.craft_box = CraftBox() # Also reset craft box state potentially?
        self.selected_pattern_index = None # Reset selection
        self.selected_pattern_rotation = 0 # Reset rotation
        # self.saved_patterns = [] # Keep saved patterns between resets for now
        self.phase = constants.SETUP_PHASE
        self.turn = 0
        self.blocks_placed = 0
        self.outcome_message = ""
        self._setup_level()
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

    def _rotate_point(self, point, degrees, max_dx, max_dy):
        """Rotates a single relative point (dx, dy) clockwise."""
        dx, dy = point
        if degrees == 90:
            # Rotate 90 deg clockwise: (x, y) -> (y, -x)
            # Adjust relative to new HxW grid: (dy, W-1-dx) -> (dy, max_dx - dx)
            return (dy, max_dx - dx)
        elif degrees == 180:
            # Rotate 180 deg: (x, y) -> (-x, -y)
            # Adjust relative to WxH grid: (W-1-dx, H-1-dy) -> (max_dx - dx, max_dy - dy)
            return (max_dx - dx, max_dy - dy)
        elif degrees == 270:
            # Rotate 270 deg clockwise (90 counter-clockwise): (x, y) -> (-y, x)
            # Adjust relative to new HxW grid: (H-1-dy, dx) -> (max_dy - dy, dx)
            return (max_dy - dy, dx)
        else: # 0 degrees
            return point

    def _rotate_pattern(self, pattern, degrees):
        """Rotates a pattern (list of (dx, dy)) clockwise by degrees (90, 180, 270)."""
        if degrees == 0 or not pattern:
            return pattern

        # Find original pattern bounds (relative to 0,0)
        max_dx = max(p[0] for p in pattern)
        max_dy = max(p[1] for p in pattern)

        rotated_pattern = []
        for point in pattern:
            rotated_pattern.append(self._rotate_point(point, degrees, max_dx, max_dy))

        # DEBUG: Print rotated pattern
        # print(f"DEBUG: Rotated {degrees} deg: {rotated_pattern}")
        return rotated_pattern

    def handle_input(self, event):
        self.mouse_pos = pygame.mouse.get_pos() # Update mouse pos continuously

        # --- Key Down --- (Handle Rotation & Start Sim)
        if event.type == pygame.KEYDOWN:
             # DEBUG: Check if keydown is detected
             # print(f"DEBUG: Keydown detected: {event.key}")
             if event.key == pygame.K_r:
                 # DEBUG: Check state when R is pressed
                 # print(f"DEBUG: R pressed. Phase: {self.phase}, Selected Index: {self.selected_pattern_index}")
                 if self.phase == constants.SETUP_PHASE and self.selected_pattern_index is not None:
                     self.selected_pattern_rotation = (self.selected_pattern_rotation + 90) % 360
                     print(f"Rotated pattern to {self.selected_pattern_rotation} degrees.")
                 else:
                     print("DEBUG: R pressed but conditions not met.")
             # --- Start Simulation with Space --- #
             elif event.key == pygame.K_SPACE:
                  if self.phase == constants.SETUP_PHASE:
                      print("DEBUG: Space pressed in setup phase.")
                      self.start_simulation()

        # --- Mouse Button Down ---
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                pos = event.pos
                # Crafting Phase
                if self.phase == constants.CRAFTING_PHASE:
                    if not self.craft_box.handle_click(pos):
                        self._handle_craft_box_button_clicks(pos)

                # Setup Phase
                elif self.phase == constants.SETUP_PHASE:
                    # 1. Check UI buttons (Start, Craft, Pattern Select)
                    if self._handle_setup_button_clicks(pos):
                        return # UI Button click handled (might select/deselect pattern)

                    # 2. Check Grid Click
                    elif 0 <= pos[0] < constants.GRID_PIXEL_WIDTH and 0 <= pos[1] < constants.GRID_PIXEL_HEIGHT:
                        grid_x = pos[0] // constants.CELL_SIZE
                        grid_y = pos[1] // constants.CELL_SIZE

                        # If a pattern IS selected, try to place it
                        if self.selected_pattern_index is not None:
                            print(f"Attempting to place pattern {self.selected_pattern_index} ({self.selected_pattern_rotation} deg) at grid ({grid_x}, {grid_y})")
                            original_pattern = self.saved_patterns[self.selected_pattern_index]
                            # Apply rotation before placement check
                            pattern_to_place = self._rotate_pattern(original_pattern, self.selected_pattern_rotation)
                            pattern_cost = len(pattern_to_place)

                            # Check block limit
                            if self.blocks_placed + pattern_cost <= self.max_blocks:
                                if self.grid.place_pattern(grid_x, grid_y, pattern_to_place):
                                    print("Pattern placed successfully!")
                                    self.blocks_placed += pattern_cost
                                    self.selected_pattern_index = None # Deselect after placement
                                    self.selected_pattern_rotation = 0 # Reset rotation
                                else:
                                    print("Pattern placement failed (invalid location/overlap).")
                        else:
                            # If NO pattern is selected, place single block
                            if self.blocks_placed < self.max_blocks:
                                if self.grid.place_live_cell(grid_x, grid_y):
                                    self.blocks_placed += 1
                                else: print("Cannot place block here.")
                            else: print(f"Block limit ({self.max_blocks}) reached.")

                    # 3. Click outside grid and buttons (deselect pattern if one is selected)
                    elif self.selected_pattern_index is not None:
                        print("Clicked outside grid, deselecting pattern.")
                        self.selected_pattern_index = None
                        self.selected_pattern_rotation = 0 # Reset rotation
                    else:
                        print("Clicked outside grid/buttons during setup.")

                # Game Over Phase
                elif self.phase == constants.GAME_OVER_PHASE:
                    self.reset_level()

    def _handle_craft_box_button_clicks(self, pos):
        # Placeholder for craft box UI button logic (Save, Exit, Resize)
        exit_btn_rect = pygame.Rect(self.craft_box.x_offset + self.craft_box.grid_pixel_width + 10, self.craft_box.y_offset + 10, 180, 40)
        if exit_btn_rect.collidepoint(pos):
            print("Exiting Craft Box (no save).")
            self.craft_box.deactivate()
            self.phase = constants.SETUP_PHASE
            return True
        save_btn_rect = pygame.Rect(self.craft_box.x_offset + self.craft_box.grid_pixel_width + 10, self.craft_box.y_offset + 60, 180, 40)
        if save_btn_rect.collidepoint(pos):
            pattern = self.craft_box.get_pattern()
            if pattern: # Only save non-empty patterns
                self.saved_patterns.append(pattern)
                print(f"Pattern saved ({len(pattern)} cells). Total patterns: {len(self.saved_patterns)}")
            else:
                print("Cannot save empty pattern.")
            self.craft_box.deactivate()
            self.phase = constants.SETUP_PHASE
            return True
        return False

    def _handle_setup_button_clicks(self, pos):
        # Calculates button positions (same as before)
        grid_width_pixels = constants.GRID_WIDTH * constants.CELL_SIZE
        grid_height_pixels = constants.GRID_HEIGHT * constants.CELL_SIZE
        ui_y_start = grid_height_pixels + 10
        if ui_y_start > constants.SCREEN_HEIGHT - 150: ui_y_start = 10
        button_x = grid_width_pixels + 20
        button_y = 50
        if button_x > constants.SCREEN_WIDTH - 170: button_x = 10 ; button_y = ui_y_start + 30

        # Check Start Sim Button
        start_button_rect = pygame.Rect(button_x, button_y, 150, 50)
        if start_button_rect.collidepoint(pos):
            # Prevent starting if a pattern is selected (must place or deselect first)
            if self.selected_pattern_index is not None:
                print("Place or deselect the current pattern before starting.")
                return False
            self.start_simulation()
            return True

        # Check Craft Pattern Button
        craft_btn_y = start_button_rect.bottom + 10
        craft_button_rect = pygame.Rect(button_x, craft_btn_y, 150, 50)
        if craft_button_rect.collidepoint(pos):
            # Prevent crafting if a pattern is selected
            if self.selected_pattern_index is not None:
                print("Place or deselect the current pattern before crafting.")
                return False
            self.phase = constants.CRAFTING_PHASE
            self.craft_box.activate()
            return True

        # Check Saved Pattern Selection Buttons (Select/Deselect)
        pattern_btn_y_start = craft_button_rect.bottom + 10
        pattern_btn_height = 30
        pattern_btn_width = 150
        for i, pattern in enumerate(self.saved_patterns):
            pattern_btn_rect = pygame.Rect(button_x, pattern_btn_y_start + i * (pattern_btn_height + 5), pattern_btn_width, pattern_btn_height)
            if pattern_btn_rect.collidepoint(pos):
                # Toggle selection
                if self.selected_pattern_index == i:
                    self.selected_pattern_index = None # Deselect if clicking the selected one
                    self.selected_pattern_rotation = 0 # Reset rotation on deselect
                    print(f"Deselected pattern {i}")
                else:
                    self.selected_pattern_index = i # Select
                    self.selected_pattern_rotation = 0 # Reset rotation on select
                    print(f"Selected pattern {i} for placement.")
                return True

        return False

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
            # Disallow starting if pattern selected
            if self.selected_pattern_index is not None:
                print("Place or deselect pattern before starting.")
                return
            if self.blocks_placed > 0 or any(len(p) > 0 for p in self.saved_patterns): # Check blocks_placed too
                self.phase = constants.SIMULATION_PHASE
                self.outcome_message = ""
                print("Starting Simulation Phase...")
            else:
                print("Place at least one block or save a pattern before starting.")

    def draw(self, surface):
        # Get fresh mouse position for this frame's drawing
        current_mouse_pos = pygame.mouse.get_pos()

        # --- Draw Craft Box if active --- #
        if self.phase == constants.CRAFTING_PHASE:
            self.craft_box.draw(surface)
            # Draw Craft Box UI Buttons (Placeholders)
            font = pygame.font.Font(None, 24)
            exit_btn_rect = pygame.Rect(self.craft_box.x_offset + self.craft_box.grid_pixel_width + 10, self.craft_box.y_offset + 10, 180, 40)
            pygame.draw.rect(surface, constants.RED, exit_btn_rect)
            exit_txt = font.render("Exit Crafting", True, constants.BLACK)
            surface.blit(exit_txt, exit_txt.get_rect(center=exit_btn_rect.center))
            save_btn_rect = pygame.Rect(self.craft_box.x_offset + self.craft_box.grid_pixel_width + 10, self.craft_box.y_offset + 60, 180, 40)
            pygame.draw.rect(surface, constants.GREEN, save_btn_rect)
            save_txt = font.render("Save Pattern & Exit", True, constants.BLACK)
            surface.blit(save_txt, save_txt.get_rect(center=save_btn_rect.center))
            return

        # --- Draw Main Game (Setup, Sim, Game Over) --- #
        grid_width_pixels = constants.GRID_WIDTH * constants.CELL_SIZE
        grid_height_pixels = constants.GRID_HEIGHT * constants.CELL_SIZE
        grid_surface = pygame.Surface((grid_width_pixels, grid_height_pixels), pygame.SRCALPHA)
        grid_surface.fill((0,0,0,0))

        self.grid.draw(grid_surface)

        # Draw pattern preview if one is selected
        if self.phase == constants.SETUP_PHASE and self.selected_pattern_index is not None:
            self._draw_pattern_preview(grid_surface, current_mouse_pos)

        surface.blit(grid_surface, (0, 0))

        # UI elements
        ui_y_start = grid_height_pixels + 10
        if ui_y_start > constants.SCREEN_HEIGHT - 150: ui_y_start = 10
        font = pygame.font.Font(None, 30)
        font_small = pygame.font.Font(None, 24)

        # Phase Text
        phase_str = ""
        if self.phase == constants.SETUP_PHASE:
            phase_str = "Setup Phase"
            if self.selected_pattern_index is not None:
                 phase_str += f" - Pattern {self.selected_pattern_index} Selected ({self.selected_pattern_rotation}°)"
        elif self.phase == constants.SIMULATION_PHASE:
             phase_str = f"Simulation Turn: {self.turn}/{self.max_turns}"
        elif self.phase == constants.GAME_OVER_PHASE:
            phase_str = "Simulation Over"
        text_surface = font.render(phase_str, True, constants.WHITE)
        surface.blit(text_surface, (10, ui_y_start))

        # Blocks Placed Text (Shows cost used)
        blocks_text = f"Blocks Cost Used: {self.blocks_placed}/{self.max_blocks}"
        blocks_surface = font.render(blocks_text, True, constants.WHITE)
        surface.blit(blocks_surface, (10, ui_y_start + 30))

        # Button Area Calculations
        button_x = grid_width_pixels + 20
        button_y = 50
        button_visible = True
        if button_x > constants.SCREEN_WIDTH - 170:
            button_x = 10
            button_y = ui_y_start + 60 # Reposition buttons if stacked
            if self.phase == constants.GAME_OVER_PHASE: button_y += 40
            if ui_y_start == 10 and self.phase == constants.GAME_OVER_PHASE: button_visible = False

        # --- Draw Buttons --- #
        if button_visible:
            # Start/Retry Button
            start_button_rect = pygame.Rect(button_x, button_y, 150, 50)
            start_button_color = constants.GRAY
            start_button_text_str = ""
            if self.phase == constants.SETUP_PHASE: start_button_color = constants.GREEN; start_button_text_str = "Start Sim"
            elif self.phase == constants.SIMULATION_PHASE: start_button_color = constants.DARK_GRAY; start_button_text_str = "Running..."
            elif self.phase == constants.GAME_OVER_PHASE: start_button_color = constants.BLUE; start_button_text_str = "Retry Level"
            pygame.draw.rect(surface, start_button_color, start_button_rect)
            start_button_text = font.render(start_button_text_str, True, constants.BLACK)
            surface.blit(start_button_text, start_button_text.get_rect(center=start_button_rect.center))

            # Craft/Pattern Buttons (Only in Setup)
            if self.phase == constants.SETUP_PHASE:
                craft_btn_y = start_button_rect.bottom + 10
                craft_button_rect = pygame.Rect(button_x, craft_btn_y, 150, 50)
                pygame.draw.rect(surface, constants.YELLOW, craft_button_rect)
                craft_text = font.render("Craft Pattern", True, constants.BLACK)
                surface.blit(craft_text, craft_text.get_rect(center=craft_button_rect.center))

                pattern_btn_y_start = craft_button_rect.bottom + 10
                pattern_btn_height = 30
                pattern_btn_width = 150
                for i, pattern in enumerate(self.saved_patterns):
                    pattern_btn_rect = pygame.Rect(button_x, pattern_btn_y_start + i * (pattern_btn_height + 5), pattern_btn_width, pattern_btn_height)
                    is_selected = (self.selected_pattern_index == i)
                    btn_color = constants.GREEN if is_selected else constants.LIGHT_GRAY
                    pygame.draw.rect(surface, btn_color, pattern_btn_rect)
                    # Add rotation display to button text if selected
                    pattern_text_str = f"Pattern {i} ({len(pattern)}c)"
                    if is_selected:
                        pattern_text_str += f" [{self.selected_pattern_rotation}°]"
                    pattern_text = font_small.render(pattern_text_str, True, constants.BLACK)
                    surface.blit(pattern_text, pattern_text.get_rect(center=pattern_btn_rect.center))

        # --- Outcome Message --- #
        if self.phase == constants.GAME_OVER_PHASE and self.outcome_message:
            result_color = constants.GREEN if "Win" in self.outcome_message else constants.RED
            result_surface = font.render(self.outcome_message, True, result_color, constants.BLACK)
            result_rect = result_surface.get_rect(center=(constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2))
            surface.blit(result_surface, result_rect)
            retry_text_surface = font_small.render("Click anywhere to retry", True, constants.WHITE)
            retry_rect = retry_text_surface.get_rect(center=(constants.SCREEN_WIDTH // 2, result_rect.bottom + 20))
            surface.blit(retry_text_surface, retry_rect)

    def _draw_pattern_preview(self, surface, current_mouse_pos):
        """Draws preview of selected pattern (with rotation) based on current mouse pos."""
        if self.selected_pattern_index is None:
            return

        grid_x = current_mouse_pos[0] // constants.CELL_SIZE
        grid_y = current_mouse_pos[1] // constants.CELL_SIZE

        original_pattern = self.saved_patterns[self.selected_pattern_index]
        # Apply rotation for preview
        pattern_to_preview = self._rotate_pattern(original_pattern, self.selected_pattern_rotation)

        # DEBUG: Print preview pattern
        # print(f"DEBUG: Previewing pattern (Rotated {self.selected_pattern_rotation}): {pattern_to_preview}")

        preview_color_valid = (*constants.WHITE, 120) # Semi-transparent white
        preview_color_invalid = (*constants.RED, 100) # Semi-transparent red

        # Check validity before drawing
        is_placement_valid = True
        pattern_cost = len(pattern_to_preview)
        if self.blocks_placed + pattern_cost > self.max_blocks:
             is_placement_valid = False # Check block limit as part of validity
        else:
             for dx, dy in pattern_to_preview:
                 px = grid_x + dx
                 py = grid_y + dy
                 if not (0 <= px < constants.GRID_WIDTH and 0 <= py < constants.GRID_HEIGHT and px < constants.START_ZONE_WIDTH):
                      is_placement_valid = False; break
                 tile = self.grid.get_tile(px, py)
                 if not tile or tile.tile_type != "empty" or tile.is_goal or tile.is_live:
                     is_placement_valid = False; break

        # Draw preview cells
        final_preview_color = preview_color_valid if is_placement_valid else preview_color_invalid
        for dx, dy in pattern_to_preview:
            px = grid_x + dx
            py = grid_y + dy
            if 0 <= px < constants.GRID_WIDTH and 0 <= py < constants.GRID_HEIGHT:
                rect = pygame.Rect(px * constants.CELL_SIZE, py * constants.CELL_SIZE, constants.CELL_SIZE, constants.CELL_SIZE)
                preview_cell_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
                preview_cell_surface.fill(final_preview_color)
                surface.blit(preview_cell_surface, rect.topleft) 