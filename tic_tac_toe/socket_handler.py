import socket
import threading
import time
from logging import ERROR
from typing import List, Dict, Optional

from tic_tac_toe.messages import Message, get_message, Acc, serialize, MessageType
from tic_tac_toe.logger import get_logger


class SocketHandler:
    logger = get_logger("socket", split=" ", level=ERROR)
    CHUNK_SIZE = 1024
    DELIMITER = b";"

    def __init__(self, conn: socket.socket):
        self.lock = threading.Lock()
        self.socket = conn
        self.buffer: List[Message] = []
        self.accs: Dict[str, Acc] = {}
        self.remain = b""

    def fill_buffer(self) -> bool:
        data = self.socket.recv(self.CHUNK_SIZE)
        if not data:
            return False
        self.remain += data
        raw_messages = self.remain.split(self.DELIMITER)
        if len(raw_messages) and len(raw_messages[-1]):
            self.remain = raw_messages[-1]
            raw_messages = raw_messages[:-1]
        else:
            self.remain = b""
        if len(raw_messages) and not raw_messages[-1]:
            raw_messages = raw_messages[:-1]
        new_messages = list(map(get_message, raw_messages))
        for message in new_messages:
            if message.message_type == MessageType.ACC:
                self.accs[message.message_id] = message
        self.buffer.extend(new_messages)
        if len(raw_messages):
            self.logger.info("New messages %s remain: %s", raw_messages, self.remain)
            return True
        return False

    def get_next_message(self) -> Message:
        # self.lock.acquire()
        while True:
            if len(self.buffer):
                # self.lock.release()
                return self.buffer.pop(0)
            else:
                self.fill_buffer()
                time.sleep(0)
                continue

    def send_acc(
        self, message_id: str, result: int = 0, text: str = "OK"
    ) -> Optional[Acc]:
        return self.send_message(
            Acc(result=result, message_id=message_id, text=text), wait_for_acc=False
        )

    def send_message(
        self, message: Message, wait_for_acc: bool, timeout: int = 5
    ) -> Optional[Acc]:
        # self.lock.acquire()
        self.logger.info("Sending new message %s", message.message_type)
        self.socket.sendall(serialize(message) + self.DELIMITER)
        if not wait_for_acc:
            # self.lock.release()
            return
        cur = time.time()
        while message.message_id not in self.accs and (time.time() - cur) < timeout:
            self.fill_buffer()
        # self.lock.release()
        return self.accs.get(message.message_id, None)
