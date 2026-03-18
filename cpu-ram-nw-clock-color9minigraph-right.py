import tkinter as tk
import time
import psutil
from datetime import datetime
import json
import os
import ctypes
import subprocess

# =========================
# CONFIG
# =========================

DEFAULT_X = 5
DEFAULT_Y_OFFSET = 160

FONT_TIME = 8
FONT_DATE = 8
FONT_INFO = 8

COLOR_TIME = "red"
COLOR_CPU = "#00BFFF"
COLOR_NET = "lime"
COLOR_SHADOW = "#111"

GRAPH_WIDTH = 80
GRAPH_HEIGHT = 14
GRAPH_POINTS = 40

TEXT_X = 0
GRAPH_X =60

FONT_NAME = "Consolas"
FONT_WEIGHT = "bold"

UPDATE_INTERVAL = 1000
NETWORK_CHECK_INTERVAL = 3

SAVE_FILE = "overlay_pos.json"

# =========================
# WINDOW
# =========================

root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)

root.configure(bg="black")
root.wm_attributes("-transparentcolor", "black")

# click xuyên
hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
styles = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
ctypes.windll.user32.SetWindowLongW(hwnd, -20, styles | 0x80000 | 0x20)

canvas = tk.Canvas(root, bg="black", highlightthickness=0)
canvas.pack()

# =========================
# POSITION
# =========================

def load_pos():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return {"x": DEFAULT_X, "y": root.winfo_screenheight() - DEFAULT_Y_OFFSET}

def save_pos(x, y):
    with open(SAVE_FILE, "w") as f:
        json.dump({"x": x, "y": y}, f)

pos = load_pos()
root.geometry(f"+{pos['x']}+{pos['y']}")

# =========================
# DRAG (SHIFT)
# =========================

drag_data = {"x": 0, "y": 0}

def start_drag(event):
    if event.state & 0x1:
        drag_data["x"] = event.x
        drag_data["y"] = event.y

def do_drag(event):
    if event.state & 0x1:
        x = root.winfo_x() + (event.x - drag_data["x"])
        y = root.winfo_y() + (event.y - drag_data["y"])
        root.geometry(f"+{x}+{y}")
        save_pos(x, y)

canvas.bind("<Button-1>", start_drag)
canvas.bind("<B1-Motion>", do_drag)

# =========================
# NETWORK
# =========================

net_old = psutil.net_io_counters()

last_net_name = ""
last_interface = ""
last_check_time = 0

def get_active_interface():
    stats = psutil.net_if_stats()
    for name, s in stats.items():
        if s.isup and not name.lower().startswith("loopback"):
            return name
    return ""

def get_wifi_ssid():
    try:
        result = subprocess.check_output(
            "netsh wlan show interfaces",
            shell=True
        ).decode("utf-8", errors="ignore")

        for line in result.split("\n"):
            if "SSID" in line and "BSSID" not in line:
                return line.split(":")[1].strip()
    except:
        pass
    return ""

def get_network_name():
    global last_net_name, last_interface, last_check_time

    now = time.time()
    if now - last_check_time < NETWORK_CHECK_INTERVAL:
        return last_net_name

    last_check_time = now

    try:
        current_if = get_active_interface()

        if not current_if:
            last_interface = ""
            last_net_name = ""
            return ""

        if current_if != last_interface:
            last_interface = current_if

            if "wi-fi" in current_if.lower():
                last_net_name = get_wifi_ssid()
            else:
                last_net_name = current_if

            return last_net_name

        if "wi-fi" in current_if.lower():
            ssid = get_wifi_ssid()
            if ssid and ssid != last_net_name:
                last_net_name = ssid

    except:
        last_net_name = ""

    return last_net_name

# =========================
# GRAPH DATA
# =========================

cpu_history = []
net_history = []

def add_data(arr, value):
    arr.append(value)
    if len(arr) > GRAPH_POINTS:
        arr.pop(0)

# =========================
# DRAW
# =========================

weekday = ["T2","T3","T4","T5","T6","T7","CN"]

def format_speed(kb):
    return f"{kb/1024:.1f} MB/s" if kb > 1024 else f"{kb:.0f} KB/s"

def draw_text(x, y, text, color, size):
    canvas.create_text(x+1, y+1, text=text, fill=COLOR_SHADOW,
                       anchor="nw", font=(FONT_NAME, size, FONT_WEIGHT))
    canvas.create_text(x, y, text=text, fill=color,
                       anchor="nw", font=(FONT_NAME, size, FONT_WEIGHT))

def draw_graph(x, y, data, color):
    if len(data) < 2:
        return

    max_val = max(max(data), 1)
    step = GRAPH_WIDTH / GRAPH_POINTS

    points = []
    for i, val in enumerate(data):
        px = x + i * step
        py = y + GRAPH_HEIGHT - (val / max_val * GRAPH_HEIGHT)
        points.extend([px, py])

    canvas.create_line(points, fill=color, width=2)

# =========================
# UPDATE
# =========================

def update():
    global net_old

    canvas.delete("all")

    now = datetime.now()

    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent

    net_new = psutil.net_io_counters()
    down = (net_new.bytes_recv - net_old.bytes_recv) / 1024
    up = (net_new.bytes_sent - net_old.bytes_sent) / 1024
    net_old = net_new

    net_name = get_network_name()

    add_data(cpu_history, cpu)
    add_data(net_history, down)

    y = 0

    # TIME
    draw_text(TEXT_X, y, now.strftime("%H:%M:%S"), COLOR_TIME, FONT_TIME)
    y += FONT_TIME

    draw_text(TEXT_X, y, f"{weekday[now.weekday()]} {now.day:02d}/{now.month:02d}", COLOR_TIME, FONT_DATE)
    y += FONT_DATE + 6

    # CPU + GRAPH
    draw_text(TEXT_X, y, f"CPU {cpu:>3}%", COLOR_CPU, FONT_INFO)
    draw_graph(GRAPH_X, y + 2, cpu_history, COLOR_CPU)
    y += FONT_INFO + 6

    # RAM
    draw_text(TEXT_X, y, f"RAM {ram:>3}%", COLOR_CPU, FONT_INFO)
    y += FONT_INFO + 6

    # NETWORK
    if net_name:
        draw_text(TEXT_X, y, net_name, COLOR_NET, FONT_INFO)
        draw_graph(GRAPH_X, y + 2, net_history, COLOR_NET)
        y += FONT_INFO + 2

        draw_text(TEXT_X, y, f"↓ {format_speed(down)}", COLOR_NET, FONT_INFO)
        y += FONT_INFO + 2

        # 🔥 UPLOAD (không có graph)
        draw_text(TEXT_X, y, f"↑ {format_speed(up)}", COLOR_NET, FONT_INFO)
        y += FONT_INFO

    canvas.config(width=220, height=y+10)

    root.after(UPDATE_INTERVAL, update)

update()
root.mainloop()