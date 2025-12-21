import time

# 方向ベクトル（8方向）
DIRS = [(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)]

# 盤面の重み付け（8x8を想定した標準的な重みマップ）
WEIGHT_MAP = [
    [100, -20, 10,  5,  5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [ 10,  -2,  5,  1,  1,  5,  -2,  10],
    [  5,  -2,  1,  0,  0,  1,  -2,   5],
    [  5,  -2,  1,  0,  0,  1,  -2,   5],
    [ 10,  -2,  5,  1,  1,  5,  -2,  10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10,  5,  5, 10, -20, 100]
]

class NeoOthelloAI:
    def __init__(self):
        self.tt = {} # 置換表

    def get_color_utils(self, color):
        opp = 3 - color if color in (1, 2) else -color
        return opp

    def in_bounds(self, board, x, y):
        return 0 <= y < len(board) and 0 <= x < len(board[y])

    def get_legal_moves(self, board, color):
        opp = self.get_color_utils(color)
        moves = []
        for y, row in enumerate(board):
            for x, val in enumerate(row):
                if val != 0: continue
                if self.is_legal_at(board, x, y, color, opp):
                    moves.append((x, y))
        return moves

    def is_legal_at(self, board, x, y, color, opp):
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if self.in_bounds(board, nx, ny) and board[ny][nx] == opp:
                nx += dx
                ny += dy
                while self.in_bounds(board, nx, ny) and board[ny][nx] == opp:
                    nx += dx
                    ny += dy
                if self.in_bounds(board, nx, ny) and board[ny][nx] == color:
                    return True
        return False

    def apply_move(self, board, x, y, color):
        new_board = [row[:] for row in board]
        new_board[y][x] = color
        opp = self.get_color_utils(color)
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            path = []
            while self.in_bounds(board, nx, ny) and new_board[ny][nx] == opp:
                path.append((nx, ny))
                nx += dx
                ny += dy
            if self.in_bounds(board, nx, ny) and new_board[ny][nx] == color:
                for px, py in path:
                    new_board[py][px] = color
        return new_board

    def evaluate(self, board, color):
        opp = self.get_color_utils(color)
        score = 0
        
        # 1. 重み付け評価 & 石数カウント
        my_stones = 0
        opp_stones = 0
        for y, row in enumerate(board):
            for x, val in enumerate(row):
                if val == color:
                    score += WEIGHT_MAP[y][x] if y < 8 and x < 8 else 5
                    my_stones += 1
                elif val == opp:
                    score -= WEIGHT_MAP[y][x] if y < 8 and x < 8 else 5
                    opp_stones += 1

        # 2. 開放度・機動力（打てる場所が多いほど有利）
        my_moves = len(self.get_legal_moves(board, color))
        opp_moves = len(self.get_legal_moves(board, opp))
        score += (my_moves - opp_moves) * 15

        # 3. 終盤の石数ボーナス
        empties = sum(row.count(0) for row in board)
        if empties < 10:
            score += (my_stones - opp_stones) * 50

        return score

    def negamax(self, board, color, depth, alpha, beta):
        board_hash = (tuple(tuple(row) for row in board), color)
        if board_hash in self.tt:
            t_depth, t_val = self.tt[board_hash]
            if t_depth >= depth: return t_val

        moves = self.get_legal_moves(board, color)
        opp = self.get_color_utils(color)

        if not moves:
            opp_moves = self.get_legal_moves(board, opp)
            if not opp_moves: # 終局
                diff = sum(row.count(color) for row in board) - sum(row.count(opp) for row in board)
                return 1000000 + diff if diff > 0 else -1000000 + diff
            return -self.negamax(board, opp, depth - 1, -beta, -alpha)

        if depth == 0:
            return self.evaluate(board, color)

        best_val = -float('inf')
        # 簡易的なオーダリング：重みが高い順に探索
        moves.sort(key=lambda m: WEIGHT_MAP[m[1]][m[0]] if m[1]<8 and m[0]<8 else 0, reverse=True)

        for mx, my in moves:
            next_b = self.apply_move(board, mx, my, color)
            val = -self.negamax(next_b, opp, depth - 1, -beta, -alpha)
            best_val = max(best_val, val)
            alpha = max(alpha, val)
            if alpha >= beta: break

        self.tt[board_hash] = (depth, best_val)
        return best_val

# ---------------- メイン関数 ----------------
neo_ai = NeoOthelloAI()

def myai(board, color):
    # 探索の深さを空きマスに応じて動的に変更
    empties = sum(row.count(0) for row in board)
    if empties > 50: depth = 4
    elif empties > 15: depth = 5
    else: depth = 8 # 終盤は深く

    moves = neo_ai.get_legal_moves(board, color)
    if not moves: return (-1, -1)

    best_move = moves[0]
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')

    # 反復深化的な要素：最初は浅く、次に深く
    for d in range(1, depth + 1):
        for mx, my in moves:
            nb = neo_ai.apply_move(board, mx, my, color)
            score = -neo_ai.negamax(nb, neo_ai.get_color_utils(color), d - 1, -beta, -alpha)
            if score > best_score:
                best_score = score
                best_move = (mx, my)
    
    return best_move
