import tkinter as tk
import time
import psutil
from datetime import datetime
import json
import os
import ctypes

# ===== CONFIG =====
SAVE_FILE = "overlay_pos.json"

# ===== WINDOW =====
root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)

root.configure(bg="black")
root.wm_attributes("-transparentcolor", "black")

# ===== CLICK XUYÊN =====
hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
styles = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
ctypes.windll.user32.SetWindowLongW(hwnd, -20, styles | 0x80000 | 0x20)
# 0x80000 = WS_EX_LAYERED
# 0x20 = WS_EX_TRANSPARENT

# ===== CANVAS =====
canvas = tk.Canvas(root, bg="black", highlightthickness=0)
canvas.pack()

# ===== LOAD POSITION =====
def load_pos():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            return json.load(f)
    return {"x": 5, "y": root.winfo_screenheight() - 150}

def save_pos(x, y):
    with open(SAVE_FILE, "w") as f:
        json.dump({"x": x, "y": y}, f)

pos = load_pos()
root.geometry(f"+{pos['x']}+{pos['y']}")

# ===== DRAG (SHIFT + kéo) =====
drag_data = {"x": 0, "y": 0}

def start_drag(event):
    if event.state & 0x1:  # SHIFT
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

# ===== DATA =====
net_old = psutil.net_io_counters()
weekday = ["T2","T3","T4","T5","T6","T7","CN"]

def format_speed(kb):
    if kb > 1024:
        return f"{kb/1024:.1f} MB/s"
    return f"{kb:.0f} KB/s"

def draw(x, y, text, color, size):
    canvas.create_text(x+1, y+1, text=text, fill="#111",
                       anchor="nw", font=("Consolas", size, "bold"))
    canvas.create_text(x, y, text=text, fill=color,
                       anchor="nw", font=("Consolas", size, "bold"))

# ===== UPDATE =====
def update():
    global net_old

    canvas.delete("all")

    now = datetime.now()

    time_str = now.strftime("%H:%M:%S")
    date_str = f"{weekday[now.weekday()]} {now.day:02d}/{now.month:02d}"

    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent

    net_new = psutil.net_io_counters()
    down = (net_new.bytes_recv - net_old.bytes_recv) / 1024
    up = (net_new.bytes_sent - net_old.bytes_sent) / 1024
    net_old = net_new

    y = 0

    draw(0, y, time_str, "red", 26)
    y += 26

    draw(0, y, date_str, "red", 16)
    y += 22

    draw(0, y, f"CPU {cpu:>3}%", "#00BFFF", 16)
    y += 18

    draw(0, y, f"RAM {ram:>3}%", "#00BFFF", 16)
    y += 20

    draw(0, y, f"↓ {format_speed(down)}", "lime", 16)
    y += 18

    draw(0, y, f"↑ {format_speed(up)}", "lime", 16)

    canvas.config(width=170, height=y+10)

    root.after(1000, update)

update()
root.mainloop()