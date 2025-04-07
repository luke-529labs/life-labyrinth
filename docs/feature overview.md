Feature Requirement Document: Life Labyrinth

Project Overview:
Life Labyrinth is a puzzle-strategy game built in Python using Pygame. Inspired by Conway's Game of Life, the player is tasked with placing a limited number of "live cells" (blocks) within a designated Start Zone on a grid. The goal is to ensure that at least one cell reaches the designated Goal Zone on the opposite side of the grid after a fixed number of simulation turns, triggering a persistence mechanic. The game will introduce increasingly complex mechanics such as barriers, logic-modifying zones, and spells that temporarily override local rules. This document outlines the full technical and feature requirements for implementation by an autonomous AI developer.

Technology Stack:

Language: Python 3.10+

Graphics Engine: Pygame

Filesystem: JSON for level and state serialization

Game Structure:

Core Components:

Game Grid

A 2D grid of fixed dimensions (e.g., 20x20).

Each tile can be one of the following:

Empty

Goal Zone Tile (triggers persistence)

Spell Zone (modifies Conway rules locally)

Decay Zone (kills all cells that enter it)

Entities

Live Cell (Block): Can be placed by the user in Setup Phase within the Start Zone.

Persistent Cell: A live cell that has reached the Goal Zone or is connected to one. Ignores standard death rules.

Dead Cell: Appears if conditions of cell birth or survival aren't met.

Phases

Setup Phase: Player places N live cells on empty, non-goal tiles within the defined Start Zone (e.g., the first few columns).

Spell Placement Phase (if applicable): Player can optionally place predefined spell zones with limited range and duration.

Simulation Phase: Runs for a fixed number of turns (e.g., 50-100) or until all cells die.

Simulation runs using Conway's Game of Life logic, modified by tile types and the persistence rule.

Any live cell that occupies a Goal Zone tile at any point during simulation triggers the persistence mechanic and achieves the win condition.

Game Rules Engine:

Standard Conway's Game of Life Rules:

Any live cell with 2 or 3 live neighbors survives.

Any dead cell with exactly 3 live neighbors becomes a live cell.

All other live cells die in the next generation.

Persistence Rule:
  - Activated when a live cell enters any tile designated as part of the Goal Zone (e.g., the last column).
  - Once a cell becomes Persistent, it remains alive indefinitely, ignoring the standard Conway survival/death rules based on neighbors.
  - Persistence spreads: Any live, non-persistent cell that is orthogonally or diagonally adjacent to a Persistent cell also becomes Persistent in the same simulation step. This spread continues outwards from all newly persistent cells until no more adjacent live cells can be converted.

Rule Modifiers (Per Tile):

Rule modifications are checked before applying standard rules.

Zones will have properties that override the default rules for affected cells:

override_survival: Tuple of (min_neighbors, max_neighbors)

override_birth: Int for custom birth threshold (e.g., 2 neighbors instead of 3)

force_kill: Boolean to automatically kill all cells in this zone

time_limited: Duration in turns for which the override remains active

Spell System:

Player is granted limited-use spells per level.

Each spell has:

area: Radius or rectangular zone of effect

duration: Number of simulation turns the effect lasts

effect_type: One of [stay_alive, birth_boost, time_stop, decay_zone]

Spell Examples:

Stay Alive Spell: Prevents death regardless of neighbors in affected zone.

Birth Boost Spell: Cells born with only 2 neighbors.

Time Stop Spell: Freezes simulation in target zone.

Decay Zone: Instantly kills cells each turn within the zone.

Spells are implemented as overlays that modify the rules engine at specific coordinates.

Level Design:
Each level must define the following:

{
  "grid_width": 20,
  "grid_height": 20,
  "num_blocks": 10,
  "num_turns": 100,
  "barriers": [[7, 5], [8, 5], [9, 5]],
  "zones": [
    {
      "type": "decay",
      "coordinates": [[10, 5], [11, 5]],
      "duration": null
    },
    {
      "type": "birth_boost",
      "coordinates": [[12, 5], [13, 5]],
      "duration": 3
    }
  ],
  "spells_available": [
    {
      "type": "stay_alive",
      "max_casts": 1,
      "duration": 3,
      "radius": 2
    }
  ]
}

Victory Conditions:

At least one live cell must reach the Goal Zone during the simulation phase (becoming persistent).

Loss Conditions:
  - All live cells die before any reach the Goal Zone.
  - The maximum number of simulation turns is reached without any cell reaching the Goal Zone.

Optional secondary goals:

Use fewer than N moves.

Finish with at least X cells remaining.

Reach the goal within Y turns.

UI Requirements (Minimalist):

Grid rendering with visual indicators for:

Start Zone (e.g., subtle background highlight)

Goal Zone (e.g., blue background)

Barriers (gray)

Zones (color-coded)

Active cells (white)

Persistent cells (yellow)

Dead cells (dark)

Cell placement via mouse in Setup Phase.

Spell placement via keyboard or GUI selector.

Step button to advance simulation by one turn for debugging.

Retry mechanism after simulation ends (win or loss).

Development Roadmap (MVP Focus):

Implement grid and tile system with metadata

Build standard Conway engine

Add rule-modifying zone logic

Implement setup and simulation phases

Add barrier and zone rendering

Build spell and overlay systems

Create level parser and loader from JSON

Add simple UI and interaction layer (placement + run/retry button)