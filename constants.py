import pygame

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Grid dimensions
GRID_WIDTH = 20
GRID_HEIGHT = 20
CELL_SIZE = 25  # Increased slightly for visibility
GRID_PIXEL_WIDTH = GRID_WIDTH * CELL_SIZE
GRID_PIXEL_HEIGHT = GRID_HEIGHT * CELL_SIZE

# --- Zone Definitions ---
START_ZONE_WIDTH = 3 # Allow placement in first 3 columns (0, 1, 2)
GOAL_COLUMN = GRID_WIDTH - 1 # Last column is the goal

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0) # Added missing color
GREEN = (0, 255, 0) # Start Zone hint
BLUE = (0, 0, 255)   # Goal Zone tile
GRAY = (128, 128, 128) # Barrier tile
DARK_GRAY = (40, 40, 40) # Empty/Dead cell BG
LIGHT_GRAY = (70, 70, 70) # Empty tile border
YELLOW = (255, 255, 0) # Persistent cell color

# Game Phases
SETUP_PHASE = 0
SIMULATION_PHASE = 1
GAME_OVER_PHASE = 2 # Added distinct phase for game over state

# Simulation settings
NUM_TURNS = 100 # Increased turns for potentially longer simulations 