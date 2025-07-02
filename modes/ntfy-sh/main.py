import os
import json
import board
import neopixel
import websocket

CONFIG_PATH = os.environ.get("LEDMATRIX_CONFIG", "config.json")
with open(CONFIG_PATH) as f:
    config = json.load(f)

LED_COUNT = 64
PIN = board.D18
BRIGHTNESS = config.get("brightness", 0.2)

pixels = neopixel.NeoPixel(PIN, LED_COUNT, brightness=BRIGHTNESS, auto_write=False)
current = [[0, 0, 0] for _ in range(LED_COUNT)]

def render(squares):
    for i in range(LED_COUNT):
        pixels[i] = tuple(squares[i])
    pixels.show()

def handle_message(payload):
    global current
    try:
        message = json.loads(payload)
        data = message.get("data")
        reset = message.get("reset", True)
        default_color = message.get("color", [0, 255, 0])
        squares = [[0, 0, 0] for _ in range(LED_COUNT)] if reset else [c[:] for c in current]

        if isinstance(data, dict):
            data = [data]

        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                col = item.get("color", default_color)
                if "index" in item and isinstance(item["index"], int):
                    idx = item["index"]
                    if 0 <= idx < LED_COUNT:
                        squares[idx] = col
                if "pattern" in item and isinstance(item["pattern"], list):
                    offset = item.get("offset", 0)
                    for i, bit in enumerate(item["pattern"]):
                        if bit:
                            idx = offset + i
                            if 0 <= idx < LED_COUNT:
                                squares[idx] = col

        current = [c[:] for c in squares]
        render(squares)

    except Exception:
        pass

def on_message(ws, message):
    try:
        outer = json.loads(message)
        inner = outer.get("message")
        if inner:
            handle_message(inner)
    except:
        pass

topic = config.get("ntfy-sh", {}).get("topic")
if not topic:
    raise ValueError("No ntfy.sh topic found in config.json")

ws_url = f"wss://ntfy.sh/{topic}/ws"
ws = websocket.WebSocketApp(ws_url, on_message=on_message)

try:
    ws.run_forever()
except KeyboardInterrupt:
    pixels.fill((0, 0, 0))
    pixels.show()
