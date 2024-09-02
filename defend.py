class Node:
    """A node class for A* Pathfinding"""

    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position

        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, other):
        return self.position == other.position


def simulate_explosions(maze):
    """Simulate explosions by converting bombs (2) to fire (3) based on their explosion radius"""
    
    # theres a bug here it shouldnt simulate past walls
    
    rows = len(maze)
    cols = len(maze[0])
    new_maze = [row[:] for row in maze]  # Copy of the maze

    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    for y in range(rows):
        for x in range(cols):
            if maze[y][x] == 2:  # Found a bomb
                # Convert the bomb itself to fire
                new_maze[y][x] = 3
                # Spread the explosion in the four directions
                for dx, dy in directions:
                    for i in range(1, 3):  # Radius of 2
                        nx, ny = x + dx * i, y + dy * i
                        if 0 <= nx < cols and 0 <= ny < rows:
                            if new_maze[ny][nx] != 1:  # Only spread fire over empty cells
                                new_maze[ny][nx] = 3

    return new_maze


def defend_astar(maze, start):
    """Returns a list of tuples as a path from the given start to the nearest safe spot (0 or -1)"""
    maze = simulate_explosions(maze)
    
    # Create start node
    start_node = Node(None, start)
    start_node.g = start_node.h = start_node.f = 0

    # Initialize both open and closed list
    open_list = []
    closed_list = []

    # Add the start node
    open_list.append(start_node)

    # Track the closest safe spot
    closest_safe_spot = None

    # Loop until you find a safe spot or exhaust all possibilities
    while len(open_list) > 0:
        # Get the current node
        current_node = open_list[0]
        current_index = 0
        for index, item in enumerate(open_list):
            if item.f < current_node.f:
                current_node = item
                current_index = index

        # Pop current off open list, add to closed list
        open_list.pop(current_index)
        closed_list.append(current_node)

        # Check if we've reached a safe spot
        x, y = current_node.position
        if maze[y][x] == 0 or maze[y][x] == -1:
            path = []
            current = current_node
            while current is not None:
                path.append(current.position)
                current = current.parent
            return path[::-1]  # Return reversed path

        # Generate children (only horizontal and vertical moves)
        children = []
        for new_position in [(1, 0), (-1, 0), (0, 1), (0, -1)]:  # Adjacent squares without diagonals

            # Get node position
            node_position = (x + new_position[0], y + new_position[1])

            # Make sure within range
            if node_position[0] > (len(maze[0]) - 1) or node_position[0] < 0 or node_position[1] > (len(maze) - 1) or node_position[1] < 0:
                continue

            # Skip impassable terrain: walls (1)
            if maze[node_position[1]][node_position[0]] == 1:
                continue

            # Create new node with a higher cost for moving into fire
            new_node = Node(current_node, node_position)
            new_node.g = current_node.g + (2 if maze[node_position[1]][node_position[0]] == 3 else 1)  # Higher cost for fire
            new_node.h = ((new_node.position[0] - start[0]) ** 2) + ((new_node.position[1] - start[1]) ** 2)
            new_node.f = new_node.g + new_node.h

            # Skip nodes already in the closed list
            if new_node in closed_list:
                continue

            # Skip nodes already in the open list with a lower g value
            if any(child == new_node and new_node.g > child.g for child in open_list):
                continue

            # Add the new node to the open list
            open_list.append(new_node)
    

    # If no path was found, return None
    return None


def main():
    maze = [[-1, 0, 1, 0, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 0, 0, 1, 1, 1, 1, 1, 1],
            [0, 1, 0, 1, 1, 1, 1, 1, 0, 0],
            [0, 1, 1, 0, 1, 0, 0, 1, 1, 1],
            [1, 1, 0, 0, 0, 0, 1, 1, 0, 1],
            [1, 0, 0, 0, 1, 0, 0, 0, 1, 1],
            [1, 1, 1, 0, 1, 0, 1, 0, 1, 1],
            [0, 1, 1, 1, 1, 0, 0, 0, 1, 0],
            [1, 1, 1, 0, 1, 1, 0, 2, 0, -2]]

    start = (9, 9)  # Start position of the enemy

    # Simulate explosions
    exploded_maze = simulate_explosions(maze)

    # Find the shortest path to a safe spot
    path = defend_astar(maze, start)
    
    if path:
        print("Safe path found:", path)
    else:
        print("No safe path available.")

    # Display the exploded maze
    for row in exploded_maze:
        print(row)


if __name__ == '__main__':
    main()