import tkinter as tk
from tkinter import messagebox
import random

# Configuration
CELL_SIZE = 20
BOARD_WIDTH = 15
BOARD_HEIGHT = 15

class PacmanGame:
    def __init__(self, master, send_func, opponent_name, my_role):
        self.master = master
        self.send_func = send_func
        self.opponent = opponent_name
        self.my_role = my_role # 'pacman' or 'ghost'
        
        self.window = tk.Toplevel(master)
        self.window.title(f"Pacman vs {opponent_name} ({self.my_role.upper()})")
        self.window.geometry(f"{BOARD_WIDTH*CELL_SIZE}x{BOARD_HEIGHT*CELL_SIZE + 50}")
        
        self.canvas = tk.Canvas(self.window, width=BOARD_WIDTH*CELL_SIZE, height=BOARD_HEIGHT*CELL_SIZE, bg="black")
        self.canvas.pack()
        
        self.score_label = tk.Label(self.window, text="Use Arrow Keys to Move", font=("Arial", 12))
        self.score_label.pack()

        # Game State
        self.pacman_pos = [1, 1]
        self.ghost_pos = [BOARD_WIDTH-2, BOARD_HEIGHT-2]
        self.coins = self.generate_coins()
        self.score = 0
        self.game_over = False

        # Controls
        self.window.bind("<KeyPress>", self.on_key_press)
        
        self.draw_board()

    def generate_coins(self):
        coins = []
        for _ in range(20):
            x = random.randint(1, BOARD_WIDTH-2)
            y = random.randint(1, BOARD_HEIGHT-2)
            if [x, y] not in coins:
                coins.append([x, y])
        return coins

    def draw_entity(self, pos, color, type="circle"):
        x, y = pos
        x1, y1 = x * CELL_SIZE, y * CELL_SIZE
        x2, y2 = x1 + CELL_SIZE, y1 + CELL_SIZE
        if type == "circle":
            self.canvas.create_oval(x1+2, y1+2, x2-2, y2-2, fill=color, outline="")
        else:
            self.canvas.create_rectangle(x1+2, y1+2, x2-2, y2-2, fill=color, outline="")

    def draw_board(self):
        if self.game_over: return
        self.canvas.delete("all")
        
        # Draw Coins
        for coin in self.coins:
            self.draw_entity(coin, "gold", "circle")
            
        # Draw Players
        self.draw_entity(self.pacman_pos, "yellow", "circle") # Pacman
        self.draw_entity(self.ghost_pos, "red", "rect")       # Ghost (Square)
        
        # UI Update
        role_txt = "PACMAN (You)" if self.my_role == 'pacman' else "GHOST (You)"
        self.score_label.config(text=f"{role_txt} | Score: {self.score}")

    def on_key_press(self, event):
        if self.game_over: return
        
        dx, dy = 0, 0
        if event.keysym == 'Up': dy = -1
        elif event.keysym == 'Down': dy = 1
        elif event.keysym == 'Left': dx = -1
        elif event.keysym == 'Right': dx = 1
        else: return

        # Validate Move (Simple boundary check)
        my_pos = self.pacman_pos if self.my_role == 'pacman' else self.ghost_pos
        new_x, new_y = my_pos[0] + dx, my_pos[1] + dy
        
        if 0 <= new_x < BOARD_WIDTH and 0 <= new_y < BOARD_HEIGHT:
            # Update local state
            if self.my_role == 'pacman':
                self.pacman_pos = [new_x, new_y]
                self.check_collisions()
            else:
                self.ghost_pos = [new_x, new_y]
                self.check_game_over()

            self.draw_board()
            # Send Move to Server: "GAME_MOVE:role:x:y"
            self.send_func(f"GAME_MOVE:{self.my_role}:{new_x}:{new_y}")

    def handle_incoming_move(self, role, x, y):
        # Update opponent position
        x, y = int(x), int(y)
        if role == 'pacman':
            self.pacman_pos = [x, y]
            if self.my_role == 'ghost': self.check_game_over() # I am ghost, check if I caught him
        else:
            self.ghost_pos = [x, y]
            if self.my_role == 'pacman': self.check_game_over() # I am pacman, check if I died
            
        self.draw_board()

    def check_collisions(self):
        # Only Pacman checks coin collections
        if self.pacman_pos in self.coins:
            self.coins.remove(self.pacman_pos)
            self.score += 10
            
        self.check_game_over()

    def check_game_over(self):
        if self.pacman_pos == self.ghost_pos:
            self.game_over = True
            winner = "Ghost"
            messagebox.showinfo("Game Over", f"{winner} Wins! Pacman was caught.")
            self.window.destroy()
        elif not self.coins:
            self.game_over = True
            winner = "Pacman"
            messagebox.showinfo("Game Over", f"{winner} Wins! All coins collected.")
            self.window.destroy()