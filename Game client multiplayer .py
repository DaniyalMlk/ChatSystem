"""
game_client_multiplayer.py - Tetris with INDIVIDUAL SCORES for 3+ players
Shows: nomu: 0 | zori: 50 | dan: 30
"""
import tkinter as tk
from tkinter import messagebox
import random
import json

# Tetris colors
COLORS = {
    'I': '#00F0F0',  # Cyan
    'O': '#F0F000',  # Yellow
    'T': '#A000F0',  # Purple
    'S': '#00F000',  # Green
    'Z': '#F00000',  # Red
    'J': '#0000F0',  # Blue
    'L': '#F0A000',  # Orange
    'empty': '#1E1E1E',
    'grid': '#2E2E2E'
}

# Tetromino shapes
SHAPES = {
    'I': [[1, 1, 1, 1]],
    'O': [[1, 1], [1, 1]],
    'T': [[0, 1, 0], [1, 1, 1]],
    'S': [[0, 1, 1], [1, 1, 0]],
    'Z': [[1, 1, 0], [0, 1, 1]],
    'J': [[1, 0, 0], [1, 1, 1]],
    'L': [[0, 0, 1], [1, 1, 1]]
}

class TetrisGame:
    def __init__(self, parent, send_callback, player_name, is_group=False):
        """Initialize multiplayer Tetris game"""
        self.send_callback = send_callback
        self.player_name = player_name
        self.is_group = is_group
        
        # Game state
        self.board_width = 10
        self.board_height = 20
        self.cell_size = 25
        self.game_over = False
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        
        # Multiplayer scores - tracks ALL players
        self.player_scores = {}  # {player_name: score}
        
        # Board state
        self.board = [[None for _ in range(self.board_width)] 
                      for _ in range(self.board_height)]
        
        # Current piece
        self.current_piece = None
        self.current_shape = None
        self.current_color = None
        self.piece_x = 0
        self.piece_y = 0
        
        # Create window
        self.window = tk.Toplevel(parent)
        if is_group:
            self.window.title("Tetris: Group Game")
        else:
            self.window.title(f"Tetris: You vs {player_name}")
        
        self.window.configure(bg='#0E0E0E')
        self.window.resizable(False, False)
        
        self._build_ui()
        self._spawn_piece()
        self._game_loop()
    
    def _build_ui(self):
        """Build the game UI with multiplayer scoreboard"""
        main_frame = tk.Frame(self.window, bg='#0E0E0E')
        main_frame.pack(padx=20, pady=20)
        
        # === MULTIPLAYER SCOREBOARD (TOP) ===
        if self.is_group:
            score_frame = tk.Frame(main_frame, bg='#0E0E0E')
            score_frame.pack(pady=(0, 10))
            
            tk.Label(score_frame, text="🏆 SCOREBOARD", 
                    font=('Arial', 14, 'bold'),
                    bg='#0E0E0E', fg='#FFD700').pack()
            
            # Container for player scores
            self.scoreboard_frame = tk.Frame(score_frame, bg='#1E1E1E')
            self.scoreboard_frame.pack(pady=5, padx=10, fill='x')
            
            # Initialize with just you
            self._update_scoreboard()
        
        # === GAME INFO (YOUR SCORE) ===
        info_frame = tk.Frame(main_frame, bg='#0E0E0E')
        info_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        # Your score (always shown)
        tk.Label(info_frame, text="YOU", font=('Arial', 16, 'bold'),
                bg='#0E0E0E', fg='#00BFFF').pack(pady=(0, 5))
        
        self.score_label = tk.Label(info_frame, text="0", 
                                    font=('Arial', 32, 'bold'),
                                    bg='#0E0E0E', fg='#00BFFF')
        self.score_label.pack()
        
        tk.Label(info_frame, text="Level", font=('Arial', 10),
                bg='#0E0E0E', fg='#888888').pack(pady=(20, 0))
        self.level_label = tk.Label(info_frame, text="1", 
                                    font=('Arial', 18),
                                    bg='#0E0E0E', fg='white')
        self.level_label.pack()
        
        tk.Label(info_frame, text="Lines", font=('Arial', 10),
                bg='#0E0E0E', fg='#888888').pack(pady=(20, 0))
        self.lines_label = tk.Label(info_frame, text="0", 
                                    font=('Arial', 18),
                                    bg='#0E0E0E', fg='white')
        self.lines_label.pack()
        
        # Controls
        tk.Label(info_frame, text="\n⌨️ Controls:", font=('Arial', 9, 'bold'),
                bg='#0E0E0E', fg='#888888').pack()
        tk.Label(info_frame, text="← → Move\n↓ Drop\n↑ Rotate\nSpace: Instant Drop", 
                font=('Arial', 8), bg='#0E0E0E', fg='#666666',
                justify=tk.LEFT).pack()
        
        # === GAME BOARD ===
        game_frame = tk.Frame(main_frame, bg='#000000', bd=2, relief=tk.RAISED)
        game_frame.pack(side=tk.LEFT)
        
        self.canvas = tk.Canvas(game_frame, 
                               width=self.board_width * self.cell_size,
                               height=self.board_height * self.cell_size,
                               bg='#1E1E1E', highlightthickness=0)
        self.canvas.pack()
        
        # Draw grid
        for i in range(self.board_height + 1):
            self.canvas.create_line(0, i * self.cell_size,
                                   self.board_width * self.cell_size,
                                   i * self.cell_size,
                                   fill=COLORS['grid'], width=1)
        for i in range(self.board_width + 1):
            self.canvas.create_line(i * self.cell_size, 0,
                                   i * self.cell_size,
                                   self.board_height * self.cell_size,
                                   fill=COLORS['grid'], width=1)
        
        # Key bindings
        self.window.bind('<Left>', lambda e: self._move(-1, 0))
        self.window.bind('<Right>', lambda e: self._move(1, 0))
        self.window.bind('<Down>', lambda e: self._move(0, 1))
        self.window.bind('<Up>', lambda e: self._rotate())
        self.window.bind('<space>', lambda e: self._instant_drop())
    
    def _update_scoreboard(self):
        """Update the multiplayer scoreboard display"""
        if not self.is_group:
            return
        
        # Clear existing labels
        for widget in self.scoreboard_frame.winfo_children():
            widget.destroy()
        
        # Add your score
        if self.player_name not in self.player_scores:
            self.player_scores[self.player_name] = self.score
        else:
            self.player_scores[self.player_name] = self.score
        
        # Sort by score (highest first)
        sorted_players = sorted(self.player_scores.items(), 
                               key=lambda x: x[1], reverse=True)
        
        # Display all players
        for idx, (name, score) in enumerate(sorted_players):
            # Color: Gold for 1st, Silver for 2nd, Bronze for 3rd
            if idx == 0:
                color = '#FFD700'  # Gold
                medal = '🥇'
            elif idx == 1:
                color = '#C0C0C0'  # Silver
                medal = '🥈'
            elif idx == 2:
                color = '#CD7F32'  # Bronze
                medal = '🥉'
            else:
                color = '#FFFFFF'
                medal = '  '
            
            # Highlight your name
            if name == self.player_name:
                bg = '#2E4E2E'
                name_display = f"YOU ({name})"
                font_weight = 'bold'
            else:
                bg = '#1E1E1E'
                name_display = name
                font_weight = 'normal'
            
            player_frame = tk.Frame(self.scoreboard_frame, bg=bg)
            player_frame.pack(fill='x', pady=2)
            
            tk.Label(player_frame, text=f"{medal} {name_display}: {score}", 
                    font=('Arial', 11, font_weight),
                    bg=bg, fg=color, anchor='w').pack(side=tk.LEFT, padx=10, pady=3)
    
    def _spawn_piece(self):
        """Spawn a new piece"""
        if self.game_over:
            return
        
        shape_name = random.choice(list(SHAPES.keys()))
        self.current_shape = SHAPES[shape_name]
        self.current_color = COLORS[shape_name]
        self.current_piece = [[1 if cell else 0 for cell in row] 
                             for row in self.current_shape]
        
        self.piece_x = self.board_width // 2 - len(self.current_piece[0]) // 2
        self.piece_y = 0
        
        # Check if piece can spawn
        if self._check_collision(self.piece_x, self.piece_y):
            self.game_over = True
            self._send_game_over()
            messagebox.showinfo("Game Over", 
                              f"Final Score: {self.score}\nLevel: {self.level}")
    
    def _check_collision(self, x, y, piece=None):
        """Check if piece collides with board or boundaries"""
        if piece is None:
            piece = self.current_piece
        
        for py, row in enumerate(piece):
            for px, cell in enumerate(row):
                if cell:
                    board_x = x + px
                    board_y = y + py
                    
                    # Check boundaries
                    if (board_x < 0 or board_x >= self.board_width or
                        board_y >= self.board_height):
                        return True
                    
                    # Check board collision
                    if board_y >= 0 and self.board[board_y][board_x]:
                        return True
        return False
    
    def _move(self, dx, dy):
        """Move piece"""
        if self.game_over:
            return
        
        new_x = self.piece_x + dx
        new_y = self.piece_y + dy
        
        if not self._check_collision(new_x, new_y):
            self.piece_x = new_x
            self.piece_y = new_y
            self._draw()
        elif dy > 0:  # Moving down and collided
            self._lock_piece()
    
    def _rotate(self):
        """Rotate piece"""
        if self.game_over:
            return
        
        # Transpose and reverse
        rotated = list(zip(*self.current_piece[::-1]))
        rotated = [[cell for cell in row] for row in rotated]
        
        if not self._check_collision(self.piece_x, self.piece_y, rotated):
            self.current_piece = rotated
            self._draw()
    
    def _instant_drop(self):
        """Drop piece instantly"""
        if self.game_over:
            return
        
        while not self._check_collision(self.piece_x, self.piece_y + 1):
            self.piece_y += 1
        
        self._lock_piece()
    
    def _lock_piece(self):
        """Lock piece to board"""
        for py, row in enumerate(self.current_piece):
            for px, cell in enumerate(row):
                if cell:
                    board_y = self.piece_y + py
                    board_x = self.piece_x + px
                    if board_y >= 0:
                        self.board[board_y][board_x] = self.current_color
        
        # Clear lines
        lines = self._clear_lines()
        if lines:
            self.lines_cleared += lines
            self.score += [0, 100, 300, 500, 800][min(lines, 4)] * self.level
            self.level = 1 + self.lines_cleared // 10
            self._update_labels()
            self._send_score_update()
        
        self._spawn_piece()
        self._draw()
    
    def _clear_lines(self):
        """Clear completed lines"""
        lines_cleared = 0
        y = self.board_height - 1
        
        while y >= 0:
            if all(self.board[y]):
                del self.board[y]
                self.board.insert(0, [None for _ in range(self.board_width)])
                lines_cleared += 1
            else:
                y -= 1
        
        return lines_cleared
    
    def _update_labels(self):
        """Update score labels"""
        self.score_label.config(text=str(self.score))
        self.level_label.config(text=str(self.level))
        self.lines_label.config(text=str(self.lines_cleared))
        
        # Update multiplayer scoreboard
        if self.is_group:
            self._update_scoreboard()
    
    def _draw(self):
        """Draw the game board"""
        self.canvas.delete("piece")
        
        # Draw locked pieces
        for y, row in enumerate(self.board):
            for x, color in enumerate(row):
                if color:
                    self._draw_cell(x, y, color)
        
        # Draw current piece
        if self.current_piece:
            for py, row in enumerate(self.current_piece):
                for px, cell in enumerate(row):
                    if cell:
                        self._draw_cell(self.piece_x + px, 
                                      self.piece_y + py,
                                      self.current_color, "piece")
    
    def _draw_cell(self, x, y, color, tag=""):
        """Draw a cell"""
        x1 = x * self.cell_size
        y1 = y * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size
        
        self.canvas.create_rectangle(x1, y1, x2, y2, 
                                     fill=color, outline=COLORS['grid'],
                                     tags=tag)
    
    def _game_loop(self):
        """Main game loop"""
        if not self.game_over:
            self._move(0, 1)
            delay = max(100, 500 - (self.level - 1) * 50)
            self.window.after(delay, self._game_loop)
    
    def _send_score_update(self):
        """Send score update to other players"""
        try:
            msg = json.dumps({
                'type': 'score_update',
                'player': self.player_name,
                'score': self.score,
                'level': self.level
            })
            self.send_callback(f"GAME_SCORE:{msg}")
        except Exception as e:
            print(f"[ERROR] Failed to send score: {e}")
    
    def _send_game_over(self):
        """Send game over notification"""
        try:
            msg = json.dumps({
                'type': 'game_over',
                'player': self.player_name,
                'final_score': self.score
            })
            self.send_callback(f"GAME_OVER:{msg}")
        except Exception as e:
            print(f"[ERROR] Failed to send game over: {e}")
    
    def receive_move(self, message):
        """Receive move from other player"""
        try:
            if message.startswith("GAME_SCORE:"):
                data = json.loads(message[11:])
                player = data.get('player')
                score = data.get('score', 0)
                
                if player and player != self.player_name:
                    self.player_scores[player] = score
                    if self.is_group:
                        self._update_scoreboard()
            
            elif message.startswith("GAME_OVER:"):
                data = json.loads(message[10:])
                player = data.get('player')
                final_score = data.get('final_score', 0)
                
                if player and player != self.player_name:
                    self.player_scores[player] = final_score
                    if self.is_group:
                        self._update_scoreboard()
                        
        except Exception as e:
            print(f"[ERROR] Failed to receive move: {e}")


# Test mode
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    
    def dummy_send(msg):
        print(f"Send: {msg}")
    
    game = TetrisGame(root, dummy_send, "TestPlayer", is_group=True)
    
    # Simulate other players for testing
    game.player_scores = {
        "TestPlayer": 0,
        "Alice": 150,
        "Bob": 300
    }
    game._update_scoreboard()
    
    root.mainloop()