import sys
import socket
import struct
import random

class TicTacToeClient:
    def __init__(self, server_ip, port):
        self.server_ip = server_ip
        self.port = port
        self.game_id = random.getrandbits(24)  # Randomized game ID
        self.player_symbol = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.current_state = 0
        self.message_id = 0  # 8-bit serial message ID

    def create_message(self, game_flags, text_message=""):
        header = struct.pack("!I", (self.game_id << 8) | self.message_id)[:3] + struct.pack("!H", game_flags)
        game_state_bytes = struct.pack("!H", self.current_state)
        utf8_message = text_message.encode("utf-8")
        return header + game_state_bytes + utf8_message

    def parse_response(self, data):
        game_flags = struct.unpack("!H", data[3:5])[0]
        game_state = struct.unpack("!H", data[5:7])[0]
        message = data[7:].decode("utf-8") if len(data) > 7 else ""
        return game_flags, game_state, message

    def print_board(self, game_state):
        symbols = {0: ' ', 1: 'X', 2: 'O'}
        board = []
        for i in range(9):
            pos = 16 - (i * 2)
            value = (game_state >> pos) & 0b11
            board.append(symbols[value])
        
        print("\nGame Board:           Current Game:")
        print(f" 1 | 2 | 3             {board[0]} | {board[1]} | {board[2]} ")
        print("---+---+---           ---+---+---")
        print(f" 4 | 5 | 6             {board[3]} | {board[4]} | {board[5]} ")
        print("---+---+---           ---+---+---")
        print(f" 7 | 8 | 9             {board[6]} | {board[7]} | {board[8]} \n")

    def get_move(self):
        while True:
            try:
                move = int(input("Enter your move (1-9): ")) - 1
                if 0 <= move <= 8:
                    pos = 16 - (move * 2)
                    if (self.current_state >> pos) & 0b11 == 0:
                        return move
                    print("That position is already taken. Try again.")
                else:
                    print("Please enter a number between 1 and 9.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def update_game_state(self, move):
        pos = 16 - (move * 2)
        symbol_value = 1 if self.player_symbol == 'X' else 2
        return self.current_state | (symbol_value << pos)

    def play_game(self):
        player_name = input("Enter your name: ")
        
        # Initial message to server
        initial_message = self.create_message(0, player_name)
        self.sock.sendto(initial_message, (self.server_ip, self.port))
        
        game_active = True
        while game_active:
            # Receive response from server
            data, _ = self.sock.recvfrom(1024)
            game_flags, game_state, message = self.parse_response(data)
            
            # Update local state
            self.current_state = game_state
            
            # Print server message and board
            print(message)
            self.print_board(game_state)
            
            # Check game ending conditions
            if game_flags & 0b11100:  # Check bits 2, 3, and 4 for game end
                game_active = False
                continue
            
            # Set player symbol if not already set
            if self.player_symbol is None:
                self.player_symbol = 'X' if game_flags & 1 else 'O'
                print(f"You are playing as {self.player_symbol}")
            
            # Player's turn
            if (game_flags & 1 and self.player_symbol == 'X') or (game_flags & 2 and self.player_symbol == 'O'):
                move = self.get_move()
                self.current_state = self.update_game_state(move)
                
                # Increment and wrap the message ID
                self.message_id = (self.message_id + 1) % 256
                
                move_message = self.create_message(self.current_state)
                self.sock.sendto(move_message, (self.server_ip, self.port))

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 client.py <server_ip> <port>")
        sys.exit(1)

    server_ip = sys.argv[1]
    port = int(sys.argv[2])
    
    client = TicTacToeClient(server_ip, port)
    client.play_game()

if __name__ == "__main__":
    main()
