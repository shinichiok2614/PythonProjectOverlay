import tkinter as tk
import time
import psutil
from datetime import datetime
import json
import os
import ctypes
import subprocess

# =========================
# ===== CONFIG ============
# =========================

DEFAULT_X = 5
DEFAULT_Y_OFFSET = 150

FONT_TIME = 8
FONT_DATE = 8
FONT_INFO = 8

COLOR_TIME = "red"
COLOR_CPU = "#00BFFF"
COLOR_NET = "lime"
COLOR_SHADOW = "#111"

FONT_NAME = "Consolas"
FONT_WEIGHT = "bold"

UPDATE_INTERVAL = 1000
NETWORK_NAME_INTERVAL = 5  # giây

SHOW_SECONDS = True

SAVE_FILE = "overlay_pos.json"

# =========================
# ===== WINDOW ============
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
# ===== POSITION ==========
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
# ===== DRAG (SHIFT) ======
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
# ===== NETWORK ===========
# =========================

net_old = psutil.net_io_counters()
last_net_name = ""
last_net_time = 0

def get_network_name():
    global last_net_name, last_net_time

    # cache
    if time.time() - last_net_time < NETWORK_NAME_INTERVAL:
        return last_net_name

    try:
        stats = psutil.net_if_stats()

        active_if = None
        for name, s in stats.items():
            if s.isup and not name.lower().startswith("loopback"):
                active_if = name
                break

        if active_if:
            # WiFi
            if "wi-fi" in active_if.lower() or "wireless" in active_if.lower():
                result = subprocess.check_output(
                    "netsh wlan show interfaces",
                    shell=True
                ).decode("utf-8", errors="ignore")

                for line in result.split("\n"):
                    if "SSID" in line and "BSSID" not in line:
                        last_net_name = line.split(":")[1].strip()
                        break
            else:
                last_net_name = active_if
        else:
            last_net_name = ""

    except:
        last_net_name = ""

    last_net_time = time.time()
    return last_net_name

def has_network():
    stats = psutil.net_if_stats()
    for s in stats.values():
        if s.isup:
            return True
    return False

# =========================
# ===== DRAW ==============
# =========================

weekday = ["T2","T3","T4","T5","T6","T7","CN"]

def format_speed(kb):
    return f"{kb/1024:.1f} MB/s" if kb > 1024 else f"{kb:.0f} KB/s"

def draw(x, y, text, color, size):
    canvas.create_text(
        x+1, y+1,
        text=text,
        fill=COLOR_SHADOW,
        anchor="nw",
        font=(FONT_NAME, size, FONT_WEIGHT)
    )
    canvas.create_text(
        x, y,
        text=text,
        fill=color,
        anchor="nw",
        font=(FONT_NAME, size, FONT_WEIGHT)
    )

# =========================
# ===== UPDATE ============
# =========================

def update():
    global net_old

    canvas.delete("all")

    # kiểm tra mạng
    if not has_network():
        root.withdraw()  # ẩn hoàn toàn
        root.after(UPDATE_INTERVAL, update)
        return
    else:
        root.deiconify()  # hiện lại

    now = datetime.now()

    time_str = now.strftime("%H:%M:%S" if SHOW_SECONDS else "%H:%M")
    date_str = f"{weekday[now.weekday()]} {now.day:02d}/{now.month:02d}"

    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent

    net_new = psutil.net_io_counters()
    down = (net_new.bytes_recv - net_old.bytes_recv) / 1024
    up = (net_new.bytes_sent - net_old.bytes_sent) / 1024
    net_old = net_new

    net_name = get_network_name()

    y = 0

    draw(0, y, time_str, COLOR_TIME, FONT_TIME)
    y += FONT_TIME

    draw(0, y, date_str, COLOR_TIME, FONT_DATE)
    y += FONT_DATE + 6

    draw(0, y, f"CPU {cpu:>3}%", COLOR_CPU, FONT_INFO)
    y += FONT_INFO + 2

    draw(0, y, f"RAM {ram:>3}%", COLOR_CPU, FONT_INFO)
    y += FONT_INFO + 4

    # network
    if net_name:
        draw(0, y, net_name, COLOR_NET, FONT_INFO)
        y += FONT_INFO + 2

    draw(0, y, f"↓ {format_speed(down)}", COLOR_NET, FONT_INFO)
    y += FONT_INFO + 2

    draw(0, y, f"↑ {format_speed(up)}", COLOR_NET, FONT_INFO)

    canvas.config(width=180, height=y+10)

    root.after(UPDATE_INTERVAL, update)

update()
root.mainloop()