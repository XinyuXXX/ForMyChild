# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Educational game application for Chinese children aged 4-6 to develop math, logical thinking, and creative skills. All UI text and voice feedback is in Chinese.

### Available Games
- **找不同** (Find Differences): Visual observation training
- **数一数** (Counting): Number recognition and memory
- **算一算** (Simple Math): Basic arithmetic operations
- **学音乐** (Learn Music): Music theory fundamentals including:
  - **五线谱** (Staff Reading): Note identification on treble/bass clefs
  - **节奏** (Rhythm): Beat patterns and timing
  - **音程** (Intervals): Musical interval recognition
- **学画画** (Learn Drawing): Configuration-based step-by-step drawing tutorials

## Commands

```bash
# Install dependencies (first time setup)
pip3 install -r requirements.txt

# Run the application
python3 main.py

# Quick start script (creates data directory)
./run.sh

# Create sample drawing configurations
# Note: No download_font.py exists - fonts are auto-detected or use bundled fallbacks
```

## Architecture

### State Management
`main.py` orchestrates four application states:
- `name_input`: First-time user registration
- `menu`: Game selection interface  
- `settings`: Player profile and difficulty customization
- `game`: Active gameplay session

### Core Systems

**GameManager** (`src/core/game_manager.py`)
- Persists player data to `data/progress.json`
- Calculates adaptive difficulty: base level from age + performance adjustments
- Manages per-game difficulty overrides from settings

**BaseGame** (`src/games/base_game.py`)
- Parent class providing window scaling support
- Required methods: `handle_click()`, `update()`, `draw()`, `get_result()`
- Built-in difficulty property and responsive layout helpers

**Audio System** (`src/utils/audio_utils.py`)
- Platform-specific TTS: macOS (`say -v Tingting`), Windows (PowerShell), Linux (`espeak`)
- Single global instance prevents voice overlap
- Always await `is_speaking()` before state transitions

### Drawing Game Architecture

**DrawingAIGame** (`src/games/drawing_ai.py`)
- Uses JSON configuration files for step-by-step drawing tutorials
- Supports multiple stroke types: line, circle, rectangle, polygon, arc
- Difficulty levels 1-10 with appropriate content complexity
- Animated drawing demonstration with voice guidance

**Drawing Configurations** (`assets/drawing_configs/`)
- Level-specific JSON files define drawing objects and steps
- Each drawing includes name, steps with descriptions, and stroke definitions
- Supports various geometric primitives and composite shapes

## Key Implementation Details

### Responsive UI
- All games inherit from `BaseGame` with `scale_value()` and `scale_font_size()` methods
- Window resizing supported via `update_window_size()`
- Chinese fonts auto-detected or fallback to `assets/fonts/`

### Difficulty System  
- Settings screen allows per-game difficulty override (1-10)
- Without override: difficulty = age_in_months / 6 + performance_factor
- Games adjust content complexity, timing, and visual elements based on difficulty

### Drawing Game Configuration Format
```json
{
  "drawings": [
    {
      "name": "太阳",
      "steps": [
        {
          "description": "画一个圆形作为太阳",
          "strokes": [
            {
              "type": "circle",
              "center": [200, 200],
              "radius": 50
            }
          ]
        }
      ]
    }
  ]
}
```

### Game Progress
- Each game tracks: games_played, games_won, current_difficulty, history[]
- 10 rounds per game session
- Wrong answers don't advance round counter
- Coins and stars awarded based on performance

## File Organization

```
src/
├── games/          # Game implementations
├── ui/             # Menu and settings screens  
├── utils/          # Shared utilities (audio, fonts, UI components)
├── core/           # GameManager and progress tracking
└── config.py       # Global constants and colors
```

## Adding New Features

### New Game Type
1. Create `src/games/your_game.py` extending `BaseGame`
2. Add to game instantiation in `main.py` start_game()
3. Add difficulty setting in `enhanced_settings_screen.py`
4. Create menu button in `responsive_main_menu.py`

### New Drawing Tutorial  
1. Create/edit JSON file in `assets/drawing_configs/level_X_drawings.json`
2. Follow the configuration schema with name, steps, and strokes
3. Test with appropriate difficulty level (1-10)

## Platform Notes

- Voice commands vary by OS - test on target platform
- Chinese font rendering requires system fonts or bundled fallbacks  
- Dependencies: pygame>=2.5.0, numpy>=1.23.0
- No git repository initialized in current directory