import tkinter as tk
import time
import psutil
from datetime import datetime

root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)

# nền trong suốt
root.configure(bg="black")
root.wm_attributes("-transparentcolor", "black")

# canvas
canvas = tk.Canvas(root, bg="black", highlightthickness=0)
canvas.pack()

# vị trí góc trái dưới
screen_height = root.winfo_screenheight()
root.geometry(f"+5+{screen_height-150}")

net_old = psutil.net_io_counters()

weekday = ["T2","T3","T4","T5","T6","T7","CN"]

def format_speed(kb):
    if kb > 1024:
        return f"{kb/1024:.1f} MB/s"
    return f"{kb:.0f} KB/s"

def draw_text(x, y, text, color, size):
    # shadow nhẹ cho “pro”
    canvas.create_text(x+1, y+1, text=text, fill="#111", anchor="nw",
                       font=("Consolas", size, "bold"))
    canvas.create_text(x, y, text=text, fill=color, anchor="nw",
                       font=("Consolas", size, "bold"))

def update():
    global net_old

    canvas.delete("all")

    now = datetime.now()

    # ===== TIME =====
    time_str = now.strftime("%H:%M:%S")
    date_str = f"{weekday[now.weekday()]} {now.day:02d}/{now.month:02d}"

    # ===== CPU RAM =====
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent

    # ===== NETWORK =====
    net_new = psutil.net_io_counters()
    down = (net_new.bytes_recv - net_old.bytes_recv) / 1024
    up = (net_new.bytes_sent - net_old.bytes_sent) / 1024
    net_old = net_new

    # ===== DRAW =====
    y = 0

    draw_text(0, y, time_str, "red", 26)
    y += 26

    draw_text(0, y, date_str, "red", 16)
    y += 22

    draw_text(0, y, f"CPU {cpu:>3}%", "#00BFFF", 16)
    y += 18

    draw_text(0, y, f"RAM {ram:>3}%", "#00BFFF", 16)
    y += 20

    draw_text(0, y, f"↓ {format_speed(down)}", "lime", 16)
    y += 18

    draw_text(0, y, f"↑ {format_speed(up)}", "lime", 16)

    # resize canvas theo nội dung
    canvas.config(width=180, height=y+20)

    root.after(1000, update)

update()
root.mainloop()