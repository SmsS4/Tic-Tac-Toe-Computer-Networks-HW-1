import socket
import threading
import time
from logging import ERROR
from typing import Optional

from tic_tac_toe.logger import get_logger
from tic_tac_toe import messages, DEFAULT_PORT
from tic_tac_toe.menu_handler import handle_menu
from tic_tac_toe.messages import Codes
from tic_tac_toe.socket_handler import SocketHandler


class Client:
    logger = get_logger("Client", split=" ", level=ERROR)
    DELIMITER = b";"
    WIDTH = 16

    def __init__(self, host: str, port: int, username: Optional[str] = None):
        self.username = username
        self.logger.info("New client connecting to %s:%d", host, port)
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((host, port))
        self.socket_handler = SocketHandler(conn)
        self.logger.info("Connected")
        self.game_thread = threading.Thread(target=self.new_game)
        self.game_state = [None, None, None, None, None, None, None, None, None]
        self.game = None
        self.wait_for_result = threading.Event()
        self.my_turn = False
        self.single_player = False

    def get_cell(self, value):
        return (' ' if value is None else value).rjust(self.WIDTH // 2).ljust(self.WIDTH // 2)

    def print_game_state(self):
        raw_cells = []
        for i in range(9):
            if self.game_state[i]:
                raw_cells.append(self.game_state[i])
            else:
                raw_cells.append(str(i))
        cells = list(map(self.get_cell, raw_cells))
        print(*cells[:3], sep=' | ')
        print('-' * self.WIDTH * 4)
        print(*cells[3:6], sep=' | ')
        print('-' * self.WIDTH * 4)
        print(*cells[6:9], sep=' | ')

    def new_game(self):
        self.logger.info("New game")
        while True:
            message = self.socket_handler.get_next_message()
            if message.message_type != messages.MessageType.ACC:
                self.socket_handler.send_acc(message.message_id)
            if message.message_type == messages.MessageType.GAME_FOUND:
                print(f"Game found vs {message.opponent}")
                self.print_game_state()
                self.game = True
            elif message.message_type == messages.MessageType.WAIT_FOR_OPPONENT:
                print('Wait for opponent')
            elif message.message_type == messages.MessageType.GAME_ENDED:
                print(f"Game ended {message.winner} won")
                self.game = False
                break
            elif message.message_type == messages.MessageType.RESULT:
                self.game = True
                self.game_state = message.game_state
                if message.winner:
                    print('Winner is', message.winner)
                self.print_game_state()
                if message.winner is not None:
                    self.game = False
                self.wait_for_result.set()
            elif message.message_type == messages.MessageType.YOU_CAN_MOVE:
                print('Its your turn')
                self.my_turn = True
            elif message.message_type == messages.MessageType.SEND_MESSAGE:
                print(f'Opponent said\n{message.text}')

    def game_menu(self):
        self.game_thread.start()
        while self.game is None:
            time.sleep(0.1)
            continue

        while True:
            options = []
            options.append(("move", "Make move"), )
            options.append(("reconnect_test", "Reconnect"), )
            if not self.single_player:
                options.append(("msg", "Send message"))

            cmd = handle_menu(options)
            if not self.game:
                break
            if cmd == 'reconnect_test':
                self.socket_handler.socket.close()
                client = Client("127.0.0.1", DEFAULT_PORT, self.username)
                client.start()
                exit(0)
            if cmd == "msg":
                text = input('Enter your message\n')
                self.socket_handler.send_message(messages.SendMessage(text, ''), False)
                print('Message sent')
            if cmd == 'move':
                if not self.my_turn:
                    print('Its not your turn')
                    continue
                cmd = input('enter empty cell\n')
                if not cmd.isnumeric():
                    print('Enter valid number')
                    continue
                cmd = int(cmd)
                if not (0 <= cmd < 9):
                    print('Enter number between 0 and 8')
                    continue
                if self.game_state[cmd] is not None:
                    print('Enter empty cell')
                    continue
                self.logger.info("Making move at %s", cmd)
                self.my_turn = False
                self.wait_for_result = threading.Event()
                self.socket_handler.send_message(messages.MakeMove(cmd), False)
                self.wait_for_result.wait()
                print('after wait', self.game)
                if not self.game:
                    break
        self.game = None

    def start(self):
        acc = self.socket_handler.send_message(
            messages.HandShake(messages.SocketType.CLIENT, self.username), True
        )
        self.logger.info("Acc is %s", acc)
        if self.username and acc.in_game():
            print('You were in game')
            self.single_player = False
            self.game_menu()
        if acc.is_ok():
            print("Connected")
            self.username = acc.text.split()[-1]
            print(acc.text)
        else:
            print("Internal error")
            exit(0)

        while True:
            cmd = handle_menu(
                [
                    ("new", "New game"),
                    ("exit", "Exit"),
                ]
            )
            if cmd == "new":
                cmd = handle_menu(
                    [
                        ("mp", "Multiplayer"),
                        ("sp", "Singleplayer"),
                    ]
                )
                message = messages.RequestNewGame(
                    messages.GameType.SINGLE_PLAYER
                    if cmd == "sp"
                    else messages.GameType.MULTI_PLAYER
                )
                if cmd == 'sp':
                    self.single_player = True
                else:
                    self.single_player = False
                acc = self.socket_handler.send_message(message, True)
                print(acc.text)
                self.game_menu()
            elif cmd == "exit":
                print('Exiting...')
                exit(0)


if __name__ == "__main__":
    client = Client("127.0.0.1", DEFAULT_PORT)
    client.start()
