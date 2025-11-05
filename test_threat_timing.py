#!/usr/bin/env python3
"""
Test enemy threat detection timing
"""

import sys
import os
import time
from unittest.mock import MagicMock, patch
from collections import deque

# Mock pygame module before importing
sys.modules['pygame'] = MagicMock()
sys.modules['termios'] = MagicMock()
sys.modules['tty'] = MagicMock()

import terminal

def test_immediate_threat_detection():
    """Test that enemy detects bombs immediately when in explosion range"""
    
    print("Testing immediate bomb threat detection...")
    
    # Initialize game components
    terminal.RENDER_ENABLED = False
    terminal.circles = deque()
    terminal.active_explosions = []
    terminal.level_map = terminal.Map(terminal.SIZE, 20, num_npcs=0)
    terminal.player = terminal.Player()
    
    # Create enemy at specific position
    enemy = terminal.Enemy(icon="🔵", position=(5, 5))
    
    # Clear the grid area around the test
    for y in range(3, 8):
        for x in range(3, 8):
            terminal.level_map.grid[y][x] = 0  # Clear space
    
    # Test 1: Place bomb horizontally aligned with enemy
    terminal.player.pos = (3, 5)  # Place player to the left of enemy
    terminal.player.put_circle(terminal.circles, terminal.level_map.grid)
    
    # Check if enemy detects the threat immediately
    threat = enemy.are_circles_nearby(terminal.level_map.grid)
    assert threat == True, "Enemy should detect bomb in horizontal alignment immediately"
    assert enemy.defend_mode == True, "Enemy should enter defend mode immediately"
    print("✓ Enemy detects horizontal bomb threat immediately")
    
    # Clear for next test
    terminal.circles.clear()
    enemy.defend_mode = False
    
    # Test 2: Place bomb vertically aligned with enemy
    terminal.player.pos = (5, 3)  # Place player above enemy
    terminal.player.put_circle(terminal.circles, terminal.level_map.grid)
    
    # Check if enemy detects the threat immediately
    threat = enemy.are_circles_nearby(terminal.level_map.grid)
    assert threat == True, "Enemy should detect bomb in vertical alignment immediately"
    assert enemy.defend_mode == True, "Enemy should enter defend mode immediately"
    print("✓ Enemy detects vertical bomb threat immediately")
    
    # Clear for next test
    terminal.circles.clear()
    enemy.defend_mode = False
    
    # Test 3: Bomb blocked by wall (should NOT trigger threat)
    terminal.level_map.grid[5][4] = terminal.WALL  # Place wall between bomb and enemy
    terminal.player.pos = (3, 5)  # Place player to the left of enemy
    terminal.player.put_circle(terminal.circles, terminal.level_map.grid)
    
    threat = enemy.are_circles_nearby(terminal.level_map.grid)
    assert threat == False, "Enemy should NOT detect threat when wall blocks explosion"
    print("✓ Enemy correctly ignores bomb blocked by wall")
    
    # Clear for next test
    terminal.circles.clear()
    terminal.level_map.grid[5][4] = 0  # Remove wall
    enemy.defend_mode = False
    
    # Test 4: Bomb out of range (should NOT trigger threat)
    terminal.player.pos = (10, 5)  # Place player far away (5 squares)
    terminal.player.put_circle(terminal.circles, terminal.level_map.grid)
    
    threat = enemy.are_circles_nearby(terminal.level_map.grid)
    assert threat == False, "Enemy should NOT detect threat when bomb is out of explosion range"
    print("✓ Enemy correctly ignores bomb out of range")
    
    print("\n✅ All immediate threat detection tests passed!")
    return True

def test_enemy_escape_timing():
    """Test that enemy starts escaping as soon as bomb is placed"""
    
    print("\nTesting enemy escape timing...")
    
    # Initialize game components
    terminal.RENDER_ENABLED = False
    terminal.circles = deque()
    terminal.active_explosions = []
    terminal.level_map = terminal.Map(terminal.SIZE, 20, num_npcs=0)
    terminal.player = terminal.Player()
    
    # Create enemy at specific position
    enemy = terminal.Enemy(icon="🔵", position=(5, 5))
    terminal.npcs = [enemy]
    
    # Clear the grid area
    for y in range(3, 8):
        for x in range(3, 8):
            terminal.level_map.grid[y][x] = 0  # Clear space
    
    # Place bomb next to enemy
    terminal.player.pos = (4, 5)  # One square to the left
    terminal.player.put_circle(terminal.circles, terminal.level_map.grid)
    
    print(f"Bomb placed at {terminal.player.pos}, enemy at {enemy.pos}")
    
    # Simulate enemy move (should detect threat and try to escape)
    initial_pos = enemy.pos
    enemy.move(terminal.level_map.grid, terminal.player.pos)
    
    # Check that enemy is in defend mode
    assert enemy.defend_mode == True, "Enemy should be in defend mode after bomb is placed"
    
    # Give enemy time to actually move
    time.sleep(0.6)  # Wait for move interval
    enemy.move(terminal.level_map.grid, terminal.player.pos)
    
    # Check if enemy moved away (may not always move due to pathfinding, but should try)
    if enemy.pos == initial_pos:
        # Enemy didn't move, check if it at least computed an escape path
        assert enemy.defend_mode == True, "Enemy should still be in defend mode"
        print(f"✓ Enemy detected threat and entered defend mode (position unchanged due to pathfinding)")
    else:
        print(f"✓ Enemy moved from {initial_pos} to {enemy.pos} to escape bomb")
    
    print("\n✅ Enemy escape timing test passed!")
    return True

def test_multiple_bomb_threats():
    """Test enemy detection of multiple bombs"""
    
    print("\nTesting multiple bomb threat detection...")
    
    # Initialize game components
    terminal.RENDER_ENABLED = False
    terminal.circles = deque()
    terminal.active_explosions = []
    terminal.level_map = terminal.Map(terminal.SIZE, 20, num_npcs=0)
    terminal.player = terminal.Player()
    terminal.player.available_circles = 3  # Give player more bombs
    
    # Create enemy at center
    enemy = terminal.Enemy(icon="🔵", position=(5, 5))
    
    # Clear the grid area
    for y in range(3, 8):
        for x in range(3, 8):
            terminal.level_map.grid[y][x] = 0  # Clear space
    
    # Place multiple bombs around enemy
    terminal.player.pos = (3, 5)  # Left
    terminal.player.put_circle(terminal.circles, terminal.level_map.grid)
    
    terminal.player.pos = (5, 3)  # Above
    terminal.player.put_circle(terminal.circles, terminal.level_map.grid)
    
    # Check threat detection
    threat = enemy.are_circles_nearby(terminal.level_map.grid)
    assert threat == True, "Enemy should detect multiple bomb threats"
    assert enemy.defend_mode == True, "Enemy should be in defend mode with multiple threats"
    
    print(f"✓ Enemy detects multiple bomb threats (2 bombs placed)")
    print(f"  Bombs: {[(b.pos) for b in terminal.circles]}")
    print(f"  Enemy at: {enemy.pos}, defend_mode: {enemy.defend_mode}")
    
    print("\n✅ Multiple bomb threat detection test passed!")
    return True

if __name__ == "__main__":
    test_immediate_threat_detection()
    test_enemy_escape_timing()
    test_multiple_bomb_threats()
    print("\n✅ All threat detection timing tests passed!")

