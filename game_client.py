"""
game_client.py - Tic-Tac-Toe Game Client
Implements a graphical Tic-Tac-Toe game that communicates through the chat socket
(Will be replaced with Pac-Man in Phase 3)
"""

import tkinter as tk
from tkinter import messagebox

class TicTacGame:
    """Tic-Tac-Toe game GUI that uses the existing chat socket"""
    
    def __init__(self, parent, send_callback, peer_name):
        """
        Initialize the game window
        
        Args:
            parent: Parent tkinter window
            send_callback: Function to send messages through chat socket
            peer_name: Name of the opponent
        """
        self.parent = parent
        self.send_callback = send_callback
        self.peer_name = peer_name
        
        # Game state
        self.board = ['' for _ in range(9)]
        self.current_player = 'X'
        self.my_symbol = None
        self.game_active = False
        
        # Create game window
        self.window = tk.Toplevel(parent)
        self.window.title(f"Tic-Tac-Toe vs {peer_name}")
        self.window.geometry("400x450")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Status label
        self.status_label = tk.Label(
            self.window, 
            text="Waiting to start...", 
            font=("Arial", 14),
            pady=10
        )
        self.status_label.pack()
        
        # Game board frame
        self.board_frame = tk.Frame(self.window)
        self.board_frame.pack(pady=20)
        
        # Create 3x3 grid of buttons
        self.buttons = []
        for i in range(9):
            row = i // 3
            col = i % 3
            btn = tk.Button(
                self.board_frame,
                text='',
                font=("Arial", 24, "bold"),
                width=5,
                height=2,
                command=lambda idx=i: self.on_cell_click(idx)
            )
            btn.grid(row=row, column=col, padx=5, pady=5)
            self.buttons.append(btn)
        
        # Control buttons
        control_frame = tk.Frame(self.window)
        control_frame.pack(pady=10)
        
        self.start_btn = tk.Button(
            control_frame,
            text="Start Game",
            font=("Arial", 12),
            command=self.start_game
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.reset_btn = tk.Button(
            control_frame,
            text="Reset",
            font=("Arial", 12),
            command=self.reset_game,
            state=tk.DISABLED
        )
        self.reset_btn.pack(side=tk.LEFT, padx=5)
        
    def start_game(self):
        """Send game start request to opponent"""
        self.send_game_message("GAME_START")
        self.my_symbol = 'X'
        self.game_active = True
        self.status_label.config(text="Your turn (X)")
        self.start_btn.config(state=tk.DISABLED)
        self.reset_btn.config(state=tk.NORMAL)
        
    def reset_game(self):
        """Reset the game board"""
        self.board = ['' for _ in range(9)]
        self.current_player = 'X'
        self.game_active = True
        
        for btn in self.buttons:
            btn.config(text='', state=tk.NORMAL, bg='SystemButtonFace')
        
        if self.my_symbol == 'X':
            self.status_label.config(text="Your turn (X)")
        else:
            self.status_label.config(text="Opponent's turn")
            
        self.send_game_message("GAME_RESET")
    
    def on_cell_click(self, idx):
        """Handle cell click event"""
        if not self.game_active:
            messagebox.showwarning("Game Not Started", "Please start the game first!")
            return
            
        if self.board[idx] != '':
            messagebox.showwarning("Invalid Move", "Cell already occupied!")
            return
            
        if self.current_player != self.my_symbol:
            messagebox.showwarning("Not Your Turn", "Wait for opponent's move!")
            return
        
        # Make move
        self.make_move(idx, self.my_symbol)
        
        # Send move to opponent
        self.send_game_message(f"GAME_MOVE:{idx}")
        
        # Check for win/draw
        if self.check_winner():
            self.end_game(f"You win!")
        elif self.is_board_full():
            self.end_game("Draw!")
        else:
            # Switch turn
            self.current_player = 'O' if self.current_player == 'X' else 'X'
            self.status_label.config(text="Opponent's turn")
    
    def make_move(self, idx, symbol):
        """Update board with move"""
        self.board[idx] = symbol
        self.buttons[idx].config(text=symbol, state=tk.DISABLED)
        
        # Color code the symbols
        if symbol == 'X':
            self.buttons[idx].config(fg='blue')
        else:
            self.buttons[idx].config(fg='red')
    
    def receive_move(self, move_data):
        """Process move received from opponent"""
        if move_data == "GAME_START":
            self.my_symbol = 'O'
            self.game_active = True
            self.status_label.config(text="Opponent's turn")
            self.start_btn.config(state=tk.DISABLED)
            self.reset_btn.config(state=tk.NORMAL)
            return
            
        if move_data == "GAME_RESET":
            self.reset_game()
            return
        
        if not move_data.startswith("GAME_MOVE:"):
            return
            
        try:
            idx = int(move_data.split(":")[1])
            opponent_symbol = 'O' if self.my_symbol == 'X' else 'X'
            
            # Make opponent's move
            self.make_move(idx, opponent_symbol)
            
            # Check for win/draw
            if self.check_winner():
                self.end_game(f"Opponent wins!")
            elif self.is_board_full():
                self.end_game("Draw!")
            else:
                # Switch turn back to player
                self.current_player = self.my_symbol
                self.status_label.config(text=f"Your turn ({self.my_symbol})")
                
        except (ValueError, IndexError) as e:
            print(f"[ERROR] Processing move: {e}")
    
    def check_winner(self):
        """Check if there's a winner"""
        # Win conditions: rows, columns, diagonals
        win_conditions = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]              # Diagonals
        ]
        
        for condition in win_conditions:
            if (self.board[condition[0]] != '' and
                self.board[condition[0]] == self.board[condition[1]] == self.board[condition[2]]):
                # Highlight winning combination
                for idx in condition:
                    self.buttons[idx].config(bg='lightgreen')
                return True
        return False
    
    def is_board_full(self):
        """Check if board is full (draw condition)"""
        return all(cell != '' for cell in self.board)
    
    def end_game(self, message):
        """End the game and show result"""
        self.game_active = False
        self.status_label.config(text=message)
        
        # Disable all buttons
        for btn in self.buttons:
            btn.config(state=tk.DISABLED)
    
    def send_game_message(self, message):
        """Send game message through chat socket"""
        self.send_callback(message)
    
    def on_close(self):
        """Handle window close"""
        if self.game_active:
            if messagebox.askokcancel("Quit Game", "Game in progress. Are you sure you want to quit?"):
                self.send_game_message("GAME_QUIT")
                self.window.destroy()
        else:
            self.window.destroy()