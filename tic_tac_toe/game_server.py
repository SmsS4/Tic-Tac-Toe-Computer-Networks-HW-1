import socket

from tic_tac_toe import messages
from tic_tac_toe.logger import get_logger
from tic_tac_toe.socket_handler import SocketHandler


class GameServer:
    logger = get_logger("game-server", split=" ")

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((host, port))
        self.socket_handler = SocketHandler(conn)

    def new_game(self):
        pass

    def start(self):
        self.logger.info("Start game server")
        acc = self.socket_handler.send_message(
            messages.HandShake(messages.SocketType.GAME), True
        )
        self.logger.info("Acc is %d %s", acc.result, acc.text)
        while True:
            message = self.socket_handler.get_next_message()
            pass


if __name__ == "__main__":
    game = GameServer("localhost", 7000)
    game.start()
