from board import Board
from engine import Engine
from tile import Colors
import random
from visualizer import Visualizer

# random.seed(int(input()))
n = 7
m = 8
dx = [0, 0, 1, -1]
dy = [1, -1, 0, 0]
board = [[-1 for j in range(m)] for i in range(n)]
for i in range(n):
    for j in range(m):
        if ((i ^ j) & 1):
            board[i][j] = random.randint(0, 5)
for i in range(n):
    for j in range(m):
        if (board[i][j] != -1):
            continue
        open = set(range(6))
        adj = set()
        for k in range(4):
            nx = i + dx[k]
            ny = j + dy[k]
            if (0 <= nx < n and 0 <= ny < m):
                adj.add(board[nx][ny])
        board[i][j] = random.choice(list(open - adj))
        

start = Board(board)
Visualizer(start)
engine = Engine(start)

player = 0
moves = (engine.get_moves(0, 11))
print(moves)
for move in moves[1]:
    (start.move(Colors(move), player))
    player ^= 1
Visualizer(start)
unicode_square = '■'
moves = (engine.get_moves(player, 11))
print(moves)
for move in moves[1]:
    (start.move(Colors(move), player))
    player ^= 1
Visualizer(start)
moves = (engine.get_moves(player, 11))
print(moves)
for move in moves[1]:
    (start.move(Colors(move), player))
    player ^= 1
Visualizer(start)
