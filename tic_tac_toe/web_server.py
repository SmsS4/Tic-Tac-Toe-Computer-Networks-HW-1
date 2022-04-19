import socket
import threading
import time
from typing import Tuple, List, Optional

from tic_tac_toe.logger import get_logger
from tic_tac_toe.messages import (
    Message,
    get_message,
    HandShake,
    SocketType,
    Acc,
    serialize,
    GameType,
    MessageType,
    RequestNewGame,
    Codes,
    GameFound,
)
from tic_tac_toe.models import GameServerData, User
from tic_tac_toe.socket_handler import SocketHandler


class WebServer:
    logger = get_logger("web-server", split=" ")
    HOST = "127.0.0.1"
    PORT = 7000

    def __init__(self):
        self.logger.info("New webserver on port %d", self.PORT)
        self.server_socket = None
        self.sockets_thread = threading.Thread(target=self.handle_sockets)
        self.game_servers: List[GameServerData] = []
        self.users: List[User] = []

    def handle_game_server_socket(self, socket_handler: SocketHandler):
        self.logger.info("New game socket")
        self.game_servers.append(GameServerData(socket_handler, 0))
        while True:
            message = socket_handler.get_next_message()
            self.logger.info("Game server said %s %s", message.message_type, message)

    def get_empty_server(
        self, game_type: GameType, block: bool
    ) -> Optional[GameServerData]:
        while True:
            if game_type == GameType.MULTI_PLAYER:
                for game_server_data in self.game_servers:
                    if game_server_data.number_of_users == 1:
                        game_server_data.number_of_users += 1
                        return game_server_data
                for game_server_data in self.game_servers:
                    if game_server_data.number_of_users == 0:
                        game_server_data.number_of_users += 1
                        return game_server_data
            else:
                for game_server_data in self.game_servers:
                    if game_server_data.number_of_users == 0:
                        game_server_data.number_of_users += 2
                        bot = User(None, None, "BOT", is_bot=True)
                        game_server_data.users.append(bot)
                        return game_server_data
            if not block:
                return None
            time.sleep(1)

    def new_game(self, user: User, message: RequestNewGame):
        self.logger.info("New game")
        user.socket_handler.send_acc(message.message_id, *Codes.WAIT_FOR_EMPTY_SERVER)
        self.logger.info("Wait for game")
        user.game_server = self.get_empty_server(message.game_type, True)
        user.game_server.users.append(user)
        self.logger.info("Found game")
        opp = (
            user.game_server.users[0]
            if user.game_server.users[0] != user.username
            else user.game_server.users[1]
        )
        self.logger.info("Hmmm")
        acc = user.socket_handler.send_message(
            GameFound(opp.username), wait_for_acc=True
        )
        self.logger.info("Hmmm")
        if acc is None:
            self.logger.error("User disconnected")
            return
        else:
            self.logger.info("Acc game found %d %s", acc.result, acc.text)

    def handle_client_socket(self, socket_handler: SocketHandler):
        user = User(socket_handler, None)
        self.users.append(user)
        self.logger.info("New client")
        while True:
            message = socket_handler.get_next_message()
            self.logger.info("Client said %s %s", message.message_type, message)
            if message.message_type == MessageType.NEW_GAME_REQUEST:
                self.new_game(user, message)
            else:
                user.game_server.socket_handler.send_message(message, False)

    def handle_socket(self, socket_handler: SocketHandler):
        message = socket_handler.get_next_message()
        self.logger.info("Handle socket %s", message)
        if message.socket_type == SocketType.GAME:
            socket_handler.send_acc(message.message_id)
            self.handle_game_server_socket(socket_handler)
        elif message.socket_type == SocketType.CLIENT:
            socket_handler.send_acc(message.message_id)
            self.handle_client_socket(socket_handler)
        else:
            self.logger.error("Unexpected socket type %s", message)
            exit(3)

    def handle_sockets(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            self.server_socket = s
            s.bind((self.HOST, self.PORT))
            s.listen()
            while True:
                conn, addr = s.accept()
                sh = SocketHandler(conn)
                self.logger.info("New socket connection by %s", addr)
                threading.Thread(target=self.handle_socket, args=(sh,)).start()

    def start(self):
        self.logger.info("Web server started")
        self.sockets_thread.start()
        while True:
            print("Commands\n/users")
            cmd = input().strip()
            if cmd == "/exit":
                self.server_socket.close()
                self.logger.warning("Exiting...")
                exit(0)
            if cmd == "/users":
                pass


if __name__ == "__main__":
    ws = WebServer()
    ws.start()
