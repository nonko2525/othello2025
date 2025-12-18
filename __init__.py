<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>最強オセロAI - GitHub Edition</title>
    <style>
        body { background: #2c3e50; color: white; font-family: sans-serif; text-align: center; }
        #board { 
            display: grid; grid-template-columns: repeat(8, 50px); grid-template-rows: repeat(8, 50px); 
            gap: 2px; width: 416px; margin: 20px auto; background: #34495e; padding: 5px; border: 5px solid #1a252f;
        }
        .cell { 
            width: 50px; height: 50px; background: #27ae60; display: flex; 
            align-items: center; justify-content: center; cursor: pointer; position: relative;
        }
        .cell:hover { background: #2ecc71; }
        .disc { width: 40px; height: 40px; border-radius: 50%; display: none; }
        .black { background: #000; display: block; box-shadow: 2px 2px 4px rgba(0,0,0,0.4); }
        .white { background: #fff; display: block; box-shadow: 2px 2px 4px rgba(0,0,0,0.2); }
        .info { font-size: 1.2rem; margin-bottom: 10px; }
        #status { font-weight: bold; color: #f1c40f; }
    </style>
</head>
<body>
    <h1>Othello AI "Grandmaster"</h1>
    <div class="info">黒(あなた) vs 白(AI) | <span id="status">あなたの番です</span></div>
    <div id="board"></div>
    <div>黒: <span id="black-score">2</span> / 白: <span id="white-score">2</span></div>
    <button onclick="resetGame()" style="margin-top: 20px; padding: 10px 20px;">リセット</button>

    <script>
        const BOARD_SIZE = 8;
        const BLACK = 1, WHITE = -1, EMPTY = 0;
        let board = Array(BOARD_SIZE).fill().map(() => Array(BOARD_SIZE).fill(EMPTY));
        let turn = BLACK;

        // 評価関数用の重みテーブル（角を重視し、角の隣を避ける）
        const WEIGHTS = [
            [100, -20, 10,  5,  5, 10, -20, 100],
            [-20, -50, -2, -2, -2, -2, -50, -20],
            [ 10,  -2,  5,  1,  1,  5,  -2,  10],
            [  5,  -2,  1,  0,  0,  1,  -2,   5],
            [  5,  -2,  1,  0,  0,  1,  -2,   5],
            [ 10,  -2,  5,  1,  1,  5,  -2,  10],
            [-20, -50, -2, -2, -2, -2, -50, -20],
            [100, -20, 10,  5,  5, 10, -20, 100]
        ];

        function init() {
            board = Array(BOARD_SIZE).fill().map(() => Array(BOARD_SIZE).fill(EMPTY));
            board[3][3] = WHITE; board[3][4] = BLACK;
            board[4][3] = BLACK; board[4][4] = WHITE;
            draw();
        }

        function draw() {
            const boardEl = document.getElementById('board');
            boardEl.innerHTML = '';
            let bCount = 0, wCount = 0;
            for (let r = 0; r < BOARD_SIZE; r++) {
                for (let c = 0; c < BOARD_SIZE; c++) {
                    const cell = document.createElement('div');
                    cell.className = 'cell';
                    cell.onclick = () => playerMove(r, c);
                    const disc = document.createElement('div');
                    disc.className = 'disc' + (board[r][c] === BLACK ? ' black' : board[r][c] === WHITE ? ' white' : '');
                    cell.appendChild(disc);
                    boardEl.appendChild(cell);
                    if (board[r][c] === BLACK) bCount++;
                    if (board[r][c] === WHITE) wCount++;
                }
            }
            document.getElementById('black-score').innerText = bCount;
            document.getElementById('white-score').innerText = wCount;
        }

        function canFlip(r, c, color, targetBoard) {
            if (targetBoard[r][c] !== EMPTY) return false;
            const dirs = [[-1,-1],[-1,0],[-1,1],[0,-1],[0,1],[1,-1],[1,0],[1,1]];
            for (let [dr, dc] of dirs) {
                let nr = r + dr, nc = c + dc, foundOpponent = false;
                while (nr >= 0 && nr < 8 && nc >= 0 && nc < 8) {
                    if (targetBoard[nr][nc] === -color) foundOpponent = true;
                    else if (targetBoard[nr][nc] === color) { if (foundOpponent) return true; break; }
                    else break;
                    nr += dr; nc += dc;
                }
            }
            return false;
        }

        function makeMove(r, c, color, targetBoard) {
            const nextBoard = targetBoard.map(row => [...row]);
            nextBoard[r][c] = color;
            const dirs = [[-1,-1],[-1,0],[-1,1],[0,-1],[0,1],[1,-1],[1,0],[1,1]];
            for (let [dr, dc] of dirs) {
                let nr = r + dr, nc = c + dc, flipList = [];
                while (nr >= 0 && nr < 8 && nc >= 0 && nc < 8) {
                    if (nextBoard[nr][nc] === -color) flipList.push([nr, nc]);
                    else if (nextBoard[nr][nc] === color) {
                        for (let [fr, fc] of flipList) nextBoard[fr][fc] = color;
                        break;
                    } else break;
                    nr += dr; nc += dc;
                }
            }
            return nextBoard;
        }

        function getValidMoves(color, targetBoard) {
            const moves = [];
            for (let r = 0; r < 8; r++) {
                for (let c = 0; c < 8; c++) {
                    if (canFlip(r, c, color, targetBoard)) moves.push([r, c]);
                }
            }
            return moves;
        }

        // AIの思考アルゴリズム: Alpha-Beta法
        function evaluate(targetBoard) {
            let score = 0;
            for (let r = 0; r < 8; r++) {
                for (let c = 0; c < 8; c++) {
                    score += targetBoard[r][c] * WEIGHTS[r][c];
                }
            }
            return score;
        }

        function minimax(targetBoard, depth, alpha, beta, isMaximizing) {
            if (depth === 0) return evaluate(targetBoard);
            const color = isMaximizing ? WHITE : BLACK;
            const moves = getValidMoves(color, targetBoard);
            if (moves.length === 0) return minimax(targetBoard, depth - 1, alpha, beta, !isMaximizing);

            if (isMaximizing) {
                let maxEval = -Infinity;
                for (let [r, c] of moves) {
                    let eval = minimax(makeMove(r, c, WHITE, targetBoard), depth - 1, alpha, beta, false);
                    maxEval = Math.max(maxEval, eval);
                    alpha = Math.max(alpha, eval);
                    if (beta <= alpha) break;
                }
                return maxEval;
            } else {
                let minEval = Infinity;
                for (let [r, c] of moves) {
                    let eval = minimax(makeMove(r, c, BLACK, targetBoard), depth - 1, alpha, beta, true);
                    minEval = Math.min(minEval, eval);
                    beta = Math.min(beta, eval);
                    if (beta <= alpha) break;
                }
                return minEval;
            }
        }

        async function playerMove(r, c) {
            if (turn !== BLACK || !canFlip(r, c, BLACK, board)) return;
            board = makeMove(r, c, BLACK, board);
            draw();
            turn = WHITE;
            document.getElementById('status').innerText = "AIが考えています...";
            
            setTimeout(aiMove, 500);
        }

        function aiMove() {
            const moves = getValidMoves(WHITE, board);
            if (moves.length > 0) {
                let bestScore = -Infinity;
                let bestMove = moves[0];
                // 探索の深さ（後半ほど深く読む）
                const depth = board.flat().filter(x => x !== EMPTY).length > 50 ? 6 : 4;

                for (let [r, c] of moves) {
                    let score = minimax(makeMove(r, c, WHITE, board), depth, -Infinity, Infinity, false);
                    if (score > bestScore) {
                        bestScore = score;
                        bestMove = [r, c];
                    }
                }
                board = makeMove(bestMove[0], bestMove[1], WHITE, board);
            }
            
            turn = BLACK;
            if (getValidMoves(BLACK, board).length === 0) {
                if (getValidMoves(WHITE, board).length === 0) {
                    endGame();
                } else {
                    document.getElementById('status').innerText = "あなたはパスです（AIが続けて打ちます）";
                    setTimeout(aiMove, 1000);
                }
            } else {
                document.getElementById('status').innerText = "あなたの番です";
            }
            draw();
        }

        function endGame() {
            const b = board.flat().filter(x => x === BLACK).length;
            const w = board.flat().filter(x => x === WHITE).length;
            const msg = b > w ? "あなたの勝ち！" : b < w ? "AIの勝ち！" : "引き分け！";
            document.getElementById('status').innerText = "ゲーム終了: " + msg;
        }

        function resetGame() {
            turn = BLACK;
            document.getElementById('status').innerText = "あなたの番です";
            init();
        }

        init();
    </script>
</body>
</html>
