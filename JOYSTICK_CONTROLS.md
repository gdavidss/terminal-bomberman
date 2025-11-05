# Joystick Controls for Bomberman

This game now supports gamepad/joystick input alongside keyboard controls, working perfectly in the terminal!

## Requirements

Install the required dependencies:
```bash
pip install -r requirements.txt
```

The `inputs` library is used for joystick support, which works without requiring a graphical display.

## Controls

### Keyboard Controls (Player 1)
- **W/A/S/D or Arrow Keys**: Move Up/Left/Down/Right
- **F or Space**: Place bomb
- **P**: Pause/Resume game
- **M**: Mute/Unmute all sounds
- **O**: Omit details (minimal display mode)

### Joystick/Gamepad Controls
- **D-Pad**: Move in all directions (recommended)
- **Left Analog Stick**: Move in all directions (alternative)
- **A Button (Xbox) / X Button (PlayStation)**: Place bomb
- **Start/Menu Button**: Pause/Resume game
- **Any Button**: Continue after round/match end

### Multi-Controller Support (COOP Mode)
When running in COOP mode (`--coop`), the game automatically detects and assigns controllers:
- **First Controller**: Controls Player 1 (Red) 🔴
- **Second Controller**: Controls Player 2 (Blue) 🔵

Both controllers use the same button mapping (D-Pad for movement, A/South button for bombs, Start for pause).

## Supported Controllers

The game supports most standard gamepads including:
- Xbox controllers (360, One, Series X/S)
- PlayStation controllers (DualShock 4, DualSense)
- Generic USB gamepads

## Troubleshooting

### No Controller Detected
- Make sure your controller is connected before starting the game
- On Linux, you may need to run with sudo or add your user to the `input` group:
  ```bash
  sudo usermod -a -G input $USER
  ```
  Then logout and login again.

### Controller Not Working on macOS
- The `inputs` library may have limited support on macOS
- Try using a different controller or use keyboard controls

### Controller Not Working on Windows
- Make sure the controller is recognized by Windows
- Check if it appears in Device Manager under "Game Controllers"

## How It Works

The game uses the `inputs` library (with optional pygame fallback) which reads gamepad input directly from the hardware without requiring a display window. This makes it perfect for terminal-based games. The joystick input is handled in a separate thread that runs alongside the keyboard listener, allowing both input methods to work simultaneously.

### Multi-Controller Detection
When the game starts, it automatically detects all connected controllers and displays their button mappings:
```
🎮 Joystick 1 detected: Xbox Controller
📋 Button Mapping:
  ┌─────────────────────────────┐
  │ D-Pad / Left Stick → Move   │
  │ A Button (South)   → Bomb   │
  │ Start / Menu       → Pause  │
  └─────────────────────────────┘

🎮 Joystick 2 detected: PlayStation Controller
  🔵 Assigned to Blue Player (P2) in COOP mode
```

### Controller Input in Menus
Controllers can now be used throughout the entire game experience:
- Navigate menus with D-Pad
- Press any button to continue after rounds
- Use controllers for all game interactions


