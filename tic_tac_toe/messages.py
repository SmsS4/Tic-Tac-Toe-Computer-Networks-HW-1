import uuid
from dataclasses import dataclass
from enum import IntEnum
import json
from dataclasses import field
from itertools import count
from typing import List, Optional


class SocketType(IntEnum):
    GAME = 1
    CLIENT = 2


class MessageType(IntEnum):
    NONE = 0
    HAND_SHAKE = 1
    ACC = 2
    NEW_GAME_REQUEST = 3
    GAME_FOUND = 4
    WAIT_FOR_OPPONENT = 5
    MAKE_MOVE = 6
    RESULT = 7
    SEND_MESSAGE = 8
    STOP_PROXY = 9
    GAME_START = 10
    GAME_ENDED = 11
    YOU_CAN_MOVE = 12
    RECONNECTED = 13


class GameType(IntEnum):
    SINGLE_PLAYER = 1
    MULTI_PLAYER = 2


class Message:
    def __init__(self, message_type: MessageType, message_id: str = None):
        if message_id is None:
            message_id = str(uuid.uuid1())
        self.message_id = message_id
        self.message_type = message_type


class HandShake(Message):
    def __init__(
        self,
        socket_type: SocketType,
        username: Optional[str] = None,
        message_type: MessageType = MessageType.HAND_SHAKE,
        message_id: int = None,
    ):
        super().__init__(message_type, message_id)
        self.username = username
        self.socket_type = socket_type


class RequestNewGame(Message):
    def __init__(
        self,
        game_type: GameType,
        message_type: MessageType = MessageType.NEW_GAME_REQUEST,
        message_id: int = None,
    ):
        super().__init__(message_type, message_id)
        self.game_type = game_type


class GameFound(Message):
    def __init__(
        self,
        opponent: str,
        message_type: MessageType = MessageType.GAME_FOUND,
        message_id: int = None,
    ):
        super().__init__(message_type, message_id)
        self.opponent = opponent

class StartGame(Message):
    def __init__(
            self,
            opponents: List[str],
            message_type: MessageType = MessageType.GAME_START,
            message_id: int = None,
    ):
        super().__init__(message_type, message_id)
        self.opponents = opponents

class WaitForOpponent(Message):
    def __init__(
            self,
            message_type: MessageType = MessageType.WAIT_FOR_OPPONENT,
            message_id: int = None
    ):
        super().__init__(message_type, message_id)


class MakeMove(Message):
    def __init__(
        self,
            pos: int,
            message_type: MessageType = MessageType.MAKE_MOVE,
            message_id: int = None
    ):
        super().__init__(message_type, message_id)
        self.pos = pos


class StopProxy(Message):
    def __init__(
        self, message_type: MessageType = MessageType.STOP_PROXY, message_id: int = None
    ):
        super().__init__(message_type, message_id)

class YouCanMove(Message):
    def __init__(
            self,user:str, message_type: MessageType = MessageType.YOU_CAN_MOVE, message_id: int = None
    ):
        super().__init__(message_type, message_id)
        self.user = user

class PlayerReconnected(Message):
    def __init__(
            self,user:str, message_type: MessageType = MessageType.RECONNECTED, message_id: int = None
    ):
        super().__init__(message_type, message_id)
        self.user = user

class Result(Message):
    def __init__(
        self,
        game_state: List[Optional[str]],
        winner: Optional[str],
        message_type: MessageType = MessageType.RESULT,
        message_id: int = None
    ):
        super().__init__(message_type, message_id)
        self.game_state = game_state
        self.winner = winner

class GameEnded(Message):
    def __init__(
            self,
            winner: str,
            message_type: MessageType = MessageType.GAME_ENDED,
            message_id: int = None
    ):
        super().__init__(message_type, message_id)
        self.winner = winner

class Codes:
    OK = 0, "OK"
    WAIT_FOR_EMPTY_SERVER = 1, "wait for empty server"
    INVALID_MOVE = 3, "cell is invalid"
    IN_GAME = 4, "You were in game"

class Acc(Message):
    def __init__(
        self,
        result: int,
        text: str,
        message_type: MessageType = MessageType.ACC,
        message_id: int = None,
    ):
        super().__init__(message_type, message_id)
        self.result = result
        self.text = text
    def in_game(self) -> bool:
        return self.result == Codes.IN_GAME[0]
    def is_ok(self) -> bool:
        return self.result == Codes.OK[0]
class SendMessage(Message):
    def __init__(
        self,
        text: str,
        target: str,
        message_type: MessageType = MessageType.SEND_MESSAGE,
        message_id: int = None,
    ):
        super().__init__(message_type, message_id)
        self.text = text
        self.target = target


messages_types = {
    MessageType.HAND_SHAKE: HandShake,
    MessageType.ACC: Acc,
    MessageType.NEW_GAME_REQUEST: RequestNewGame,
    MessageType.WAIT_FOR_OPPONENT: WaitForOpponent,
    MessageType.MAKE_MOVE: MakeMove,
    MessageType.RESULT: Result,
    MessageType.STOP_PROXY: StopProxy,
    MessageType.GAME_FOUND: GameFound,
    MessageType.GAME_START: StartGame,
    MessageType.GAME_ENDED: GameEnded,
    MessageType.YOU_CAN_MOVE: YouCanMove,
    MessageType.SEND_MESSAGE: SendMessage,
    MessageType.RECONNECTED: PlayerReconnected,
}


def serialize(msg: Message) -> bytes:
    return json.dumps(msg, default=lambda x: x.__dict__).encode()


def get_message(data: bytes) -> Message:
    json_data = json.loads(data)
    return messages_types[json_data["message_type"]](**json_data)
