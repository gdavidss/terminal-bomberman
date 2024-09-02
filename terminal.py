import os
import sys
import time
import random
from pynput import keyboard
import threading
from collections import deque, defaultdict
from attack import attack_astar
from defend import defend_astar

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

        # Horizontal explosion to the right
        for i in range(1, circle.radius+1):
            if x+i < SIZE:
                explosion_cells.append((y, x+i))
                if grid[y][x+i] == WALL:
                    break
                elif grid[y][x+i] == CIRCLE:
                    Circle.trigger_bomb(x+i, y, circles, grid)
                    break
        
        # Horizontal explosion to the left
        for i in range(1, circle.radius+1):
            if x-i >= 0:
                explosion_cells.append((y, x-i))
                if grid[y][x-i] == WALL:
                    break
                elif grid[y][x-i] == CIRCLE:
                    Circle.trigger_bomb(x-i, y, circles, grid)
                    break
        
        # Vertical explosion downward
        for i in range(1, circle.radius+1):
            if y+i < SIZE:
                explosion_cells.append((y+i, x))
                if grid[y+i][x] == WALL:
                    break
                elif grid[y+i][x] == CIRCLE:
                    Circle.trigger_bomb(x, y+i, circles, grid)
                    break
        
        # Vertical explosion upward
        for i in range(1, circle.radius+1):
            if y-i >= 0:
                explosion_cells.append((y-i, x))
                if grid[y-i][x] == WALL:
                    break
                elif grid[y-i][x] == CIRCLE:
                    Circle.trigger_bomb(x, y-i, circles, grid)
                    break
        
        # The initial position where the bomb explodes
        explosion_cells.append((y, x))
        
        # Set the explosion on the grid and remove walls
        for (cy, cx) in explosion_cells:
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

        for explosion in active_explosions:
            start_time, cells = explosion
            if current_time - start_time >= time_to_reset:
                for y, x in cells:
                    if Circle.all_fire_cells[(y, x)] == 1: 
                        grid[y][x] = 0
                    Circle.all_fire_cells[(y, x)] -= 1
                explosions_to_remove.append(explosion)
            
            # Check if the player or enemy is in the fire area during fire phase
            for y, x in cells:
                if player.pos == (x, y):
                    print(f"Game Over! {player.icon} was hit by the fire.")
                    game_over('enemy')
                    return
                for npc in npcs:
                    if npc.pos == (x, y):
                        print(f"Game Over! {npc.icon} was hit by the fire.")
                        game_over('player')
                        return

        # Remove the explosions that are done
        for explosion in explosions_to_remove:
            active_explosions.remove(explosion)

class Player:
    num_players = 0
    
    def __init__(self):
        Player.num_players += 1
        
        self.pos = (0, 0) if Player.num_players == 1 else (SIZE-1, SIZE-1)
        self.icon = "🔴" if Player.num_players == 1 else "🔵"
        
        self.available_circles = 4
        self.directions = ['w', 's', 'a', 'd'] if Player.num_players == 1 else ['i', 'k', 'j', 'l']
        
    def put_circle(self, circles, grid):
        if grid[self.pos[1]][self.pos[0]] == CIRCLE: # don't allow putting 2 bombs on same place
            return
        
        if self.available_circles > 0:
            circle = Circle(self.pos, owner=self)
            circles.append(circle)
            x, y = self.pos
            grid[y][x] = CIRCLE
            self.available_circles -= 1
    
    def move_player(self, direction, grid, enemy_pos):
        x, y = self.pos
        other_player = PLAYER2 if self.icon == "🔴" else PLAYER
        
        new_x, new_y = x, y

        # Determine the new position based on the direction
        if direction == self.directions[0] and y > 0 and grid[y-1][x] != WALL and grid[y-1][x] != CIRCLE:
            new_y -= 1
        elif direction == self.directions[1] and y < SIZE-1 and grid[y+1][x] != WALL and grid[y+1][x] != CIRCLE:
            new_y += 1
        elif direction == self.directions[2] and x > 0 and grid[y][x-1] != WALL and grid[y][x-1] != CIRCLE:
            new_x -= 1
        elif direction == self.directions[3] and x < SIZE-1 and grid[y][x+1] != WALL and grid[y][x+1] != CIRCLE:
            new_x += 1

        # If the player moved, update the grid
        if (new_x, new_y) != (x, y):
            if (x,y) == enemy_pos:
                grid[y][x] = ENEMY
            elif grid[y][x] != other_player:
                grid[y][x] = 0
                
                for bomb in circles:
                    bomb_x, bomb_y = bomb.pos
                    if (bomb_x, bomb_y) == (x, y):
                        grid[y][x] = CIRCLE

            # If the new position is fire, the player loses
            if grid[new_y][new_x] == FIRE:
                print(f"Game Over! {self.icon} walked into the fire.")
                game_over('enemy')  # Exit the game
                return

            # Update the grid to reflect the player's new position
            if grid[new_y][new_x] != other_player:
                grid[new_y][new_x] = PLAYER if self.icon == "🔴" else PLAYER2
            if (new_y, new_x) != enemy_pos:
                grid[new_y][new_x] = PLAYER if self.icon == "🔴" else PLAYER2

            # Update the player's position
            self.pos = (new_x, new_y)

class Enemy:
    def __init__(self, icon="🔵"):
        self.pos = (SIZE-1, SIZE-1)
        self.icon = icon
        self.available_circles = 4
        self.next_moves = []
        self.last_move_time = 0
        self.defend_mode = False
        self.move_interval = 0.2
    
    def put_circle(self, circles, grid):
        if grid[self.pos[1]][self.pos[0]] == CIRCLE: # don't allow putting 2 bombs on same place
            return
        
        if self.available_circles > 0:
            circle = Circle(self.pos, owner=self)
            circles.append(circle)
            
            x, y = self.pos
            grid[y][x] = CIRCLE
            
            self.available_circles -= 1
            
    def compute_next_moves(self, grid, player_pos):
        if self.defend_mode or self.are_circles_nearby(grid):
            path = defend_astar(grid, self.pos)
        else:
            path = attack_astar(grid, self.pos, player_pos)
            
        if path is None or len(path) <= 1:  # No path found or no moves to make
            return []
        return path[1:]  # Skip the current position

    def move(self, grid, player_pos):
        current_time = time.time()
        if current_time - self.last_move_time <= move_interval:
            return
            
        if not self.next_moves or self.are_circles_nearby(grid):
            self.next_moves = self.compute_next_moves(grid, player_pos)
        
        if not self.next_moves or self.are_circles_nearby(grid):
            self.next_moves = self.compute_next_moves(grid, player_pos)
    
        if not self.next_moves:  # If still no moves, just return
            return
        
        x, y = self.pos
        
        new_x, new_y = self.next_moves.pop(0)
        
        # Check if the new position is valid (i.e., not a wall or a circle)
        if grid[new_y][new_x] == WALL or grid[new_y][new_x] == CIRCLE:
            # Recompute the path if the next move is not valid
            self.next_moves = self.compute_next_moves(grid, player_pos)
            if not self.next_moves:
                return
            new_x, new_y = self.next_moves.pop(0)
        
        # Only update the grid and position if the enemy actually moves
        if (new_x, new_y) != (x, y):
            # Clear the current position on the grid if it's not a player or circle
            if grid[y][x] != PLAYER:
                grid[y][x] = 0 #if grid[y][x] != CIRCLE else CIRCLE
                
                for bomb in circles:
                    bomb_x, bomb_y = bomb.pos
                    if (bomb_x, bomb_y) == (x, y):
                        grid[y][x] = CIRCLE
                        
                    
            # If the new position is fire, the enemy loses
            if grid[new_y][new_x] == FIRE:
                print(f"Game Over! {self.icon} walked into the fire.")
                game_over('player')  # Player was hit, enemy wins
                return
            
                
            # Move the enemy to the new position on the grid
            if grid[new_y][new_x] != PLAYER:
                grid[new_y][new_x] = ENEMY
            
            # Update the enemy's position
            self.pos = (new_x, new_y)
            
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
        radius = 4
        
        if grid[y][x] == CIRCLE:
            self.defend_mode = True
            return True
        
        # Check right
        for i in range(1, radius + 1):
            if x + i < SIZE:
                if grid[y][x + i] == CIRCLE:
                    self.defend_mode = True
                    return True
                if grid[y][x + i] == WALL:
                    break  # Stop checking further in this direction if there's a wall

        # Check left
        for i in range(1, radius + 1):
            if x - i >= 0:
                if grid[y][x - i] == CIRCLE:
                    self.defend_mode = True
                    return True
                if grid[y][x - i] == WALL:
                    break

        # Check down
        for i in range(1, radius + 1):
            if y + i < SIZE:
                if grid[y + i][x] == CIRCLE:
                    self.defend_mode = True
                    return True
                if grid[y + i][x] == WALL:
                    break

        # Check up
        for i in range(1, radius + 1):
            if y - i >= 0:
                if grid[y - i][x] == CIRCLE:
                    self.defend_mode = True
                    return True
                if grid[y - i][x] == WALL:
                    break

        # If no bombs were found in any direction, return False
        return False
            
class Map:
    def __init__(self, SIZE, percentage):
        forbidden = [(0,0), (0,1), (1,0), (SIZE-1, SIZE-1), (SIZE-2, SIZE-1), (SIZE-1, SIZE-2), (0, SIZE-1), (0, SIZE-2), (1, SIZE-1)]
        grid = [[0] * SIZE for _ in range(SIZE)]
        
        total_cells = SIZE * SIZE - len(forbidden)
        num_ones = int(total_cells * percentage / 100)

        placed_ones = 0
        while placed_ones < num_ones:
            x = random.randint(0, SIZE - 1)
            y = random.randint(0, SIZE - 1)
            if (x, y) not in forbidden and grid[y][x] == 0:
                grid[y][x] = WALL
                placed_ones += 1
        
        grid[0][0] = PLAYER  # represents the player
        grid[SIZE-1][SIZE-1] = ENEMY  # represents the enemy
        self.grid = grid

    def draw(self):
        print_scoreboard()
        for row in self.grid:
            for cell in row:
                if cell == WALL:
                    print("⬛", end="")
                elif cell == PLAYER:
                    print("🔴", end="")
                elif cell == PLAYER2:
                    print("🔵", end="")
                elif cell == CIRCLE:
                    print("💣", end="")
                elif cell == FIRE:
                    print("🔥", end="")
                else:
                    print("⬜", end="")
            print()

SIZE = 10 

PERCENTAGE = 70
FPS = 30

# Grid values
WALL = 1
PLAYER = -1
ENEMY = PLAYER2 = -2

CIRCLE = 2
FIRE = 3

def update_scores_and_reset(winner):
    global player_score, enemy_score
    if winner == 'player':
        player_score += 1
    elif winner == 'enemy':
        enemy_score += 1
    reset_game()

def print_scoreboard():
    print(f"Scoreboard: Player {player_score} - {enemy_score} Enemy")

def game_over(winner):
    sys.stdout.write('\033[1;1H')
    sys.stdout.write('\033[K')
    sys.stdout.flush()
    
    print(f"Game Over! {winner} wins.")
    sys.stdout.flush()  # Ensure the message is printed immediately
    time.sleep(2)  # Pause to allow the player to see the message
    update_scores_and_reset(winner)
    
def on_press(key):
    try:
        if key.char == "p":
            pause()
        if key.char == 'w':
            player.move_player('w', level_map.grid, enemy.pos)
        elif key.char == 's':
            player.move_player('s', level_map.grid, enemy.pos)
        elif key.char == 'a':
            player.move_player('a', level_map.grid, enemy.pos)
        elif key.char == 'd':
            player.move_player('d', level_map.grid, enemy.pos)
        elif key.char == "f":
            player.put_circle(circles, level_map.grid)
            
        # Send a backspace character to erase the typed character
        sys.stdout.write('\b')    
        sys.stdout.flush()
        # Player 2 controls
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
    global player, enemy, npcs, circles, active_explosions, level_map
    
    Player.num_players = 0 # hacky thing so that it works in solo
    
    player = Player()
    
    enemy = Enemy()
    #enemy2 = Enemy("🤢")
    #enemy2.pos = (0, SIZE-1)
    
    npcs = [enemy]
    
    circles = deque()
    
    if Circle.all_fire_cells:
        Circle.all_fire_cells = defaultdict(int)
        
    active_explosions = []
    level_map = Map(SIZE, percentage=PERCENTAGE)
    
    for npc in npcs:
        npc.compute_next_moves(level_map.grid, player.pos)

move_interval = 0.25
last_move_time = time.time()  # Record the start time

player_score = 0
enemy_score = 0

if __name__ == "__main__":
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    reset_game()

    while True:
        os.system("cls" if os.name =="nt" else "clear")
        Circle.detonate_circles(circles, level_map.grid, active_explosions)
        
        # print every row of level grid
        #print(f"Enemy mode:  {'Defend' if enemy.defend_mode else 'Attack'}")
        #print("Enemy next moves: ", enemy.next_moves)
        #print("Active explosions: ", active_explosions)
        
        for npc in npcs:
          npc.move(level_map.grid, player.pos)
        
        # Update explosions
        level_map.draw()
        
        Circle.update_explosions(active_explosions, level_map.grid, player, npcs) 
        
        time.sleep(1/FPS)