import pygame

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Grid dimensions
GRID_WIDTH = 100 # Increased size
GRID_HEIGHT = 100 # Increased size
CELL_SIZE = 6  # Drastically reduced to fit (approx 100*6=600 pixels)
GRID_PIXEL_WIDTH = GRID_WIDTH * CELL_SIZE
GRID_PIXEL_HEIGHT = GRID_HEIGHT * CELL_SIZE

# --- Zone Definitions ---
START_ZONE_WIDTH = 15 # Increased size
GOAL_COLUMN = GRID_WIDTH - 1 # Last column is the goal

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0) # Start Zone hint
BLUE = (0, 0, 255)   # Goal Zone tile
GRAY = (128, 128, 128) # Barrier tile
DARK_GRAY = (40, 40, 40) # Empty/Dead cell BG
LIGHT_GRAY = (70, 70, 70) # Empty tile border
YELLOW = (255, 255, 0) # Persistent cell color

# Game Phases
SETUP_PHASE = 0
SIMULATION_PHASE = 1
GAME_OVER_PHASE = 2
CRAFTING_PHASE = 3 # New phase for pattern editor

# Simulation settings
NUM_TURNS = 200

# --- Craft Box Settings ---
CRAFT_BOX_SIZES = [(5, 5), (10, 10), (10, 20), (25, 25)]
DEFAULT_CRAFT_BOX_SIZE_INDEX = 1 # Default to 10x10
CRAFT_GRID_CELL_SIZE = 20 # Larger cells for easier editing
CRAFT_GRID_BG_COLOR = (30, 30, 30)
CRAFT_UI_AREA_WIDTH = 200 # Width for buttons next to craft grid 