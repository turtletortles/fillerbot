from tile import Tile
from tile import Colors
import math
import random

class Board:
    n = 7 
    m = 8
    dx = [0, 0, 1, -1]
    dy = [1, -1, 0, 0]

    def __init__(self, _board: list[list[int]] = [[]]):
        """Generates a random board on empty constructor"""
        self.board = [[Tile(Colors(Colors.empty), i, j) for j in range(8)] for i in range(7)]
        self.player_colors = [Colors.empty, Colors.empty]
        self.player_tiles = [[], []] # assumes we are 0, opp is 1
        self.board_control = [0.0, 0.0]

        if (_board == [[]]):
            _board = self.gen_random()

        for i in range(self.n):
            for j in range(self.m):
                self.board[i][j] = Tile(Colors(_board[i][j]), i, j)

        self.board[self.n - 1][0].owner = 0 
        self.board[0][self.m - 1].owner = 1 
        self.player_tiles[0].append(self.board[self.n - 1][0])
        self.player_tiles[1].append(self.board[0][self.m - 1])
        self.player_colors[0] = self.board[self.n - 1][0].color
        self.player_colors[1] = self.board[0][self.m - 1].color
        self.stack = []

        # if board state is not from starting then make sure adj tiles of same color to corners work
        for i in range(2):
            while (len(self.get_adjacent_unowned(i).get(self.player_colors[i], []))):
                self.move(self.player_colors[i], i, False)

    def gen_random(self):
        board = [[-1 for j in range(self.m)] for i in range(self.n)]
        for i in range(self.n):
            for j in range(self.m):
                if ((i ^ j) & 1):
                    board[i][j] = random.randint(0, 5)
        for i in range(self.n):
            for j in range(self.m):
                if (board[i][j] != -1):
                    continue
                open = set(range(6))
                adj = set()
                for k in range(4):
                    nx = i + self.dx[k]
                    ny = j + self.dy[k]
                    if (0 <= nx < self.n and 0 <= ny < self.m):
                        adj.add(board[nx][ny])
                board[i][j] = random.choice(list(open - adj))
        return board
        
    def get_adjacent_unowned(self, player):
        adj_tiles = {}
        visited = set()
        for c in Colors:
            adj_tiles[c] = []
        for tile in list(self.player_tiles[player]):
            for i in range(4):
                nx = tile.x + self.dx[i]
                ny = tile.y + self.dy[i]
                if (nx, ny) in visited:
                    continue
                visited.add((nx, ny))
                if (not self.inside_board(nx, ny) 
                    or self.board[nx][ny].owner != -1 
                ):
                    continue
                adj_tiles[self.board[nx][ny].color].append((nx, ny))
        return adj_tiles
    
    def undo_move(self):
        if (len(self.stack) == 0):
            return False
        cur = self.stack[-1]
        for i in range(cur[1], len(self.player_tiles[cur[0]])):
            self.player_tiles[cur[0]][i].owner = -1 
        del self.player_tiles[cur[0]][cur[1]:]
        self.player_colors[cur[0]] = cur[2]
        self.board_control[cur[0]] = cur[3]
        self.stack.pop()
        return True
        
    def clone(self):
        new = Board.__new__(Board) 
        new.n = self.n
        new.m = self.m
        new.dx = self.dx
        new.dy = self.dy
        new.board = [[tile.copy() for tile in row] for row in self.board]
        new.player_tiles = [[], []]
        for p in range(2):
            for tile in self.player_tiles[p]:
                new_tile = new.board[tile.x][tile.y]
                new.player_tiles[p].append(new_tile)
        new.player_colors = list(self.player_colors)
        new.stack = list(self.stack)
        new.board_control = list(self.board_control)
        return new

    def inside_board(self, x: int, y: int):
        return 0 <= x < self.n and 0 <= y < self.m

    # -1 if moves can still be made, 0/1 for player win, 2 for draw
    def win(self): 
        if (len(self.player_tiles[0]) + len(self.player_tiles[1]) != 56):
            return -1
        x = len(self.player_tiles[0])
        y = len(self.player_tiles[1])
        if x == y:
            return 2
        return 0 if x > y else 1

    def move(self, color, player, color_check=True):
        if color_check and color in self.player_colors:
            return False

        new_tiles = []
        adj_tiles = self.get_adjacent_unowned(player)
        sum = 0
        for nx, ny in adj_tiles[color]:
            self.board[nx][ny].owner = player
            new_tiles.append(self.board[nx][ny])
            sum += self.corner_dist_gradient(nx, ny, player)
        self.stack.append((player, len(self.player_tiles[player]), self.player_colors[player], self.board_control[player]))
        self.board_control[player] += sum
        self.player_colors[player] = color
        self.player_tiles[player].extend(new_tiles)
        return True
        

    def corner_dist_gradient(self, x: int, y: int, player: int, n: int = 7, m: int = 8) -> float:
        cx, cy = (n - 1, 0) if player == 0 else (0, m - 1)
        dx = x - cx
        dy = y - cy
        dist = (dx ** 2 + dy ** 2) ** 0.5
        max_dist = (n ** 2 + m ** 2) ** 0.5
        norm_dist = dist / max_dist 
        return 1 - pow(2, -5 * norm_dist)

    def normalize_log(self, x):
        """For nonnegative inputs: [0, 3)"""
        if (x == 0):
            return 0
        return (1 + 2 * (math.log(x) / (1 + abs(math.log(x)))))

    def eval(self, player: int):
        winner = self.win()
        if winner != -1:
            if winner == 2:
                return 0
            return float('inf') if winner == player else float('-inf')
        us = len(self.player_tiles[player]) + self.normalize_log(self.board_control[player])
        them = len(self.player_tiles[player ^ 1]) + self.normalize_log(self.board_control[player ^ 1])
        us += len(max(self.get_adjacent_unowned(player).values(), key=lambda x: len(x), default = []))
        them += len(max(self.get_adjacent_unowned(player ^ 1).values(), key=lambda x: len(x), default = []))
        return us - them
