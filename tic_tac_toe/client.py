import socket

from tic_tac_toe.logger import get_logger
from tic_tac_toe import messages
from tic_tac_toe.menu_handler import handle_menu
from tic_tac_toe.messages import Codes
from tic_tac_toe.socket_handler import SocketHandler


class Client:
    logger = get_logger("Client", split=" ")
    DELIMITER = b";"

    def __init__(self, host: str, port: int):
        self.logger.info("New client connecting to %s:%d", host, port)
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((host, port))
        self.socket_handler = SocketHandler(conn)
        self.logger.info("Connected")

    def new_game(self):
        self.logger.info("New game")
        while True:
            message = self.socket_handler.get_next_message()
            print(message)
            if message.message_type == messages.MessageType.GAME_FOUND:
                print(f"Game found vs {message.opponent}")

    def start(self):
        acc = self.socket_handler.send_message(
            messages.HandShake(messages.SocketType.CLIENT), True
        )
        self.logger.info("Acc is %s", acc)
        if acc.is_ok():
            print("Connected")
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
                acc = self.socket_handler.send_message(message, True)
                print(acc.text)
                self.new_game()
            elif cmd == "exit":
                pass


if __name__ == "__main__":
    client = Client("127.0.0.1", 7000)
    client.start()
