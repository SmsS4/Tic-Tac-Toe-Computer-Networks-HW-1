from typing import Tuple, List


def handle_menu(options: List[Tuple]) -> str:
    while True:
        cmd = input("\n".join([f"/{opt[0]} :: {opt[1]}" for opt in options]) + "\n")
        if not cmd:
            continue
        if cmd[0] != "/":
            continue
        cmd = cmd[1:]
        for opt in options:
            if cmd == opt[0]:
                return cmd
        continue
