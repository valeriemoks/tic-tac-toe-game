import socket
import struct
import random

class TicTacToeServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.games = {}  # Dictionary to store active games
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((host, port))

    def create_response(self, game_id, message_id, game_flags, game_state, text_message=""):
        header = struct.pack("!I", (game_id << 8) | message_id)[:3] + struct.pack("!H", game_flags)
        game_state_bytes = struct.pack("!H", game_state)
        utf8_message = text_message.encode("utf-8")
        return header + game_state_bytes + utf8_message

    def parse_request(self, data):
        game_id = struct.unpack("!I", data[:3] + b'\x00')[0] >> 8
        message_id = struct.unpack("!I", data[:3] + b'\x00')[0] & 0xFF  # Extract last 8 bits
        game_state = struct.unpack("!H", data[5:7])[0]
        message = data[7:].decode("utf-8") if len(data) > 7 else ""
        return game_id, message_id, game_state, message

    def check_winner(self, game_state):
        win_combinations = [
            0b110000000000000000, 0b000110000000000000, 0b000000110000000000,  # Rows
            0b100100100000000000, 0b010010010000000000, 0b001001001000000000,  # Columns
            0b100010001000000000, 0b001010100000000000  # Diagonals
        ]
        
        x_state = game_state & 0b101010101010101010
        x_state = (x_state | (x_state >> 1)) & 0b111111111000000000
        
        o_state = (game_state >> 1) & 0b101010101010101010
        o_state = (o_state | (o_state >> 1)) & 0b111111111000000000
        
        for combo in win_combinations:
            if (x_state & combo) == combo:
                return 1  # X wins
            if (o_state & combo) == combo:
                return 2  # O wins
        
        if bin(game_state).count('1') == 18:
            return 3  # Tie
        
        return 0  # Game continues

    def make_server_move(self, game_state):
        empty_positions = []
        for i in range(9):
            pos = 16 - (i * 2)
            if (game_state >> pos) & 0b11 == 0:
                empty_positions.append(i)
        
        if empty_positions:
            move = random.choice(empty_positions)
            pos = 16 - (move * 2)
            return game_state | (0b10 << pos)  # Server always plays as O
        return game_state

    def run(self):
        print(f"Server listening on {self.host}:{self.port}")
        while True:
            data, addr = self.sock.recvfrom(1024)
            game_id, message_id, game_state, message = self.parse_request(data)
            
            if game_id not in self.games:
                # New game
                self.games[game_id] = {
                    'addr': addr,
                    'player_name': message,
                    'game_state': 0
                }
                response_flags = 1  # Set X player to move
                response_message = f"Welcome {message}! You are X. Your move!"
            else:
                # Existing game
                game = self.games[game_id]
                response_flags = 0
                if game_state != game['game_state']:
                    game['game_state'] = game_state  # Update game state
                    winner = self.check_winner(game_state)
                    if winner == 1:
                        response_flags |= 0b100  # X wins
                        response_message = "X wins! Game over."
                    elif winner == 2:
                        response_flags |= 0b1000  # O wins
                        response_message = "O wins! Game over."
                    elif winner == 3:
                        response_flags |= 0b10000  # Tie
                        response_message = "It's a tie! Game over."
                    else:
                        game['game_state'] = self.make_server_move(game_state)
                        response_flags |= 2  # O's turn
                        response_message = "Server's turn."
                else:
                    response_message = "Invalid move. Try again."
            
            response = self.create_response(game_id, message_id, response_flags, game['game_state'], response_message)
            self.sock.sendto(response, addr)

def main():
    server = TicTacToeServer('0.0.0.0', 12345)
    server.run()

if __name__ == "__main__":
    main()
