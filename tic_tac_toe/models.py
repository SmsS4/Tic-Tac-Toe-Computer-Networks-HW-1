from dataclasses import dataclass, field
import socket
from typing import Optional, List

import names

from tic_tac_toe.socket_handler import SocketHandler


@dataclass
class GameServerData:
    socket_handler: SocketHandler
    number_of_users: int
    users: List["User"] = field(default_factory=list)


@dataclass
class User:
    socket_handler: SocketHandler
    game_server: Optional[GameServerData]
    username: str = field(default_factory=names.get_last_name)
    is_bot: bool = False
