import tkinter as tk
from tkinter import messagebox

class TicTacGame(tk.Toplevel):
    def __init__(self, parent, send_callback):
        super().__init__(parent)
        self.title("Tic-Tac-Toe")
        self.geometry("300x350")
        self.send_callback = send_callback # Function to send msg to server
        
        self.turn = 'X'
        self.buttons = {}
        self.board = [" "]*9
        self.game_active = True
        
        self.create_widgets()
        
    def create_widgets(self):
        frame = tk.Frame(self)
        frame.pack(pady=10)
        
        # Create 3x3 Grid
        for i in range(9):
            btn = tk.Button(frame, text=" ", font=('Arial', 20), width=4, height=2,
                            command=lambda idx=i: self.on_click(idx))
            btn.grid(row=i//3, column=i%3)
            self.buttons[i] = btn
            
        reset_btn = tk.Button(self, text="Quit Game", command=self.destroy)
        reset_btn.pack(pady=10)

    def on_click(self, idx):
        if self.board[idx] == " " and self.game_active:
            # Send move to opponent via chat protocol
            # Protocol: GAME_MOVE:index
            self.send_callback(f"GAME_MOVE:{idx}")
            
            # Optimistically update our board (optional, but feels faster)
            # Alternatively wait for server echo. Here we wait for logic to update.

    def update_board(self, idx, player):
        """Called when a move message is received from the network"""
        if self.board[idx] == " ":
            self.board[idx] = player
            self.buttons[idx].config(text=player, state="disabled")
            self.check_winner()
            
            # Toggle turn tracker (for local logic if needed)
            self.turn = 'O' if self.turn == 'X' else 'X'

    def check_winner(self):
        wins = [(0,1,2), (3,4,5), (6,7,8), # Rows
                (0,3,6), (1,4,7), (2,5,8), # Cols
                (0,4,8), (2,4,6)]          # Diags
                
        for a,b,c in wins:
            if self.board[a] == self.board[b] == self.board[c] and self.board[a] != " ":
                self.game_active = False
                winner = self.board[a]
                color = "green" if winner == "X" else "blue"
                for i in [a,b,c]:
                    self.buttons[i].config(bg=color)
                messagebox.showinfo("Game Over", f"Player {winner} wins!")
                return

        if " " not in self.board:
            self.game_active = False
            messagebox.showinfo("Game Over", "It's a Draw!")