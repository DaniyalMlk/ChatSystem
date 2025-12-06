import tkinter as tk
import random

# Tetromino shapes
SHAPES = [
    [[1, 1, 1, 1]],                       # I
    [[1, 1], [1, 1]],                     # O
    [[0, 1, 0], [1, 1, 1]],               # T
    [[1, 0, 0], [1, 1, 1]],               # L
    [[0, 0, 1], [1, 1, 1]],               # J
    [[0, 1, 1], [1, 1, 0]],               # S
    [[1, 1, 0], [0, 1, 1]]                # Z
]
# Matching colors for shapes
COLORS = ['#0A84FF', '#30D158', '#BF5AF2', '#FF9F0A', '#FF453A', '#64D2FF', '#FFD60A']

class TetrisGame:
    def __init__(self, parent, send_callback, peer_name):
        self.send_callback = send_callback
        self.peer_name = peer_name
        
        # Create Game Window
        self.window = tk.Toplevel(parent)
        self.window.title(f"Tetris vs {peer_name}")
        self.window.geometry("400x600")
        self.window.configure(bg='#1E1E1E')
        
        # Game Config
        self.rows = 20
        self.cols = 10
        self.cell_size = 30
        self.score = 0
        self.level = 1
        self.speed = 500  # Start speed (ms)
        self.game_over = False
        self.board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        
        self._setup_ui()
        
        # Controls
        self.window.bind("<Left>", lambda e: self.move(-1, 0))
        self.window.bind("<Right>", lambda e: self.move(1, 0))
        self.window.bind("<Down>", lambda e: self.move(0, 1))
        self.window.bind("<Up>", lambda e: self.rotate())
        
        # Start
        self.spawn_piece()
        self.run_game_loop()

    def _setup_ui(self):
        # Header
        self.score_label = tk.Label(self.window, text="Score: 0  Level: 1", 
                                  font=("Arial", 20, "bold"), bg='#1E1E1E', fg='white')
        self.score_label.pack(pady=20)
        
        # Board Canvas
        self.canvas = tk.Canvas(self.window, width=self.cols*self.cell_size, 
                              height=self.rows*self.cell_size, bg='#252525', highlightthickness=0)
        self.canvas.pack()

    def spawn_piece(self):
        self.current_shape = random.choice(SHAPES)
        self.current_color = random.choice(COLORS)
        # Center piece
        self.piece_x = self.cols // 2 - len(self.current_shape[0]) // 2
        self.piece_y = 0
        
        if self.check_collision(self.piece_x, self.piece_y, self.current_shape):
            self.game_over = True
            self.send_callback(f"GAME_OVER: I scored {self.score} in Tetris!")
            self.canvas.create_text(
                (self.cols*self.cell_size)/2, (self.rows*self.cell_size)/2,
                text="GAME OVER", fill="white", font=("Arial", 30, "bold")
            )

    def check_collision(self, x, y, shape):
        for r, row in enumerate(shape):
            for c, cell in enumerate(row):
                if cell:
                    if (y + r >= self.rows or x + c < 0 or x + c >= self.cols or 
                        self.board[y + r][x + c]):
                        return True
        return False

    def rotate(self):
        # Matrix rotation logic
        new_shape = [list(row) for row in zip(*self.current_shape[::-1])]
        if not self.check_collision(self.piece_x, self.piece_y, new_shape):
            self.current_shape = new_shape
            self.draw()

    def move(self, dx, dy):
        if not self.game_over and not self.check_collision(self.piece_x + dx, self.piece_y + dy, self.current_shape):
            self.piece_x += dx
            self.piece_y += dy
            self.draw()
            return True
        elif dy > 0: # Hit bottom
            self.lock_piece()
            return False
        return False

    def lock_piece(self):
        for r, row in enumerate(self.current_shape):
            for c, cell in enumerate(row):
                if cell:
                    self.board[self.piece_y + r][self.piece_x + c] = self.current_color
        self.clear_lines()
        self.spawn_piece()

    def clear_lines(self):
        new_board = [row for row in self.board if any(c == 0 for c in row)]
        lines_cleared = self.rows - len(new_board)
        
        if lines_cleared > 0:
            for _ in range(lines_cleared):
                new_board.insert(0, [0 for _ in range(self.cols)])
            self.board = new_board
            
            # Score Calculation
            self.score += lines_cleared * 100 * self.level
            self.level = 1 + self.score // 500
            
            # Speed up logic (lower ms = faster)
            self.speed = max(100, 500 - (self.level * 30))
            
            self.score_label.config(text=f"Score: {self.score}  Level: {self.level}")

    def draw(self):
        self.canvas.delete("all")
        # Draw board
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c]:
                    self.draw_cell(c, r, self.board[r][c])
        # Draw current piece
        for r, row in enumerate(self.current_shape):
            for c, cell in enumerate(row):
                if cell:
                    self.draw_cell(self.piece_x + c, self.piece_y + r, self.current_color)

    def draw_cell(self, x, y, color):
        self.canvas.create_rectangle(
            x*self.cell_size, y*self.cell_size, 
            (x+1)*self.cell_size, (y+1)*self.cell_size, 
            fill=color, outline=""
        )

    def run_game_loop(self):
        if not self.game_over:
            self.move(0, 1) # Auto drop
            self.draw()
            self.window.after(self.speed, self.run_game_loop)
            
    def receive_move(self, message):
        pass