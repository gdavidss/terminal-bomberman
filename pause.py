import os
import sys

# Suppress pygame messages
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'  # Hide pygame welcome message
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pygame")  # Hide pkg_resources warning

import time
import random
from pynput import keyboard
import threading
from collections import deque, defaultdict
from attack import attack_astar
from defend import defend_astar

# Platform-specific imports
if os.name != 'nt':
    import termios
    import tty
    import select

# Music imports
MUSIC_AVAILABLE = False
try:
    from music import start_jungle_music, stop_jungle_music, toggle_music, play_stage_start, play_game_over, play_victory, wait_for_music, init_sound_effects, play_bomb_explosion, pause_music, unpause_music, play_bomberman_scream, play_pause_sound, play_select_sound, toggle_sound_effects, music_enabled, play_i_won_sound, play_nooo_sound, play_bomb_up_sound
    MUSIC_AVAILABLE = True
except ImportError:
    pass
try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import inputs
    JOYSTICK_AVAILABLE = True
except ImportError:
    JOYSTICK_AVAILABLE = False
    # Silently skip - joystick just won't be available

# Joystick globals
gamepad2 = None  # Second controller for player2 (not used in pause.py, kept for consistency)

# Clear screen function
def clear_screen():
    os.system("cls" if os.name =="nt" else "clear")

# Constants
DEFAULT_SIZE = 12  # Increased by 20% from 10
SIZE = DEFAULT_SIZE
PERCENTAGE = 70
FPS = 30
NUM_NPCS = 1  # Number of NPC enemies (1-3)

# Grid values
WALL = 1
PLAYER = -1
PLAYER2 = -2
ENEMY = -3
CIRCLE = 2
FIRE = 3
BOMB_ITEM = 4  # 🔢 Power-up to increase bomb capacity

# Initialize scores
player_score = 0
enemy_score = 0
MATCH_WINNING_SCORE = 5
npc_scores = {}
alive_npcs = []

# Display mode
minimal_mode = False  # Toggle with 'o' to show only grid and scoreboard

# Initialize pause event and game state
pause_event = threading.Event()
pause_event.set()  # Game starts in unpaused state
game_over_event = threading.Event()  # Set when game is over
game_over_event.clear()  # Start not game over
pause_start_time = None  # Track when pause started

class Circle:
    all_fire_cells = defaultdict(int)

    def __init__(self, pos, owner):
        self.pos = pos
        self.radius = 2
        self.timestamp = time.time()
        self.owner = owner

    @staticmethod
    def detonate_circles(circles, grid, active_explosions):
        while circles and time.time() - circles[0].timestamp > 3:  # 3 seconds to detonate
            circle = circles.popleft()  # Pop the oldest circle
            Circle.create_explosion(circle, grid, active_explosions, circles)
            circle.owner.available_circles += 1

    @staticmethod
    def create_explosion(circle, grid, active_explosions, circles):
        x, y = circle.pos
        explosion_cells = []
        
        # Play explosion sound effect
        if MUSIC_AVAILABLE:
            play_bomb_explosion()

        # Horizontal explosion to the right
        for i in range(1, circle.radius+1):
            if x+i < SIZE:
                explosion_cells.append((y, x+i))
                if grid[y][x+i] == WALL:
                    break  # Wall stops explosion but gets destroyed
                elif grid[y][x+i] == CIRCLE:
                    Circle.trigger_bomb(x+i, y, circles, grid)
                    break

        # Horizontal explosion to the left
        for i in range(1, circle.radius+1):
            if x-i >= 0:
                explosion_cells.append((y, x-i))
                if grid[y][x-i] == WALL:
                    break  # Wall stops explosion but gets destroyed
                elif grid[y][x-i] == CIRCLE:
                    Circle.trigger_bomb(x-i, y, circles, grid)
                    break

        # Vertical explosion downward
        for i in range(1, circle.radius+1):
            if y+i < SIZE:
                explosion_cells.append((y+i, x))
                if grid[y+i][x] == WALL:
                    break  # Wall stops explosion but gets destroyed
                elif grid[y+i][x] == CIRCLE:
                    Circle.trigger_bomb(x, y+i, circles, grid)
                    break

        # Vertical explosion upward
        for i in range(1, circle.radius+1):
            if y-i >= 0:
                explosion_cells.append((y-i, x))
                if grid[y-i][x] == WALL:
                    break  # Wall stops explosion but gets destroyed
                elif grid[y-i][x] == CIRCLE:
                    Circle.trigger_bomb(x, y-i, circles, grid)
                    break

        # The initial position where the bomb explodes
        explosion_cells.append((y, x))

        # Set the explosion on the grid and remove walls
        for (cy, cx) in explosion_cells:
            # Check if this was a wall with a bomb item
            if grid[cy][cx] == WALL and hasattr(level_map, 'bomb_items') and (cx, cy) in level_map.bomb_items:
                # Will reveal the bomb item after fire clears
                pass  # The item will be revealed when fire clears
            # Check if there's an exposed bomb item that should be destroyed
            elif grid[cy][cx] == BOMB_ITEM and hasattr(level_map, 'bomb_items') and (cx, cy) in level_map.bomb_items:
                # Fire destroys the exposed bomb item
                level_map.bomb_items.remove((cx, cy))
                print(f"💥 Bomb power-up at ({cx}, {cy}) was destroyed by fire!")
            grid[cy][cx] = FIRE
            Circle.all_fire_cells[(cy, cx)] += 1

        active_explosions.append((time.time(), explosion_cells))

    @staticmethod
    def trigger_bomb(x, y, circles, grid):
        """Trigger a bomb at the specified location."""
        for circle in circles:
            if circle.pos == (x, y):
                circle.timestamp = 0  # Set the timestamp to explode immediately
                break

    @staticmethod
    def update_explosions(active_explosions, grid, player, npcs):
        time_to_reset = 0.5  # Time to reset the cells after the fire phase
        current_time = time.time()
        explosions_to_remove = []
        npcs_died_this_update = False  # Track if any NPC died during this update

        for explosion in active_explosions:
            start_time, cells = explosion
            if current_time - start_time >= time_to_reset:
                for y, x in cells:
                    if Circle.all_fire_cells[(y, x)] == 1:
                        # Check if this position had a bomb item
                        if hasattr(level_map, 'bomb_items') and (x, y) in level_map.bomb_items:
                            grid[y][x] = BOMB_ITEM  # Place the bomb item
                        else:
                            grid[y][x] = 0
                    Circle.all_fire_cells[(y, x)] -= 1
                explosions_to_remove.append(explosion)

            # Check if the player or enemy is in the fire area during fire phase
            for y, x in cells:
                if player.pos == (x, y):
                    print(f"Game Over! {player.icon} was hit by the fire.")
                    show_death_animation(player.pos, grid, death_type="fire")
                    if MUSIC_AVAILABLE:
                        play_nooo_sound()  # Play nooo sound when human player dies
                    game_over('enemy')
                    return
                for npc in npcs:
                    if npc.alive and npc.pos == (x, y):
                        print(f"{npc.icon} was hit by the fire and eliminated!")
                        npc.alive = False
                        grid[y][x] = 0  # Clear the enemy from the grid
                        npcs_died_this_update = True  # Mark that an NPC died

        # Remove the explosions that are done
        for explosion in explosions_to_remove:
            active_explosions.remove(explosion)
        
        # Check if round is over after processing all explosions (only once per update)
        if npcs_died_this_update:
            check_round_over()

class Player:
    num_players = 0

    def __init__(self):
        Player.num_players += 1

        self.pos = (0, 0) if Player.num_players == 1 else (SIZE-1, SIZE-1)
        self.icon = "🔴" if Player.num_players == 1 else "🔵"

        self.available_circles = 1  # Start with only 1 bomb
        self.directions = ['w', 's', 'a', 'd'] if Player.num_players == 1 else ['i', 'k', 'j', 'l']

    def put_circle(self, circles, grid):
        x, y = self.pos
        
        # Check if there's already a bomb at this position
        for bomb in circles:
            if bomb.pos == (x, y):
                return  # Don't place another bomb here

        if self.available_circles > 0:
            circle = Circle(self.pos, owner=self)
            circles.append(circle)
            # For player, we still update grid since player moves away immediately
            grid[y][x] = CIRCLE
            self.available_circles -= 1

    def move_player(self, direction, grid, enemy_pos=None):
        x, y = self.pos
        other_player = PLAYER2 if self.icon == "🔴" else PLAYER

        new_x, new_y = x, y

        # Determine the new position based on the direction
        # Check for WALL and CIRCLE to prevent moving into them
        # Allow moving into FIRE and ENEMY (handled later with collision/death)
        if direction == self.directions[0] and y > 0:
            if grid[y-1][x] not in [WALL, CIRCLE]:
                new_y -= 1
        elif direction == self.directions[1] and y < SIZE-1:
            if grid[y+1][x] not in [WALL, CIRCLE]:
                new_y += 1
        elif direction == self.directions[2] and x > 0:
            if grid[y][x-1] not in [WALL, CIRCLE]:
                new_x -= 1
        elif direction == self.directions[3] and x < SIZE-1:
            if grid[y][x+1] not in [WALL, CIRCLE]:
                new_x += 1

        # If the player moved, update the grid
        if (new_x, new_y) != (x, y):
            # Clear the old position
            if grid[y][x] != other_player:
                # Restore the correct occupant of the old cell (enemy > bomb > empty)
                restored = False
                if 'npcs' in globals():
                    for npc in npcs:
                        if npc.alive and npc.pos == (x, y):
                            grid[y][x] = ENEMY
                            restored = True
                            break
                if not restored:
                    # Check if there was a bomb at the old position
                    for bomb in circles:
                        bomb_x, bomb_y = bomb.pos
                        if (bomb_x, bomb_y) == (x, y):
                            grid[y][x] = CIRCLE
                            restored = True
                            break
                if not restored:
                    grid[y][x] = 0

            # Check if the new position is fire (player loses)
            if grid[new_y][new_x] == FIRE:
                # Move player to the fire position first
                self.pos = (new_x, new_y)
                print(f"Game Over! {self.icon} walked into the fire.")
                show_death_animation(self.pos, grid, death_type="fire")
                if MUSIC_AVAILABLE:
                    play_nooo_sound()  # Play nooo sound when human player dies
                game_over('enemy')  # Exit the game
                return

            # Check if the new position has a bomb item
            if grid[new_y][new_x] == BOMB_ITEM:
                self.available_circles += 1  # Increase bomb capacity
                print(f"{self.icon} collected a bomb power-up! Bombs: {self.available_circles}")
                if MUSIC_AVAILABLE:
                    play_bomb_up_sound()  # Play bomb_up sound when collecting item
                # Remove the item from the bomb_items list
                if hasattr(level_map, 'bomb_items') and (new_x, new_y) in level_map.bomb_items:
                    level_map.bomb_items.remove((new_x, new_y))
            
            # Allow overlap with enemies without death; visual priority stays with first occupant
            
            # Only update position if no collision detected
            self.pos = (new_x, new_y)

            # Update the grid to reflect the player's new position
            # Do not overwrite an enemy tile to preserve first-mover display priority
            if grid[new_y][new_x] != ENEMY:
                grid[new_y][new_x] = PLAYER if self.icon == "🔴" else PLAYER2

class Enemy:
    def __init__(self, icon="🔵", position=None):
        self.pos = position if position else (SIZE-1, SIZE-1)
        self.icon = icon
        self.available_circles = 1  # Start with only 1 bomb
        self.next_moves = []
        self.last_move_time = 0
        self.defend_mode = False
        self.move_interval = 0.2
        self.alive = True  # Track if this NPC is still alive
        self.previous_pos = None  # Track previous position to prevent oscillation
        self.stuck_counter = 0  # Track if enemy is stuck in same area

    def put_circle(self, circles, grid):
        x, y = self.pos
        
        # Check if there's already a bomb at this position
        for bomb in circles:
            if bomb.pos == (x, y):
                return  # Don't place another bomb here

        if self.available_circles > 0:
            circle = Circle(self.pos, owner=self)
            circles.append(circle)

            # Don't overwrite the enemy's position in the grid
            # The bomb exists in the circles list, but the grid still shows the enemy
            # This will be handled when drawing/checking collisions

            self.available_circles -= 1

    def compute_next_moves(self, grid, player_pos):
        # Create a copy of the grid that includes all bombs from circles list
        grid_copy = [row[:] for row in grid]
        for bomb in circles:
            bx, by = bomb.pos
            # Mark bomb positions in the grid copy for pathfinding
            if 0 <= by < len(grid_copy) and 0 <= bx < len(grid_copy[0]):
                if grid_copy[by][bx] not in [WALL, FIRE]:  # Don't overwrite walls or fire
                    grid_copy[by][bx] = CIRCLE
        
        # Check if there are visible bomb items on the grid
        bomb_item_positions = []
        for y in range(len(grid)):
            for x in range(len(grid[0])):
                if grid[y][x] == BOMB_ITEM:
                    bomb_item_positions.append((x, y))
        
        # Priority 1: If there are bomb items and enemy needs them, go get them
        if bomb_item_positions and self.available_circles < 3:
            # Find the closest bomb item
            closest_item = None
            closest_dist = float('inf')
            for item_x, item_y in bomb_item_positions:
                dist = abs(self.pos[0] - item_x) + abs(self.pos[1] - item_y)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_item = (item_x, item_y)
            
            # Try to path to the closest bomb item
            if closest_item:
                path = attack_astar(grid_copy, self.pos, closest_item)
                if path and len(path) > 1:
                    return path[1:]  # Skip the current position
        
        # Priority 2: If in danger, find safety
        if self.defend_mode or self.are_circles_nearby(grid):
            path = defend_astar(grid_copy, self.pos)
            if path and len(path) > 1:
                return path[1:]
            # If defend fails, try attack as fallback
            path = attack_astar(grid_copy, self.pos, player_pos)
            if path and len(path) > 1:
                return path[1:]
        
        # Priority 3: Attack the player
        path = attack_astar(grid_copy, self.pos, player_pos)
        if path and len(path) > 1:
            return path[1:]
        
        # Priority 4: If attack fails, try defend to find ANY valid path
        path = defend_astar(grid_copy, self.pos)
        if path and len(path) > 1:
            return path[1:]
            
        # Priority 5: As absolute last resort, find any adjacent empty cell
        x, y = self.pos
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            new_x, new_y = x + dx, y + dy
            if (0 <= new_x < len(grid) and 0 <= new_y < len(grid) and
                grid[new_y][new_x] not in [WALL, CIRCLE, FIRE] and
                not any(b.pos == (new_x, new_y) for b in circles)):
                return [(new_x, new_y)]
        
        return []  # No moves available

    def move(self, grid, player_pos):
        if not self.alive:  # Don't move if dead
            return
            
        current_time = time.time()
        if current_time - self.last_move_time <= self.move_interval:
            return
        
        # ALWAYS check for bomb threats first - this is highest priority
        bombs_nearby = self.are_circles_nearby(grid)
        if bombs_nearby:
            # Immediately switch to defend mode and recalculate escape path
            self.defend_mode = True
            self.next_moves = []  # Clear any existing path
        
        # Check if we should place a bomb when close to player (only if safe)
        if not bombs_nearby and self.should_place_bomb(grid, player_pos):
            self.put_circle(circles, grid)
            self.defend_mode = True  # Switch to escape mode after placing bomb
            self.next_moves = []  # Recalculate path to escape
            
        # Recalculate path if we don't have one or if bombs are nearby
        if not self.next_moves or bombs_nearby:
            self.next_moves = self.compute_next_moves(grid, player_pos)
            # Remove any moves that would go back to previous position immediately
            if self.previous_pos and self.next_moves and self.next_moves[0] == self.previous_pos:
                self.next_moves.pop(0)

        if not self.next_moves:
            # If no moves, force recalculation with opposite mode
            self.defend_mode = not self.defend_mode
            self.next_moves = self.compute_next_moves(grid, player_pos)
            
            # If still no moves, we're truly stuck - but this shouldn't happen with proper pathfinding
            if not self.next_moves:
                self.stuck_counter += 1
                # After being stuck for a while, forcibly switch strategies
                if self.stuck_counter > 5:
                    # Reset and try opposite strategy
                    self.defend_mode = not self.defend_mode
                    self.stuck_counter = 0
                return

        x, y = self.pos

        new_x, new_y = self.next_moves.pop(0)
        
        # Prevent immediate backtracking
        if self.previous_pos and (new_x, new_y) == self.previous_pos:
            # Try to get the next move in the path instead
            if self.next_moves:
                new_x, new_y = self.next_moves.pop(0)
            else:
                # No other moves available, stay in place
                return

        # Check if the new position is valid
        has_bomb_at_dest = any(bomb.pos == (new_x, new_y) for bomb in circles)
        is_player_at_dest = (player.pos == (new_x, new_y))
        
        if grid[new_y][new_x] == WALL or grid[new_y][new_x] == CIRCLE or grid[new_y][new_x] == FIRE or has_bomb_at_dest or is_player_at_dest:
            # Path is blocked, recalculate
            self.next_moves = self.compute_next_moves(grid, player_pos)
            
            # If still no valid moves after recalculation
            if not self.next_moves:
                self.stuck_counter += 1
                # Switch between attack and defend modes to find a path
                if self.stuck_counter > 3:
                    self.defend_mode = not self.defend_mode
                    self.stuck_counter = 0
                    self.next_moves = self.compute_next_moves(grid, player_pos)
                return
            
            # Try the new path
            new_x, new_y = self.next_moves.pop(0)
            
            # Double-check the new position
            has_bomb_at_dest = any(bomb.pos == (new_x, new_y) for bomb in circles)
            is_player_at_dest = (player.pos == (new_x, new_y))
            
            if grid[new_y][new_x] == WALL or grid[new_y][new_x] == CIRCLE or grid[new_y][new_x] == FIRE or has_bomb_at_dest or is_player_at_dest:
                # Still blocked - skip this turn
                self.next_moves = []
                return

        # Only update the grid and position if the enemy actually moves
        if (new_x, new_y) != (x, y):
            # Double-check player positions one more time
            if grid[new_y][new_x] == PLAYER or grid[new_y][new_x] == PLAYER2:
                # Enemy cannot move to where a player is - recalculate path
                self.next_moves = []
                return
            
            # Clear the current position on the grid
            # Only clear if we're sure it's this enemy's position
            if grid[y][x] == ENEMY:
                # Check if there's a bomb at current position
                has_bomb = False
                for bomb in circles:
                    bomb_x, bomb_y = bomb.pos
                    if (bomb_x, bomb_y) == (x, y):
                        grid[y][x] = CIRCLE  # Restore bomb to grid
                        has_bomb = True
                        break
                if not has_bomb:
                    grid[y][x] = 0  # Clear the cell

            # If the new position is fire, the enemy loses
            if grid[new_y][new_x] == FIRE:
                print(f"Game Over! {self.icon} walked into the fire.")
                game_over('player')  # Player was hit, enemy wins
                return
            
            # Check if the new position has a bomb item
            if grid[new_y][new_x] == BOMB_ITEM:
                self.available_circles += 1  # Increase bomb capacity
                print(f"{self.icon} collected a bomb power-up! Bombs: {self.available_circles}")
                if MUSIC_AVAILABLE:
                    play_bomb_up_sound()  # Play bomb_up sound when collecting item
                # Remove the item from the bomb_items list
                if hasattr(level_map, 'bomb_items') and (new_x, new_y) in level_map.bomb_items:
                    level_map.bomb_items.remove((new_x, new_y))

            # Move the enemy to the new position on the grid
            grid[new_y][new_x] = ENEMY

            # Track previous position to prevent oscillation
            self.previous_pos = (x, y)
            
            # Update the enemy's position
            self.pos = (new_x, new_y)
            
            # Reset stuck counter on successful move
            self.stuck_counter = 0

            # If no moves left, prepare to put a circle (bomb) or switch modes
            if not self.next_moves:
                if self.defend_mode:
                    self.defend_mode = False
                else:
                    self.put_circle(circles, grid)
                    self.defend_mode = True
                self.next_moves = self.compute_next_moves(grid, player_pos)

            self.last_move_time = current_time

    def are_circles_nearby(self, grid):
        x, y = self.pos
        radius = 5  # Increased radius for more aggressive detection
        
        # Check all bombs in the circles list for immediate threat
        for bomb in circles:
            bomb_x, bomb_y = bomb.pos
            
            # Check if we're standing on a bomb
            if bomb.pos == (x, y):
                self.defend_mode = True
                return True
            
            # Check if we're in the explosion path of ANY bomb
            # Bombs have radius 2, meaning they can reach 2 squares away
            explosion_radius = bomb.radius if hasattr(bomb, 'radius') else 2
            
            # Check horizontal alignment
            if y == bomb_y and abs(x - bomb_x) <= explosion_radius:
                # Check if there's a clear path (no walls blocking)
                clear_path = True
                start = min(x, bomb_x)
                end = max(x, bomb_x)
                for i in range(start + 1, end):
                    if grid[y][i] == WALL:
                        clear_path = False
                        break
                if clear_path:
                    self.defend_mode = True
                    return True  # We're in danger from this bomb
            
            # Check vertical alignment
            if x == bomb_x and abs(y - bomb_y) <= explosion_radius:
                # Check if there's a clear path (no walls blocking)
                clear_path = True
                start = min(y, bomb_y)
                end = max(y, bomb_y)
                for i in range(start + 1, end):
                    if grid[i][x] == WALL:
                        clear_path = False
                        break
                if clear_path:
                    self.defend_mode = True
                    return True  # We're in danger from this bomb
        
        # If no bombs were found, return False
        return False
    
    def should_place_bomb(self, grid, player_pos):
        """Determine if enemy should place a bomb based on strategic positioning"""
        if self.available_circles <= 0:
            return False
        
        # Don't place bomb if we're in defend mode (escaping from existing bombs)
        if self.defend_mode:
            return False
        
        # Check if there's already a bomb at our position
        for bomb in circles:
            if bomb.pos == self.pos:
                return False
        
        x, y = self.pos
        px, py = player_pos
        
        # Calculate Manhattan distance to player
        distance = abs(x - px) + abs(y - py)
        
        # Place bomb if we're close to the player (within bomb blast radius + 1)
        bomb_radius = 2  # Default bomb radius
        
        # Check if player would be in danger from a bomb at our position
        player_in_danger = False
        
        # Check horizontal alignment
        if y == py and abs(x - px) <= bomb_radius:
            # Check if there's a clear path between us and player
            clear_path = True
            start = min(x, px)
            end = max(x, px)
            for i in range(start + 1, end):
                if grid[y][i] == WALL:
                    clear_path = False
                    break
            if clear_path:
                player_in_danger = True
        
        # Check vertical alignment
        if x == px and abs(y - py) <= bomb_radius:
            # Check if there's a clear path between us and player
            clear_path = True
            start = min(y, py)
            end = max(y, py)
            for i in range(start + 1, end):
                if grid[i][x] == WALL:
                    clear_path = False
                    break
            if clear_path:
                player_in_danger = True
        
        # Also place bomb if we're adjacent to the player (can trap them)
        if distance == 1:
            player_in_danger = True
        
        # Only place bomb if player would be in danger and we have a chance to escape
        if player_in_danger:
            # Simple check: we should have at least 2 available moves
            escape_routes = 0
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                new_x, new_y = x + dx, y + dy
                if 0 <= new_x < SIZE and 0 <= new_y < SIZE:
                    if grid[new_y][new_x] not in [WALL, CIRCLE]:
                        escape_routes += 1
            
            # Place bomb if we have escape routes
            return escape_routes >= 2
        
        return False

class Map:
    def __init__(self, SIZE, percentage, num_npcs=1):
        # Start with player spawn area (3x3 safe zone)
        forbidden = [(0,0), (0,1), (1,0), (2,0), (0,2), (1,1), (2,1), (1,2)]  # Larger safe zone for player
        
        # Add NPC spawn areas based on num_npcs with MUCH LARGER guaranteed corridors
        if num_npcs >= 1:  # Bottom-right corner
            # 3x3 spawn area
            forbidden.extend([(SIZE-1, SIZE-1), (SIZE-2, SIZE-1), (SIZE-1, SIZE-2),
                            (SIZE-2, SIZE-2), (SIZE-3, SIZE-1), (SIZE-1, SIZE-3)])
            # Wide corridor from spawn (entire bottom row and right column)
            for i in range(max(0, SIZE-6), SIZE):
                forbidden.append((i, SIZE-1))  # Horizontal corridor
                forbidden.append((SIZE-1, i))  # Vertical corridor
            # Additional cross-connection through middle
            if SIZE > 10:
                for i in range(max(0, SIZE//2-1), SIZE):
                    forbidden.append((i, SIZE-2))  # Second horizontal corridor
                    
        if num_npcs >= 2:  # Top-right corner
            # 3x3 spawn area
            forbidden.extend([(SIZE-1, 0), (SIZE-2, 0), (SIZE-1, 1),
                            (SIZE-2, 1), (SIZE-3, 0), (SIZE-1, 2)])
            # Wide corridor from spawn
            for i in range(max(0, SIZE-6), SIZE):
                forbidden.append((i, 0))  # Horizontal corridor
            for i in range(0, min(6, SIZE)):
                forbidden.append((SIZE-1, i))  # Vertical corridor
            # Additional cross-connection
            if SIZE > 10:
                for i in range(max(0, SIZE//2-1), SIZE):
                    forbidden.append((i, 1))  # Second horizontal corridor
                    
        if num_npcs >= 3:  # Bottom-left corner
            # 3x3 spawn area
            forbidden.extend([(0, SIZE-1), (0, SIZE-2), (1, SIZE-1),
                            (1, SIZE-2), (2, SIZE-1), (0, SIZE-3)])
            # Wide corridor from spawn
            for i in range(0, min(6, SIZE)):
                forbidden.append((i, SIZE-1))  # Horizontal corridor
            for i in range(max(0, SIZE-6), SIZE):
                forbidden.append((0, i))  # Vertical corridor
            # Additional cross-connection
            if SIZE > 10:
                for i in range(0, min(SIZE//2+1, SIZE)):
                    forbidden.append((i, SIZE-2))  # Second horizontal corridor
        
        grid = [[0] * SIZE for _ in range(SIZE)]

        # Remove duplicates from forbidden list
        forbidden = list(set(forbidden))
        
        total_cells = SIZE * SIZE - len(forbidden)
        num_ones = int(total_cells * percentage / 100)

        placed_ones = 0
        walls = []
        while placed_ones < num_ones:
            x = random.randint(0, SIZE - 1)
            y = random.randint(0, SIZE - 1)
            if (x, y) not in forbidden and grid[y][x] == 0:
                grid[y][x] = WALL
                walls.append((x, y))
                placed_ones += 1
        
        # Place bomb items in walls near spawn areas (num_players_or_npc * 3 items)
        # In COOP mode (num_npcs=0): 2 players, otherwise: 1 player + num_npcs
        total_players = 2 if num_npcs == 0 else 1 + num_npcs
        num_bomb_items = total_players * 3
        self.bomb_items = []  # Initialize bomb_items list
        if walls and num_bomb_items > 0:
            # Define spawn regions (player + NPCs)
            spawn_regions = [(0, 0)]  # Player spawn
            if num_npcs >= 1:
                spawn_regions.append((SIZE-1, SIZE-1))  # Bottom-right
            if num_npcs >= 2:
                spawn_regions.append((SIZE-1, 0))  # Top-right
            if num_npcs >= 3:
                spawn_regions.append((0, SIZE-1))  # Bottom-left
            
            # Calculate distance from each wall to nearest spawn region
            walls_with_distance = []
            for wall_x, wall_y in walls:
                min_distance = float('inf')
                for spawn_x, spawn_y in spawn_regions:
                    # Manhattan distance
                    distance = abs(wall_x - spawn_x) + abs(wall_y - spawn_y)
                    min_distance = min(min_distance, distance)
                walls_with_distance.append((min_distance, wall_x, wall_y))
            
            # Sort walls by distance to spawn regions (closer first)
            walls_with_distance.sort()
            
            # Categorize walls by distance layers
            first_layer = []  # Distance 2-5 (immediate walls around spawn)
            second_layer = []  # Distance 6-8 (next layer)
            other_walls = []  # Distance 9+ (farther walls)
            
            for dist, x, y in walls_with_distance:
                if dist <= 5:
                    first_layer.append((dist, x, y))
                elif dist <= 8:
                    second_layer.append((dist, x, y))
                else:
                    other_walls.append((dist, x, y))
            
            # Allocate items: 60% to first layer, 30% to second, 10% to others
            # But ensure we use as many first layer walls as possible
            items_first_layer = min(len(first_layer), max((num_bomb_items * 60) // 100, 
                                                         min(num_bomb_items, len(first_layer))))
            remaining = num_bomb_items - items_first_layer
            items_second_layer = min(len(second_layer), max((remaining * 75) // 100,
                                                            min(remaining, len(second_layer))))
            items_other = num_bomb_items - items_first_layer - items_second_layer
            
            selected_walls = []
            
            # Place items in first layer (closest to spawn)
            if items_first_layer > 0 and first_layer:
                selected_first = random.sample(first_layer, min(items_first_layer, len(first_layer)))
                selected_walls.extend(selected_first)
            
            # Place items in second layer
            if items_second_layer > 0 and second_layer:
                selected_second = random.sample(second_layer, min(items_second_layer, len(second_layer)))
                selected_walls.extend(selected_second)
            
            # Place remaining items
            remaining_needed = num_bomb_items - len(selected_walls)
            if remaining_needed > 0:
                # Try other walls first
                if other_walls:
                    selected_other = random.sample(other_walls, min(remaining_needed, len(other_walls)))
                    selected_walls.extend(selected_other)
                    remaining_needed = num_bomb_items - len(selected_walls)
                
                # If still need more, take from any available walls
                if remaining_needed > 0:
                    all_available = first_layer + second_layer + other_walls
                    already_selected = set((x, y) for _, x, y in selected_walls)
                    available = [(d, x, y) for d, x, y in all_available if (x, y) not in already_selected]
                    if available:
                        extra = random.sample(available, min(remaining_needed, len(available)))
                        selected_walls.extend(extra)
            
            # Place bomb items in selected walls
            for _, x, y in selected_walls:
                self.bomb_items.append((x, y))

        grid[0][0] = PLAYER  # represents the player
        
        self.grid = grid

    def draw(self, npc_list=None):
        # Use the passed npc_list or fall back to global variable
        if npc_list is None:
            # Access the module-level npcs variable
            import sys
            current_module = sys.modules[__name__]
            npc_list = getattr(current_module, 'npcs', [])
        
        # Get the circles list to check for bombs
        circles_list = globals().get('circles', [])
        
        # Get player positions to handle overlap correctly
        player1_pos = globals().get('player').pos if 'player' in globals() and globals().get('player') else None
        player2_pos = None  # Co-op not used in pause.py but kept for consistency
        
        print_scoreboard()
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                # First check if there's a bomb at this position (highest priority for display)
                has_bomb = False
                for bomb in circles_list:
                    if bomb.pos == (x, y):
                        print("💣", end="")
                        has_bomb = True
                        break
                
                if not has_bomb:
                    # Check actual positions to handle overlaps correctly
                    if player1_pos == (x, y) and cell != ENEMY:
                        # Player1 is here and not overlapping with enemy (player has display priority)
                        print("🔴", end="")
                    elif player2_pos == (x, y) and cell != ENEMY:
                        # Player2 is here and not overlapping with enemy
                        print("🔵", end="")
                    elif cell == WALL:
                        print("⬛", end="")
                    elif cell == PLAYER:
                        # Only show player icon if actually at this position
                        if player1_pos == (x, y):
                            print("🔴", end="")
                        else:
                            print("⬜", end="")  # Stale player marker, clear it
                    elif cell == PLAYER2:
                        # Only show player2 icon if actually at this position
                        if player2_pos == (x, y):
                            print("🔵", end="")  # Player 2 in co-op mode
                        else:
                            print("⬜", end="")  # Stale player marker, clear it
                    elif cell == ENEMY:
                        # Find which NPC is at this position
                        npc_found = False
                        for npc in npc_list:
                            if npc is not None and npc.pos == (x, y):
                                print(npc.icon, end="")
                                npc_found = True
                                break
                        if not npc_found:
                            print("👾", end="")  # Fallback icon
                    elif cell == CIRCLE:
                        print("💣", end="")
                    elif cell == FIRE:
                        print("🔥", end="")
                    else:
                        print("⬜", end="")
            print()

def check_round_over():
    """Check if the round is over (all NPCs dead or player dead)"""
    global alive_npcs, player_score
    
    # Update alive_npcs list
    alive_npcs = [npc for npc in npcs if npc.alive]
    
    if not alive_npcs:
        # All NPCs are dead, player wins the round
        print("\n🎉 Round Over! Player wins this round!")
        player_score += 1
        
        # Check if player won the match
        if player_score >= MATCH_WINNING_SCORE:
            match_winner('Player')
        else:
            print_scoreboard()
            print("\nPress any button to continue...")
            sys.stdout.flush()
            
            # Wait for any input (keyboard or controller)
            wait_for_any_input()
            
            # Play stage start music for new round
            if MUSIC_AVAILABLE:
                play_stage_start()
                # Schedule battle music to start after stage start finishes
                threading.Timer(3.0, start_jungle_music).start()
            
            reset_game()

def match_winner(winner_name):
    """Handle when someone wins the entire match"""
    global player_score, enemy_score, npc_scores, game_over_event
    
    game_over_event.set()
    
    # Play victory or game over music
    if MUSIC_AVAILABLE:
        if 'Player' in winner_name:
            play_victory()
            play_i_won_sound()  # Play i_won sound when human player wins
        else:
            play_game_over()
    
    os.system("cls" if os.name == "nt" else "clear")
    print("\n" + "="*50)
    print(f"🏆🏆🏆 {winner_name} WINS THE MATCH! 🏆🏆🏆")
    print("="*50)
    
    print("\nFinal Scores:")
    print_scoreboard()
    
    print("\nPlay another match? (y/n): ", end='')
    sys.stdout.flush()
    
    # Get user input
    response = ''
    if os.name == 'nt':
        import msvcrt
        response = msvcrt.getch().decode('utf-8').lower()
    else:
        fd = sys.stdin.fileno()
        old_attrs = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            response = sys.stdin.read(1).lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_attrs)
    
    if response == 'y':
        # Play select sound for choosing to play again
        if MUSIC_AVAILABLE:
            play_select_sound()
        
        # Reset ALL scores for new match
        player_score = 0
        enemy_score = 0
        for icon in npc_scores:
            npc_scores[icon] = 0
        game_over_event.clear()
        
        # Play stage start music then battle music
        if MUSIC_AVAILABLE:
            play_stage_start()
            # Schedule battle music to start after stage start finishes
            threading.Timer(3.0, start_jungle_music).start()
        
        reset_game()
    else:
        print("\nThanks for playing!")
        os._exit(0)

def print_scoreboard():
    # Move the cursor to the top-left corner
    sys.stdout.write('\033[H')
    sys.stdout.flush()
    global player_score, enemy_score, npc_scores
    
    # Display player score
    player_trophies = '🏆' * player_score
    
    # Combine all NPC icons and sum their scores
    npc_icons = ''.join(sorted(npc_scores.keys()))
    total_npc_score = sum(npc_scores.values())
    npc_trophies = '🏆' * total_npc_score
    
    # Print scoreboard
    print(f"🔴 Player: {player_trophies if player_trophies else '0'}  |  {npc_icons}: {npc_trophies if npc_trophies else '0'}")
    print()  # Add newline after scoreboard

def show_death_animation(player_pos, grid, death_type="enemy"):
    """Show death animation based on death type"""
    x, y = player_pos
    
    # Show appropriate death visual based on type
    old_value = grid[y][x]
    if death_type == "fire":
        grid[y][x] = FIRE  # Show fire for fire death
    # For enemy collision, keep the enemy visible or show collision indicator
    # Don't change grid for enemy collision - player and enemy overlap
    
    # Clear and redraw
    os.system("cls" if os.name == "nt" else "clear")
    level_map.draw(npcs)
    
    # Show death message
    print("\n💀 PLAYER DIED! 💀")
    sys.stdout.flush()
    
    # Pause to let player see how they died
    time.sleep(1.5)
    
    # Restore grid (though we're about to reset anyway)
    grid[y][x] = old_value

def game_over(winner):
    """Handle when the player dies - NPCs that are alive win"""
    global game_over_event
    
    # Find which NPCs are still alive
    alive_icons = [npc.icon for npc in npcs if npc.alive]
    
    os.system("cls" if os.name == "nt" else "clear")
    
    # Player died, alive NPCs win a point each
    if alive_icons:
        print(f"\n\n💀 ROUND OVER! Player died! 💀")
        print(f"Surviving enemies win this round: {' '.join(alive_icons)}")
        
        # Check BEFORE incrementing if we would reach the winning score
        for icon in alive_icons:
            if icon in npc_scores:
                # Check if this NPC would win the match
                if npc_scores[icon] + 1 >= MATCH_WINNING_SCORE:
                    npc_scores[icon] += 1  # Add the final point
                    npc_icons = ''.join(sorted(npc_scores.keys()))
                    match_winner(f'{npc_icons} Enemies')
                    return
        
        # If no one won yet, increment scores normally
        for icon in alive_icons:
            if icon in npc_scores:
                npc_scores[icon] += 1
    else:
        print("\n\n🎮 ROUND OVER! Draw! 🎮")
    
    print_scoreboard()
    print("\nPress any button to continue...")
    sys.stdout.flush()
    
    # Wait for any input (keyboard or controller)
    wait_for_any_input()
    
    # Play stage start music for new round
    if MUSIC_AVAILABLE:
        play_stage_start()
        # Schedule battle music to start after stage start finishes
        threading.Timer(3.0, start_jungle_music).start()
    
    reset_game()

def wait_for_any_input():
    """Wait for keyboard or controller input"""
    # Wait for keyboard or any controller button
    if os.name == 'nt':
        import msvcrt
        # Windows: check both keyboard and controller
        while True:
            if msvcrt.kbhit():
                msvcrt.getch()
                return
            # Check for any controller button
            if gamepad and JOYSTICK_AVAILABLE:
                try:
                    events = inputs.get_gamepad()
                    for event in events:
                        if 'BTN' in event.code and event.state == 1:
                            return
                except:
                    pass
            time.sleep(0.05)
    else:
        # Unix/Mac: use select to check stdin and poll controller
        fd = sys.stdin.fileno()
        old_attrs = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            while True:
                rlist, _, _ = select.select([sys.stdin], [], [], 0.05)
                if rlist:
                    sys.stdin.read(1)
                    return
                # Check for any controller button
                if gamepad and JOYSTICK_AVAILABLE:
                    try:
                        events = inputs.get_gamepad()
                        for event in events:
                            if 'BTN' in event.code and event.state == 1:
                                return
                    except:
                        pass
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_attrs)

def pause_game():
    global pause_start_time
    if pause_event.is_set():
        pause_event.clear()
        pause_start_time = time.time()  # Record when we paused
        # Pause the music when game is paused
        if MUSIC_AVAILABLE:
            pause_music()
            play_pause_sound()  # Play pause sound effect
    else:
        # Calculate how long we were paused
        if pause_start_time is not None:
            pause_duration = time.time() - pause_start_time
            # Adjust all bomb timestamps to account for pause
            for bomb in circles:
                bomb.timestamp += pause_duration
            # Also adjust active explosions
            for i, (explosion_time, cells) in enumerate(active_explosions):
                active_explosions[i] = (explosion_time + pause_duration, cells)
            # Adjust enemy movement timers
            for npc in alive_npcs:
                if hasattr(npc, 'last_move_time'):
                    npc.last_move_time += pause_duration
        pause_start_time = None
        pause_event.set()
        # Resume the music when game is unpaused
        if MUSIC_AVAILABLE:
            unpause_music()
            play_pause_sound()  # Play unpause sound effect

def on_press(key):
    # Don't process game commands if game is over
    if game_over_event.is_set():
        return
        
    try:
        if key.char == "p":
            pause_game()
            return  # Skip further processing when pausing/resuming
        elif key.char == 'm' and MUSIC_AVAILABLE:
            # If we're currently unmuted (about to mute), play select sound as confirmation
            was_muted = not music_enabled
            if music_enabled:
                play_select_sound()  # Play this before muting as audio feedback
            toggle_music()
            toggle_sound_effects()
            # If we just unmuted, play select sound as confirmation
            if was_muted:
                # Ensure sound effects are initialized after unmuting
                init_sound_effects()
                import time
                time.sleep(0.1)  # Brief delay to ensure sound system is ready
                play_select_sound()  # Play after unmuting to confirm sounds are back
            return
        elif key.char == 'o':
            # Toggle minimal display mode
            global minimal_mode
            minimal_mode = not minimal_mode
            if MUSIC_AVAILABLE:
                play_select_sound()  # Play sound when toggling display mode
            return
        
        # Only allow game actions when not paused
        if pause_event.is_set():
            if key.char == 'w':
                player.move_player('w', level_map.grid, enemy.pos)
            elif key.char == 's':
                player.move_player('s', level_map.grid, enemy.pos)
            elif key.char == 'a':
                player.move_player('a', level_map.grid, enemy.pos)
            elif key.char == 'd':
                player.move_player('d', level_map.grid, enemy.pos)
            elif key.char == 'f' or key.char == ' ':
                player.put_circle(circles, level_map.grid)

            # Send a backspace character to erase the typed character
            sys.stdout.write('\b')
            sys.stdout.flush()
            # Player 2 controls (if needed)
            """
            elif key.char == 'i':
                enemy.move_player('i', level_map.grid)
            elif key.char == 'k':
                enemy.move_player('k', level_map.grid)
            elif key.char == 'j':
                enemy.move_player('j', level_map.grid)
            elif key.char == 'l':
                enemy.move_player('l', level_map.grid)
            elif key.char == "ç":
                enemy.put_circle(circles, level_map.grid)
            """
    except AttributeError:
        pass

def reset_game():
    global player, enemy, npcs, circles, active_explosions, level_map, SIZE, NUM_NPCS
    
    # Scale map size based on number of NPCs (10% per NPC)
    scaled_size = int(DEFAULT_SIZE * (1 + (NUM_NPCS - 1) * 0.1))
    SIZE = scaled_size

    Player.num_players = 0 # hacky thing so that it works in solo

    player = Player()
    npcs = []
    
    # Create NPCs based on NUM_NPCS
    # Icons for different NPCs
    npc_configs = [
        {"icon": "🔵", "pos": (SIZE-1, SIZE-1)},  # Bottom-right corner
        {"icon": "🟢", "pos": (SIZE-1, 0)},       # Top-right corner  
        {"icon": "🟣", "pos": (0, SIZE-1)}        # Bottom-left corner
    ]
    
    for i in range(min(NUM_NPCS, 3)):
        config = npc_configs[i]
        npc = Enemy(icon=config["icon"], position=config["pos"])
        npcs.append(npc)
        # Initialize score for this NPC if not already in dict
        if config["icon"] not in npc_scores:
            npc_scores[config["icon"]] = 0
    
    # Keep reference to first enemy for backwards compatibility
    enemy = npcs[0] if npcs else None

    circles = deque()

    if Circle.all_fire_cells:
        Circle.all_fire_cells = defaultdict(int)

    active_explosions = []
    level_map = Map(SIZE, percentage=PERCENTAGE, num_npcs=NUM_NPCS)

    # Place NPCs in the grid after map generation
    for npc in npcs:
        if npc is not None and hasattr(npc, 'alive') and npc.alive:
            x, y = npc.pos
            level_map.grid[y][x] = ENEMY

    for npc in npcs:
        npc.compute_next_moves(level_map.grid, player.pos)

def init_joystick():
    """Initialize joystick support using inputs library"""
    global gamepad2
    if not JOYSTICK_AVAILABLE:
        return None
    
    try:
        # Try to get available gamepads
        gamepads = inputs.DeviceManager().gamepads
        if gamepads:
            return gamepads[0]
        else:
            return None
    except Exception as e:
        return None

def handle_joystick():
    """Handle joystick input in a separate thread"""
    global joystick_stop
    
    if not gamepad:
        return
    
    # Movement tracking
    DEADZONE = 0.3
    MOVE_DELAY = 0.15
    last_move_time = {}
    button_states = {}
    
    print("✓ Joystick thread started!")
    while not joystick_stop:
        if not pause_event.is_set():  # Game is paused (event cleared)
            time.sleep(0.01)
            continue
        
        try:
            events = inputs.get_gamepad()
        except Exception as e:
            print(f"Error reading gamepad: {e}")
            time.sleep(0.01)
            continue
        
        current_time = time.time()
        
        for event in events:
            # Skip joystick events if game is over
            if game_over_event.is_set():
                time.sleep(0.01)
                continue
                
            # Handle analog stick movement
            if event.code == 'ABS_X':  # Left stick horizontal
                value = event.state / 32768.0  # Normalize to -1 to 1
                if abs(value) > DEADZONE:
                    if current_time - last_move_time.get('x', 0) > MOVE_DELAY:
                        if value < -DEADZONE:
                            player.move_player('a', level_map.grid, enemy.pos)
                            last_move_time['x'] = current_time
                        elif value > DEADZONE:
                            player.move_player('d', level_map.grid, enemy.pos)
                            last_move_time['x'] = current_time
            
            elif event.code == 'ABS_Y':  # Left stick vertical (inverted)
                value = event.state / 32768.0  # Normalize to -1 to 1
                if abs(value) > DEADZONE:
                    if current_time - last_move_time.get('y', 0) > MOVE_DELAY:
                        if value < -DEADZONE:
                            player.move_player('w', level_map.grid, enemy.pos)
                            last_move_time['y'] = current_time
                        elif value > DEADZONE:
                            player.move_player('s', level_map.grid, enemy.pos)
                            last_move_time['y'] = current_time
            
            # Handle D-Pad
            elif event.code == 'ABS_HAT0X':  # D-Pad horizontal
                if current_time - last_move_time.get('dpad_x', 0) > MOVE_DELAY:
                    if event.state == -1:
                        player.move_player('a', level_map.grid, enemy.pos)
                        last_move_time['dpad_x'] = current_time
                    elif event.state == 1:
                        player.move_player('d', level_map.grid, enemy.pos)
                        last_move_time['dpad_x'] = current_time
            
            elif event.code == 'ABS_HAT0Y':  # D-Pad vertical (inverted)
                if current_time - last_move_time.get('dpad_y', 0) > MOVE_DELAY:
                    if event.state == 1:
                        player.move_player('w', level_map.grid, enemy.pos)
                        last_move_time['dpad_y'] = current_time
                    elif event.state == -1:
                        player.move_player('s', level_map.grid, enemy.pos)
                        last_move_time['dpad_y'] = current_time
            
            # Handle buttons
            elif event.code == 'BTN_SOUTH':  # A button (Xbox) / X button (PS)
                if event.state == 1 and not button_states.get('bomb', False):
                    player.put_circle(circles, level_map.grid)
                    button_states['bomb'] = True
                elif event.state == 0:
                    button_states['bomb'] = False
            
            elif event.code == 'BTN_WEST':  # X button (Xbox) / Square button (PS)
                if event.state == 1 and not button_states.get('omit', False):
                    # Toggle minimal display mode
                    global minimal_mode
                    minimal_mode = not minimal_mode
                    if MUSIC_AVAILABLE:
                        play_select_sound()
                    button_states['omit'] = True
                elif event.state == 0:
                    button_states['omit'] = False
            
            elif event.code == 'BTN_NORTH':  # Y button (Xbox) / Triangle button (PS)
                if event.state == 1 and not button_states.get('mute', False):
                    # Toggle all sounds on/off
                    if MUSIC_AVAILABLE:
                        was_muted = not music_enabled
                        if music_enabled:
                            play_select_sound()
                        toggle_music()
                        toggle_sound_effects()
                        if was_muted:
                            init_sound_effects()
                            import time
                            time.sleep(0.1)
                            play_select_sound()
                    button_states['mute'] = True
                elif event.state == 0:
                    button_states['mute'] = False
            
            elif event.code == 'BTN_START':  # Start/Menu button
                if event.state == 1 and not button_states.get('pause', False):
                    pause_game()
                    button_states['pause'] = True
                    time.sleep(0.5)
                elif event.state == 0:
                    button_states['pause'] = False

if __name__ == "__main__":
    # Initialize joystick
    gamepad = init_joystick()
    joystick_stop = False
    
    # Debug output
    if gamepad:
        print("✓ Joystick initialized successfully!")
    else:
        print("✗ No joystick detected")
    
    # Start keyboard listener
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    
    # Start joystick handler thread if available
    joystick_thread = None
    if gamepad and JOYSTICK_AVAILABLE:
        print("✓ Starting joystick thread...")
        joystick_thread = threading.Thread(target=handle_joystick, daemon=True)
        joystick_thread.start()
    
    reset_game()
    
    # Initialize sound effects and play stage start music then battle music
    if MUSIC_AVAILABLE:
        try:
            init_sound_effects()  # Initialize sound effects
            play_bomberman_scream()  # Play scream sound on game start
            play_stage_start()
            # Start battle music after stage start finishes (approx 3 seconds)
            threading.Timer(3.0, start_jungle_music).start()
        except Exception as e:
            pass  # Could not start music - fail silently

    try:
        while True:
            # Check if game is over
            if game_over_event.is_set():
                time.sleep(0.1)  # Wait a bit before checking again
                continue
            
            # Check if game is paused
            if pause_event.is_set():
                clear_screen()
                Circle.detonate_circles(circles, level_map.grid, active_explosions)

                for npc in npcs:
                    npc.move(level_map.grid, player.pos)

                # Update explosions and draw
                level_map.draw(npcs)
                
                # Display controls unless in minimal mode
                if not minimal_mode:
                    print(f"\nFirst to {MATCH_WINNING_SCORE} wins!")
                    print("\n" + "-" * 40)
                    if gamepad and JOYSTICK_AVAILABLE:
                        print("🎮 [D-Pad]: Move      [A]: Bomb")
                        print("🎮 [Y]: Mute sounds   [X]: Omit details")
                        print("🎮 [Start]: Pause game")
                    else:
                        print("[↑↓←→ or WASD]: Move  [F or SPACE]: Bomb")
                        print("[M]: Mute sounds       [O]: Omit details")
                        print("[P]: Pause game")

                Circle.update_explosions(active_explosions, level_map.grid, player, npcs)
            else:
                # Display paused game with frozen grid
                clear_screen()
                # Show the frozen grid state
                level_map.draw(npcs)
                print("\n⏸️  GAME PAUSED - Press 'p' to resume")
                
                # Display controls unless in minimal mode
                if not minimal_mode:
                    print("\n" + "-" * 40)
                    if gamepad and JOYSTICK_AVAILABLE:
                        print("🎮 [D-Pad]: Move      [A]: Bomb")
                        print("🎮 [Y]: Mute sounds   [X]: Omit details")
                        print("🎮 [Start]: Resume game")
                    else:
                        print("[↑↓←→ or WASD]: Move  [F or SPACE]: Bomb")
                        print("[M]: Mute sounds       [O]: Omit details")
                        print("[P]: Resume game")
                
                time.sleep(0.2)  # Longer sleep when paused to reduce flicker
                continue

            time.sleep(1/FPS)
    except KeyboardInterrupt:
        joystick_stop = True
        if MUSIC_AVAILABLE:
            stop_jungle_music()
        print("\nGame ended.")

