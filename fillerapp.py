from pathlib import Path
from textual.app import App
from textual.widgets import DirectoryTree, Footer, Static 
from textual.widget import Widget
from textual.reactive import var
from textual.message import Message
from rich.panel import Panel
from rich.columns import Columns
from rich.console import Group
from board import Board
from tile import Colors
from engine import Engine
from griddetection import GridDetection

class Grid(Widget):
    n = 7
    m = 8
    hex_colors = {
            "blue": "#61acee",
            "purple": "#6b539f",
            "red": "#e55767",
            "green": "#add367",
            "black": "#414141",
            "yellow": "#fae251"
            }

    def __init__(self, _board: Board):
        super().__init__()
        self.board = _board
        self.styles.height = 36
       
    def render(self):
        columns = []
        for i in range(self.n):
            row = []
            for j in range(self.m):
                color = Colors(self.board.board[i][j].color).name
                owner = self.board.board[i][j].owner
                if (owner != -1):
                    color = Colors(self.board.player_colors[owner]).name
                row.append(Panel("  ", style=f"on {self.hex_colors[color]}", padding=(1, 2), expand=True, border_style=color))
            columns.append(Columns(row, expand=True))
        return Group(*columns)

class EngineWidget(Static):
    engine_line = var([])
    engine_eval = var(0)
    hex_colors = {
            "blue": "#61acee",
            "purple": "#6b539f",
            "red": "#e55767",
            "green": "#add367",
            "black": "#414141",
            "yellow": "#fae251"
            }

    def __init__(self, _engine: Engine):
        super().__init__()
        self.engine = _engine
        self.max_depth = 10
        self.parity = 0
        # self.styles.height = 3
        # self.styles.dock = "bottom"

    def set_parity(self, parity):
        self.parity = parity

    async def on_mount(self):
        self.engine_line = []
        self.run_worker(self.engine.IDDFS(self.parity, self.max_depth, self.update_move), exclusive=True)
    
    def update_move(self, nline, neval):
        self.engine_line = list(nline)
        self.engine_eval = neval
        self.refresh()

    def start_search(self):
        return self.engine.IDDFS(self.parity, self.max_depth, self.update_move)

    def render(self):
        p1_color = Colors(self.engine.board.player_colors[0]).name
        p2_color = Colors(self.engine.board.player_colors[1]).name

        p1 = f"[{self.hex_colors[p1_color]}]{len(self.engine.board.player_tiles[0])}"
        p2 = f"[{self.hex_colors[p2_color]}]{len(self.engine.board.player_tiles[1])}"
        
        tile_counts = f"{p1} - {p2}\n"

        if not self.engine_line:
            best_line = "Best continuation: (thinking...)"
        else:
            line = ' → '.join(
                f"[{self.hex_colors[color.name]}]{color.name}"
                for color in self.engine_line
            )
            best_line = f"Best continuation: {line}"

        return f"{tile_counts}{best_line}[/]\nEngine evaluation: {self.engine_eval}"

class FileSelected(Message):
    def __init__(self, path):
        self.path = path
        super().__init__()

class FilePickerWidget(DirectoryTree):
    image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp", ".heic", ".heif", ".ico", ".psd", ".svg", ".eps", ".ai", ".pdf"]

    def filter_paths(self, paths):
        return [
            path for path in paths
            if not path.name.startswith(".") and (
                Path(path).is_dir() or Path(path).suffix.lower() in self.image_extensions
            )
        ]

    def on_tree_node_selected(self, event: DirectoryTree.NodeSelected) -> None:
        path = event.node.data.path
        if Path(path).is_file() and Path(path).suffix.lower() in self.image_extensions:
            self.post_message(FileSelected(Path(path)))

class FillerApp(App):
    def __init__(self, driver_class=None, css_path=None, watch_css=False, ansi_color=False):
        super().__init__(driver_class, css_path, watch_css, ansi_color)
        self.board = Board()
        self.grid = Grid(self.board)
        self.engine = Engine(self.board)
        self.engine_display = EngineWidget(self.engine)
        self.detector = GridDetection()
        self.parity = 0
        self.file_picker = None
        self.selected_file = None

    BINDINGS = [
        ("1", "make_move(0)", "Move Red"),
        ("2", "make_move(1)", "Move Green"),
        ("3", "make_move(2)", "Move Yellow"),
        ("4", "make_move(3)", "Move Blue"),
        ("5", "make_move(4)", "Move Purple"),
        ("6", "make_move(5)", "Move Black"),
        ("7", "make_move(-1)", "Engine Move"),
        ("0", "pass", "Pass"),
        ("i", "import_board", "Import Board"),
        ("u", "undo()", "Undo"),
        ("r", "make_move(0)"),
        ("g", "make_move(1)"),
        ("y", "make_move(2)"),
        ("b", "make_move(3)"),
        ("p", "make_move(4)"),
        ("k", "make_move(5)"),
        ("e", "make_move(-1)")
    ]

    async def action_import_board(self):
        if self.file_picker:
            await self.file_picker.remove()
            self.file_picker = None
            return
        self.file_picker = FilePickerWidget("./")
        await self.mount(self.file_picker)

    async def on_file_selected(self, message: FileSelected):
        self.selected_file = message.path
        if self.file_picker:
            await self.file_picker.remove()
            self.file_picker = None
        self.detector.process(self.selected_file)
        print(self.selected_file)
        print(self.detector.get_board())
        self.board = Board(self.detector.get_board())

        await self.grid.remove()
        await self.engine_display.remove()

        self.grid = Grid(self.board)
        self.engine = Engine(self.board)
        self.engine_display = EngineWidget(self.engine)

        self.parity = 0
        await self.mount(self.grid)
        await self.mount(self.engine_display)

        self.run_worker(
            self.engine_display.engine.IDDFS(self.parity, self.engine_display.max_depth, self.engine_display.update_move),
            exclusive=True
        )

        self.selected_file = None


    def action_pass(self):
        self.parity ^= 1
        self.engine_display.set_parity(self.parity)
        self.run_worker(
            self.engine_display.engine.IDDFS(self.parity, self.engine_display.max_depth, self.engine_display.update_move),
            exclusive=True
        )

    def action_make_move(self, color: int):
        if (color == -1 and len(self.engine_display.engine_line)):
            color = self.engine_display.engine_line[0]
        success = self.board.move(Colors(color), self.parity)
        self.grid.refresh()
        self.parity ^= success
        self.engine_display.set_parity(self.parity)
        self.run_worker(
            self.engine_display.engine.IDDFS(self.parity, self.engine_display.max_depth, self.engine_display.update_move),
            exclusive=True
        )

    def action_undo(self):
        success = self.board.undo_move()
        self.grid.refresh()
        self.parity ^= success
        self.engine_display.set_parity(self.parity)
        self.run_worker(
            self.engine_display.engine.IDDFS(self.parity, self.engine_display.max_depth, self.engine_display.update_move),
            exclusive=True
        )

    def compose(self):
        yield self.grid
        yield self.engine_display
        yield Footer()
