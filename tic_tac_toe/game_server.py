import random
import socket
from enum import IntEnum
from typing import Optional

from tic_tac_toe import messages, DEFAULT_PORT
from tic_tac_toe.logger import get_logger
from tic_tac_toe.messages import Result, GameEnded
from tic_tac_toe.socket_handler import SocketHandler


class GameServer:
    logger = get_logger("game-server", split=" ")

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect((host, port))
        self.socket_handler = SocketHandler(conn)
        self.players = None
        self.game_state = [None, None, None, None, None, None, None, None, None]

    def get_winner(self) -> Optional[str]:
        crosses = [
            [0, 1, 2],
            [3, 4, 5],
            [6, 7, 8],
            [0, 4, 8],
            [2, 4, 6],
            [0, 3, 6],
            [1, 4, 7],
            [2, 5, 8],
        ]
        for cross in crosses:
            if self.game_state[cross[0]] == self.game_state[cross[1]] == self.game_state[cross[2]]:
                if self.game_state[cross[0]]:
                    self.logger.info('%s won', self.game_state[cross[0]])
                    return self.game_state[cross[0]]
        if None in self.game_state:
            self.logger.info("No one")
            return None
        self.logger.info("TIE")
        return 'TIE'

    def move(self):
        self.logger.info("Player %s can move now", self.players[0])
        self.socket_handler.send_message(
            messages.YouCanMove(self.players[0]), False
        )

    def start(self):
        self.logger.info("Start game server")
        acc = self.socket_handler.send_message(
            messages.HandShake(messages.SocketType.GAME), True
        )
        self.logger.info("Acc is %d %s", acc.result, acc.text)
        while True:
            message = self.socket_handler.get_next_message()
            if message.message_type != messages.MessageType.ACC:
                self.socket_handler.send_acc(message.message_id)
            self.logger.info("New message type %s %s", message.message_type, message)
            if message.message_type == messages.MessageType.GAME_START:
                self.logger.info("Game started %s vs %s", *message.opponents)
                self.players = message.opponents[0], message.opponents[1]
                if self.players[0] == 'BOT':
                    self.players = self.players[1], self.players[0]
                self.move()
            elif message.message_type == messages.MessageType.SEND_MESSAGE:
                self.socket_handler.send_message(message, False)
            elif message.message_type == messages.MessageType.RECONNECTED:
                self.logger.info("Player %s reconnected", message.user)
                if len(self.players):
                    self.logger.info("Game not finished")
                    self.socket_handler.send_message(
                        Result(self.game_state, self.get_winner()),
                        False
                    )
                    if self.players[0] == message.user:
                        self.move()
            elif message.message_type == messages.MessageType.MAKE_MOVE:
                self.logger.info("Move made at %s", message.pos)
                if self.game_state[message.pos]:
                    self.logger.info("Cell is not empty")
                    self.socket_handler.send_acc(message.message_id, *messages.Codes.INVALID_MOVE)
                else:
                    self.game_state[message.pos] = self.players[0]
                    self.players = self.players[1], self.players[0]


                    if self.players[0] == 'BOT' and self.get_winner() is None:
                        self.logger.info("Bot making move")
                        while True:
                            pos = random.randint(0, 8)
                            if self.game_state[pos] is None:
                                break
                        self.logger.info("Bot hit %d", pos)
                        self.game_state[pos] = 'BOT'
                        self.players = self.players[1], self.players[0]
                        self.socket_handler.send_message(
                            Result(self.game_state, self.get_winner()),
                            False
                        )
                    else:
                        self.socket_handler.send_message(
                            Result(self.game_state, self.get_winner()),
                            False
                        )
                    if self.get_winner() is None:
                        self.move()
            if self.get_winner():
                self.logger.info("Game ended")
                self.socket_handler.send_message(
                    GameEnded(self.get_winner()), False
                )
                self.game_state = [None, None, None, None, None, None, None, None, None]
                self.players = None


if __name__ == "__main__":
    game = GameServer("localhost", DEFAULT_PORT)
    game.start()
