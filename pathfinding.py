from collections import deque


class PathFindingAlgorithm:
    def __init__(self, game):
        # Initialize the pathfinding algorithm with the game reference
        self.game = game
        self.map = game.map.mini_map
        self.ways = [(-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (1, -1), (1, 1), (-1, 1)]
        self.graph = {}
        self.get_graph()

    def get_path(self, start, goal):
        # Get the path from start to goal using BFS
        self.visited = self.bfs(self.graph, start, goal)
        path = [goal]
        step = self.visited.get(goal, start)

        while step and step != start:
            path.append(step)
            step = self.visited[step]
        path.append(start)
        path.reverse()
        return path

    def bfs(self, graph, start, goal):
        # Perform BFS to find the shortest path
        queue = deque([start])
        visited = {start: None}

        while queue:
            current_node = queue.popleft()

            if current_node == goal:
                break

            if current_node not in graph:
                continue  # Skip nodes that are not in the graph

            for next_node in graph[current_node]:
                if next_node not in visited:
                    queue.append(next_node)
                    visited[next_node] = current_node

        return visited

    def get_next_nodes(self, x, y):
        # Get the next possible nodes from the current position
        return [(x + dx, y + dy) for dx, dy in self.ways if (x + dx, y + dy) not in self.game.map.world_map]

    def get_graph(self):
        # Build the graph from the mini_map
        for y, rows in enumerate(self.map):
            for x, columns in enumerate(rows):
                if not columns:
                    self.graph[(x, y)] = self.graph.get((x, y), []) + self.get_next_nodes(x, y)
