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


def is_in_danger_zone(position, maze):
    """Check if a position is within a radius of 2 of a bomb (value 2)"""
    x, y = position
    directions = [[0,0], (1, 0), (-1, 0), (0, 1), (0, -1)]

    for dx, dy in directions:
        for i in range(1, 3):  # Check up to 2 squares away
            nx, ny = x + dx * i, y + dy * i
            if 0 <= nx < len(maze[0]) and 0 <= ny < len(maze):
                if maze[ny][nx] == 2:  # Bomb detected
                    return True
    return False


def attack_astar(maze, start, end):
    """Returns a list of tuples as a path from the given start to the given end in the given maze"""

    # Create start and end node
    start_node = Node(None, start)
    start_node.g = start_node.h = start_node.f = 0
    end_node = Node(None, end)
    end_node.g = end_node.h = end_node.f = 0

    # Initialize both open and closed list
    open_list = []
    closed_list = []

    # Add the start node
    open_list.append(start_node)

    # Track the closest node to the goal
    closest_node = start_node
    closest_distance = float("inf")

    # Loop until you find the end or exhaust all possibilities
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

        # Calculate the distance from the current node to the goal
        current_distance = (current_node.position[0] - end_node.position[0]) ** 2 + (current_node.position[1] - end_node.position[1]) ** 2

        # Update the closest node if this node is closer to the goal
        if current_distance < closest_distance:
            closest_node = current_node
            closest_distance = current_distance

        # Found the goal
        if current_node == end_node:
            path = []
            current = current_node
            while current is not None:
                path.append(current.position)
                current = current.parent
            return path[::-1]  # Return reversed path

        # Generate children (only horizontal and vertical moves)
        children = []
        for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0)]:  # Adjacent squares without diagonals

            # Get node position
            node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])

            # Make sure within range
            if node_position[0] > (len(maze[0]) - 1) or node_position[0] < 0 or node_position[1] > (len(maze) - 1) or node_position[1] < 0:
                continue

            # Avoid bombs, fire, walls, and danger zones, but allow starting on the initial bomb
            if node_position != start and maze[node_position[1]][node_position[0]] in (2, 1, 3) or is_in_danger_zone(node_position, maze):
                continue

            # Create new node
            new_node = Node(current_node, node_position)

            # Append
            children.append(new_node)

        # Loop through children
        for child in children:

            # Child is on the closed list
            if child in closed_list:
                continue

            # Create the f, g, and h values
            child.g = current_node.g + 1
            child.h = ((child.position[0] - end_node.position[0]) ** 2) + ((child.position[1] - end_node.position[1]) ** 2)
            child.f = child.g + child.h

            # Child is already in the open list
            if any(child == open_node and child.g > open_node.g for open_node in open_list):
                continue

            # Add the child to the open list
            open_list.append(child)

    # If no path was found, return the path to the closest node
    path = []
    current = closest_node
    while current is not None:
        path.append(current.position)
        current = current.parent
    return path[::-1]  # Return reversed path


def main():
    maze = [[-1, 0, 0, 1, 1, 0, 1, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0, 1, 0],
            [0, 1, 0, 1, 0, 0, 1, 1, 0, 0],
            [0, 0, 1, 0, 0, 0, 1, 1, 1, 0],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [0, 0, 1, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 1, 0, 0, 1],
            [0, 1, 0, 0, 0, 1, 1, 1, 0, 1],
            [0, 1, 1, 1, 0, 0, 1, 1, 1, 2],
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]

    
    start = (9, 9)
    end = (0, 0)

    path = attack_astar(maze, start, end)
    print(path)


if __name__ == '__main__':
    main()
