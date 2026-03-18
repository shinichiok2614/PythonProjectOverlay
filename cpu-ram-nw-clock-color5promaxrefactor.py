import tkinter as tk
import time
import psutil
from datetime import datetime
import json
import os
import ctypes

# =========================
# ===== CONFIG ============
# =========================

# vị trí mặc định
DEFAULT_X = 5
DEFAULT_Y_OFFSET = 10   # khoảng cách từ đáy màn hình

# kích thước font
FONT_TIME = 8
FONT_DATE = 8
FONT_INFO = 8

# màu sắc
COLOR_TIME = "red"
COLOR_CPU = "#00BFFF"
COLOR_NET = "lime"
COLOR_SHADOW = "#111"

# font
FONT_NAME = "Consolas"
FONT_WEIGHT = "bold"

# tốc độ update (ms)
UPDATE_INTERVAL = 1000

# hiển thị
SHOW_SECONDS = True

# file lưu vị trí
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
# ===== DATA ==============
# =========================

net_old = psutil.net_io_counters()
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

    now = datetime.now()

    # time
    if SHOW_SECONDS:
        time_str = now.strftime("%H:%M:%S")
    else:
        time_str = now.strftime("%H:%M")

    date_str = f"{weekday[now.weekday()]} {now.day:02d}/{now.month:02d}"

    # system
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent

    net_new = psutil.net_io_counters()
    down = (net_new.bytes_recv - net_old.bytes_recv) / 1024
    up = (net_new.bytes_sent - net_old.bytes_sent) / 1024
    net_old = net_new

    # draw
    y = 0

    draw(0, y, time_str, COLOR_TIME, FONT_TIME)
    y += FONT_TIME

    draw(0, y, date_str, COLOR_TIME, FONT_DATE)
    y += FONT_DATE + 6

    draw(0, y, f"CPU {cpu:>3}%", COLOR_CPU, FONT_INFO)
    y += FONT_INFO + 2

    draw(0, y, f"RAM {ram:>3}%", COLOR_CPU, FONT_INFO)
    y += FONT_INFO + 4

    draw(0, y, f"↓ {format_speed(down)}", COLOR_NET, FONT_INFO)
    y += FONT_INFO + 2

    draw(0, y, f"↑ {format_speed(up)}", COLOR_NET, FONT_INFO)

    canvas.config(width=180, height=y+10)

    root.after(UPDATE_INTERVAL, update)

update()
root.mainloop()