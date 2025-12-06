import tkinter as tk
import random

SHAPES = [
    [[1, 1, 1, 1]], [[1, 1], [1, 1]], [[0, 1, 0], [1, 1, 1]], 
    [[1, 0, 0], [1, 1, 1]], [[0, 0, 1], [1, 1, 1]], 
    [[0, 1, 1], [1, 1, 0]], [[1, 1, 0], [0, 1, 1]]
]
COLORS = ['#0A84FF', '#30D158', '#BF5AF2', '#FF9F0A', '#FF453A', '#64D2FF', '#FFD60A']

class TetrisGame:
    def __init__(self, parent, send_callback, peer_name):
        self.send_callback = send_callback
        self.peer_name = peer_name
        
        # 1. VISUAL FIX: Larger Window to prevent bottom cut-off
        self.window = tk.Toplevel(parent)
        self.window.title(f"Tetris: You vs {peer_name}")
        self.window.geometry("500x750") 
        self.window.configure(bg='#1E1E1E')
        
        self.rows = 20
        self.cols = 10
        self.cell_size = 30
        self.score = 0
        self.opponent_score = 0
        self.level = 1
        self.speed = 500 
        self.game_over = False
        self.board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        
        self._setup_ui()
        
        # Controls
        self.window.bind("<Left>", lambda e: self.move(-1, 0))
        self.window.bind("<Right>", lambda e: self.move(1, 0))
        self.window.bind("<Down>", lambda e: self.move(0, 1))
        self.window.bind("<Up>", lambda e: self.rotate())
        self.window.bind("<space>", lambda e: self.hard_drop())
        
        # Notify opponent we started
        self.send_callback(f"GAME_START:{self.peer_name}")
        self.spawn_piece()
        self.run_game_loop()

    def _setup_ui(self):
        # Header Frame for Scores
        header = tk.Frame(self.window, bg='#1E1E1E')
        header.pack(pady=20, fill=tk.X)
        
        # Your Score
        self.score_label = tk.Label(header, text="YOU: 0", font=("Arial", 18, "bold"), bg='#1E1E1E', fg='#0A84FF')
        self.score_label.pack(side=tk.LEFT, padx=30)
        
        # Opponent Score
        self.opp_label = tk.Label(header, text=f"{self.peer_name}: 0", font=("Arial", 18, "bold"), bg='#1E1E1E', fg='#FF453A')
        self.opp_label.pack(side=tk.RIGHT, padx=30)
        
        # Level Indicator
        self.level_label = tk.Label(self.window, text="Level: 1", font=("Arial", 12), bg='#1E1E1E', fg='#8E8E93')
        self.level_label.pack()

        # Canvas
        self.canvas = tk.Canvas(self.window, width=self.cols*self.cell_size, 
                              height=self.rows*self.cell_size, bg='#252525', highlightthickness=0)
        self.canvas.pack(pady=10)

    def spawn_piece(self):
        if self.game_over: return
        self.current_shape = random.choice(SHAPES)
        self.current_color = random.choice(COLORS)
        self.piece_x = self.cols // 2 - len(self.current_shape[0]) // 2
        self.piece_y = 0
        
        if self.check_collision(self.piece_x, self.piece_y, self.current_shape):
            self.game_over = True
            self.send_callback(f"GAME_OVER_SCORE:{self.score}")
            self.draw_game_over("GAME OVER")

    def check_collision(self, x, y, shape):
        for r, row in enumerate(shape):
            for c, cell in enumerate(row):
                if cell:
                    if x + c < 0 or x + c >= self.cols or y + r >= self.rows: return True
                    if y + r >= 0 and self.board[y + r][x + c]: return True
        return False

    def rotate(self):
        if self.game_over: return
        new_shape = [list(row) for row in zip(*self.current_shape[::-1])]
        if not self.check_collision(self.piece_x, self.piece_y, new_shape):
            self.current_shape = new_shape
            self.draw()

    def move(self, dx, dy):
        if self.game_over: return False
        if not self.check_collision(self.piece_x + dx, self.piece_y + dy, self.current_shape):
            self.piece_x += dx
            self.piece_y += dy
            self.draw()
            return True
        elif dy > 0:
            self.lock_piece()
            return False
        return False

    def hard_drop(self):
        if self.game_over: return
        while not self.check_collision(self.piece_x, self.piece_y + 1, self.current_shape):
            self.piece_y += 1
        self.draw()
        self.lock_piece()

    def lock_piece(self):
        for r, row in enumerate(self.current_shape):
            for c, cell in enumerate(row):
                if cell: self.board[self.piece_y + r][self.piece_x + c] = self.current_color
        self.clear_lines()
        self.spawn_piece()

    def clear_lines(self):
        full_lines = [r for r in range(self.rows) if all(self.board[r])]
        lines_cleared = len(full_lines)
        if lines_cleared > 0:
            for r in full_lines:
                del self.board[r]
                self.board.insert(0, [0 for _ in range(self.cols)])
            
            # Score Update
            scores = [0, 100, 300, 500, 800]
            self.score += scores[lines_cleared] * self.level
            self.level = 1 + self.score // 500
            
            # 2. SPEED FIX: Make it get faster more aggressively
            self.speed = max(50, 500 - (self.level * 50)) 
            
            self.score_label.config(text=f"YOU: {self.score}")
            self.level_label.config(text=f"Level: {self.level}")
            
            # 3. MULTIPLAYER: Send score to opponent
            self.send_callback(f"GAME_SCORE:{self.score}")

    def draw(self):
        self.canvas.delete("all")
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c]: self.draw_cell(c, r, self.board[r][c])
        for r, row in enumerate(self.current_shape):
            for c, cell in enumerate(row):
                if cell: self.draw_cell(self.piece_x + c, self.piece_y + r, self.current_color)

    def draw_cell(self, x, y, color):
        self.canvas.create_rectangle(x*self.cell_size, y*self.cell_size, (x+1)*self.cell_size, (y+1)*self.cell_size, fill=color, outline="black")

    def draw_game_over(self, text):
        # 4. VISUAL FIX: Perfectly Centered Game Over Text
        self.canvas.create_rectangle(50, 250, 250, 350, fill="#1E1E1E", outline="white")
        self.canvas.create_text(150, 300, text=text, fill="red", font=("Arial", 24, "bold"))

    def run_game_loop(self):
        if not self.game_over:
            self.move(0, 1)
            self.window.after(self.speed, self.run_game_loop)
            
    # 5. MULTIPLAYER: Handle incoming data
    def receive_move(self, message):
        if message.startswith("GAME_SCORE:"):
            score = message.split(":")[1]
            self.opp_label.config(text=f"{self.peer_name}: {score}")
        elif message.startswith("GAME_OVER_SCORE:"):
            score = message.split(":")[1]
            self.opp_label.config(text=f"{self.peer_name}: {score} (Final)")
            tk.messagebox.showinfo("Game Info", f"{self.peer_name} finished with {score} points!")