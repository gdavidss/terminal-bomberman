#!/bin/bash

# Install script for Bomberman game
# This script sets up the 'bomberman' command to work from anywhere

GAME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOMBERMAN_SCRIPT="$GAME_DIR/bomberman"

echo "🎮 Bomberman Game Installer"
echo "============================"
echo ""

# Check if bomberman script exists
if [ ! -f "$BOMBERMAN_SCRIPT" ]; then
    echo "❌ Error: bomberman script not found at $BOMBERMAN_SCRIPT"
    exit 1
fi

# Make sure the bomberman script is executable
chmod +x "$BOMBERMAN_SCRIPT"

echo "Choose installation method:"
echo "1) Create symlink in /usr/local/bin (recommended, requires sudo)"
echo "2) Add alias to shell configuration"
echo "3) Add directory to PATH"
echo ""
read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "Creating symlink in /usr/local/bin..."
        sudo ln -sf "$BOMBERMAN_SCRIPT" /usr/local/bin/bomberman
        if [ $? -eq 0 ]; then
            echo "✅ Success! You can now run 'bomberman' from anywhere."
        else
            echo "❌ Failed to create symlink. You may need to run with sudo."
            exit 1
        fi
        ;;
    
    2)
        echo ""
        echo "Setting up shell alias..."
        
        # Detect shell
        if [ -n "$ZSH_VERSION" ]; then
            SHELL_RC="$HOME/.zshrc"
        elif [ -n "$BASH_VERSION" ]; then
            SHELL_RC="$HOME/.bashrc"
        else
            SHELL_RC="$HOME/.bashrc"
        fi
        
        # Check if alias already exists
        if grep -q "alias bomberman=" "$SHELL_RC" 2>/dev/null; then
            echo "⚠️  Alias already exists in $SHELL_RC"
            echo "Updating existing alias..."
            sed -i.bak "/alias bomberman=/d" "$SHELL_RC"
        fi
        
        # Add alias
        echo "" >> "$SHELL_RC"
        echo "# Bomberman game alias" >> "$SHELL_RC"
        echo "alias bomberman='$BOMBERMAN_SCRIPT'" >> "$SHELL_RC"
        
        echo "✅ Alias added to $SHELL_RC"
        echo ""
        echo "To use the command immediately, run:"
        echo "  source $SHELL_RC"
        echo ""
        echo "Or restart your terminal."
        ;;
    
    3)
        echo ""
        echo "Adding directory to PATH..."
        
        # Detect shell
        if [ -n "$ZSH_VERSION" ]; then
            SHELL_RC="$HOME/.zshrc"
        elif [ -n "$BASH_VERSION" ]; then
            SHELL_RC="$HOME/.bashrc"
        else
            SHELL_RC="$HOME/.bashrc"
        fi
        
        # Check if PATH addition already exists
        if grep -q "$GAME_DIR" "$SHELL_RC" 2>/dev/null; then
            echo "⚠️  Directory already in PATH"
        else
            echo "" >> "$SHELL_RC"
            echo "# Add Bomberman game to PATH" >> "$SHELL_RC"
            echo "export PATH=\"$GAME_DIR:\$PATH\"" >> "$SHELL_RC"
            
            echo "✅ Directory added to PATH in $SHELL_RC"
        fi
        
        echo ""
        echo "To use the command immediately, run:"
        echo "  source $SHELL_RC"
        echo ""
        echo "Or restart your terminal."
        ;;
    
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "🎮 Installation complete!"
echo ""
echo "Usage:"
echo "  bomberman           # Start the game"
echo "  bomberman --coop    # Start 2-player co-op mode"
echo "  bomberman --size 15 # Start with custom board size"
echo ""
echo "Controls:"
echo "  W/A/S/D - Move player"
echo "  F - Place bomb"
echo "  P - Pause game"
echo ""
echo "Enjoy playing Bomberman! 💣"


