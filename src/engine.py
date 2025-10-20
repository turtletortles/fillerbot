from types import FunctionType
from .board import Board
from .tile import Colors
import asyncio

class Engine:
    def __init__(self, _board: Board):
        self.board = _board
        self.killer_moves = {}
        self.principal_variation = {}
        self.count = 0

    def get_children(self, cur_board: Board, player: int, depth: int):
        children = []
        for color in Colors:
            if color == Colors.empty or color in cur_board.player_colors:
                continue
            before = len(cur_board.player_tiles[player])
            if not cur_board.move(color, player):
                continue
            after = len(cur_board.player_tiles[player])
            delta = after - before
            children.append((color, delta))
            cur_board.undo_move()

        pv = self.principal_variation.get(depth, -1)
        children.sort(key=lambda x: (0 if pv == x[0] else 1 if x[0] in self.killer_moves.get(depth, []) else 2, -x[1]))
        return [color for color, _ in children]


    async def alphabeta_search(self, cur_board: Board, depth: int, alpha: float, beta: float,
                  player: int, path: list[Colors], root: int) -> tuple[float, list[Colors]]:
        if depth == 0 or cur_board.win() != -1:
            eval = cur_board.eval(root)
            return eval, path[:]

        self.count += 1
        if (self.count % 100 == 0):
            await asyncio.sleep(0)
            if (asyncio.current_task().cancelled()):
                raise asyncio.CancelledError()

        if player == root:
            max_eval = float('-inf')
            best_path = []
            for color in self.get_children(cur_board, player, depth):
                if not cur_board.move(color, player):
                    continue
                path.append(color)
                eval, result_path = await self.alphabeta_search(cur_board, depth - 1, alpha, beta, player ^ 1, path, root)
                path.pop()
                cur_board.undo_move()

                if eval > max_eval:
                    max_eval = eval
                    best_path = result_path[:]

                alpha = max(alpha, max_eval)
                if beta <= alpha:
                    self.killer_moves.setdefault(depth, [])
                    if color not in self.killer_moves[depth]:
                        self.killer_moves[depth].append(color)
                        if len(self.killer_moves[depth]) > 2:
                            self.killer_moves[depth].pop(0)
                    break
            return max_eval, best_path
        else:
            min_eval = float('inf')
            best_path = []
            for color in self.get_children(cur_board, player, depth):
                if not cur_board.move(color, player):
                    continue
                path.append(color)
                eval, result_path = await self.alphabeta_search(cur_board, depth - 1, alpha, beta, player ^ 1, path, root)
                path.pop()
                cur_board.undo_move()

                if eval < min_eval:
                    min_eval = eval
                    best_path = result_path[:]

                beta = min(beta, min_eval)
                if beta <= alpha:
                    self.killer_moves.setdefault(depth, [])
                    if color not in self.killer_moves[depth]:
                        self.killer_moves[depth].append(color)
                        if len(self.killer_moves[depth]) > 2:
                            self.killer_moves[depth].pop(0)
                    break
            return min_eval, best_path

    async def get_moves(self, player: int, depth: int, clear_killers=True, clear_pv=True):
        nboard = self.board.clone()
        best_eval = float('-inf')
        best_path = []
        if clear_killers:
            self.killer_moves.clear()
        if clear_pv:
            self.principal_variation.clear()

        for color in self.get_children(nboard, player, depth):
            if not nboard.move(color, player):
                continue
            path = [color]
            eval_score, res_path = await self.alphabeta_search(nboard, depth - 1, float('-inf'), float('inf'), player ^ 1, path, player)
            nboard.undo_move()
            if eval_score > best_eval:
                best_eval = eval_score
                best_path = res_path

        return best_eval, best_path

    async def IDDFS(self, player: int, depth: int, callback=None):
        eval = 0
        path = []
        funny_count = 0
        for d in range(2, depth + 1, 2):
            try:
                eval, path = await self.get_moves(player, d, d == 1, d == 1)
            except asyncio.CancelledError:
                return
            if path:
                self.principal_variation[d] = path[0]
            if (eval == float('inf') or eval == float('-inf')):
                if funny_count:
                    break
                else:
                    funny_count += 1
            if callback is not None:
                callback(path, eval)

            await asyncio.sleep(0)
            if (asyncio.current_task().cancelled()):
                return
