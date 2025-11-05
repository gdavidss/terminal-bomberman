# 💣 Terminal Bomberman

```
🔴⬜⬛⬛⬛
⬜⬛⬜⬛⬛
⬜⬜⬜⬛💣
⬜⬛⬛⬛🔵
⬜⬜⬛⬜⬜
```




## Quick Start

### Run the game
```bash
# After installation (see below)
bomberman

# Or run directly
./bomberman

# Or using Python
python3 terminal.py
```

### Game Modes
```bash
# Single player vs 1 AI enemy
bomberman

# Single player vs multiple AI enemies (1-3)
bomberman --npcs 2  # 2 enemies in different corners
bomberman --npcs 3  # 3 enemies, one in each corner

# 2-player co-op mode (no AI enemies)
bomberman --coop

# Custom board size
bomberman --size 15

# Combine options (multiple enemies with larger board)
bomberman --npcs 3 --size 15

# Start game with all sounds muted
bomberman --mute
```

### Controls
- **W/A/S/D or Arrow Keys** - Move player
- **F or SPACE** - Place bomb
- **P** - Pause game (freezes grid and music)
- **M** - Toggle all sounds on/off (music & effects) 🔇
- **O** - Toggle minimal display mode (omit details)
- **Arrow keys** - Player 2 movement (in co-op mode)
- **/** - Player 2 bomb (in co-op mode)

A terminal-based Bomberman game rendered entirely with emojis! Built with love on a plane ✈️

## Features
- 🎮 Single player vs 1-3 AI enemies
- 👥 2-player co-op mode
- 🤖 Smart NPCs using A* pathfinding with anti-oscillation logic
- 🎯 Strategic AI that actively tries to trap players with bombs
- 💣 Attack & defense modes with smart bomb placement
- 🛤️ Guaranteed corridors ensure enemies can always move from spawn
- 🔢 Power-up system - collect bomb items to increase capacity
- 🎵 Dynamic music system:
  - Stage start jingle when each round begins (including after death)
  - Battle theme during gameplay (battle.mid)
  - Victory fanfare when player wins match (5 trophies)
  - Game over theme when enemies win match (5 trophies)
- 💥 Sound effects:
  - Bomberman scream on game start
  - Bomb explosion sounds (randomly selects large/medium)
  - Pause/unpause sound effects
  - Menu selection sounds
- 🎨 Multiple enemy types with different colors:
  - 🔵 Blue enemy (bottom-right corner)
  - 🟢 Green enemy (top-right corner)
  - 🟣 Purple enemy (bottom-left corner)
- 🏆 Individual scoring for each enemy
- 🎯 Match system - first to 5 wins
- 💀 Elimination mechanics - defeat all enemies to win round
- 🗺️ Dynamic map scaling (10% larger per enemy)
- 🕹️ Joystick/gamepad support
- ⏸️ Enhanced pause (freezes grid, music, and all movement)
- 🎯 Safe player-enemy overlap without instant death
- 🧠 Smart enemy AI that strategically places bombs to trap players
- 🔄 Play again option after match ends

## Installation

### Automatic Installation
```bash
# Run the install script
./install.sh

# Follow the prompts to set up the 'bomberman' command
```

### Manual Installation
```bash
# Make the script executable
chmod +x bomberman

# Add to your shell configuration (~/.zshrc or ~/.bashrc)
echo "alias bomberman='$(pwd)/bomberman'" >> ~/.zshrc
source ~/.zshrc
```

Now you can run `bomberman` from anywhere in your terminal!

## Game Mechanics

### Power-up System
- **Bomb Capacity**: Players and enemies start with only 1 bomb
- **Bomb Items (🔢)**: Hidden in destructible walls (total players/NPCs × 3 items)
- **Smart Spawning**: ~80% of items spawn within immediate reach of spawn points (distance 2-5) for quick early access
- **Collection**: Walk over revealed items to increase bomb capacity
- **Enemy Behavior**: NPCs actively seek bomb items when low on bombs
- **Strategy**: Control power-ups to gain advantage over enemies

### Movement Mechanics
- **Player Movement**: Can move in 4 directions (up, down, left, right)
- **Collision Rules**:
  - Players are blocked by walls and bombs
  - Players CAN safely move over enemy positions (whoever moves first gets display priority)
  - Walking into fire causes instant death
  - Movement is completely blocked when game is paused
- **Enemy AI**: NPCs use advanced strategies
  - A* pathfinding for intelligent navigation
  - Strategic bomb placement when near players (adjacent or aligned)
  - Actively tries to trap players with smart positioning
  - Switches between attack and defense modes dynamically
  - Avoids dangerous areas and ensures escape routes before bombing
  - Anti-oscillation logic prevents getting stuck in loops
  - Guaranteed corridors from spawn areas ensure mobility

### Scoring System
- **Individual NPC Tracking**: Each enemy has their own score (🔵: 🏆, 🟢: 🏆🏆, etc.)
- **Round System**: 
  - Player wins a round by eliminating ALL enemies
  - Surviving enemies win when the player dies
  - Each surviving enemy gets a point when player dies
- **Match System**: First to 5 points wins the match
- **Play Again**: Option to start a new match after someone wins

### AI Enemies
- **Multiple NPCs**: Support for 1-3 enemy NPCs, each spawning in different corners
- **Dynamic difficulty**: More enemies = larger map (10% increase per enemy)
- **Smart pathfinding**: NPCs use A* algorithm with two modes:
  - **Attack mode**: Actively pursues the player and strategically places bombs
  - **Defense mode**: Avoids dangerous paths by simulating explosion patterns
- **Elimination**: Enemies can be eliminated individually, game continues until all are gone

### Command Line Options
- `--npcs [1-3]`: Number of enemy NPCs (default: 1)
- `--coop`: Enable 2-player cooperative mode (disables NPCs)
- `--size [N]`: Set base board size (default: 12, scales with NPCs)
- `--mute`: Start game with all sounds muted

### macOS: Grant permissions for keyboard input (Accessibility)

On macOS, the game uses `pynput` to listen to keyboard events. macOS requires explicit permission for apps to monitor input. If you see a message like:

```
This process is not trusted! Input event monitoring will not be possible until it is added to accessibility clients.
```

Grant permission as follows:

1. Open System Settings → Privacy & Security.
2. Scroll to Accessibility.
3. Click the + button and add your Terminal app (or the app you use to run Python, e.g., iTerm).
4. Ensure the toggle is enabled for that app.

If you still have issues, also add Terminal/iTerm under Privacy & Security → Input Monitoring.

Then restart Terminal/iTerm and run the game again.

