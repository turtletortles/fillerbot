from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from .board import Board
from .tile import Colors

class Visualizer:
    square = '■'
    n = 7
    m = 8

    def __init__(self, board: Board):
        console = Console()
        for i in range(self.n):
            row = []
            for j in range(self.m):
                color = Colors(board.board[i][j].color).name
                owner = board.board[i][j].owner
                if (owner != -1):
                    color = Colors(board.player_colors[owner]).name
                row.append(Panel("  ", style=f"on {color}", padding=(1, 2), expand=True, border_style=color))
            console.print(Columns(row, expand=True), justify='center')

        print('\n' * 5)
