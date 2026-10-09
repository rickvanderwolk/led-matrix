#!/usr/bin/env python3

import json
import sys
import threading
import time
import websocket
from core import Matrix, BLACK

matrix = Matrix()


def handle_message(payload):
    message = json.loads(payload)
    data = message.get("data")
    reset = message.get("reset", True)
    default_color = message.get("color", [0, 255, 0])
    squares = [BLACK] * matrix.count if reset else [matrix[i] for i in range(matrix.count)]

    if isinstance(data, dict):
        data = [data]

    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            col = tuple(item.get("color", default_color))
            if "index" in item and isinstance(item["index"], int):
                idx = item["index"]
                if 0 <= idx < matrix.count:
                    squares[idx] = col
            if "pattern" in item and isinstance(item["pattern"], list):
                offset = item.get("offset", 0)
                for i, bit in enumerate(item["pattern"]):
                    if bit:
                        idx = offset + i
                        if 0 <= idx < matrix.count:
                            squares[idx] = col

    for i, color in enumerate(squares):
        matrix[i] = color
    matrix.show()


def on_message(ws, message):
    try:
        inner = json.loads(message).get("message")
        if inner:
            handle_message(inner)
    except Exception as e:
        print(f"Ignoring invalid message: {e}")


topic = matrix.settings.get("topic")
if not topic:
    raise ValueError("No ntfy.sh topic found in config.json")

ws = websocket.WebSocketApp(f"wss://ntfy.sh/{topic}/ws", on_message=on_message)
listener = threading.Thread(target=ws.run_forever, daemon=True)
listener.start()

# Keep showing so scheduled brightness changes apply between messages
while listener.is_alive():
    matrix.show()
    time.sleep(1)

print("Connection to ntfy.sh closed")
sys.exit(1)
