import tkinter as tk
import time
import psutil
from datetime import datetime

root = tk.Tk()

# bỏ khung
root.overrideredirect(True)

# luôn trên cùng
root.attributes("-topmost", True)

# nền trong suốt
root.configure(bg="black")
root.wm_attributes("-transparentcolor", "black")

label = tk.Label(
    root,
    font=("Consolas", 8),
    fg="red",
    bg="black",
    justify="left"
)

label.pack()

# vị trí góc trái dưới
screen_height = root.winfo_screenheight()
root.geometry(f"+0+{screen_height-160}")

net_old = psutil.net_io_counters()

# tên thứ
weekday = ["CN","Thu2","Thu3","Thu4","Thu5","Thu6","Thu7"]

def update():

    global net_old

    now = datetime.now()

    current_time = now.strftime("%H:%M:%S")
    date_text = f"{weekday[now.weekday()+1 if now.weekday()<6 else 0]}-{now.day:02d}-{now.month:02d}"

    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent

    net_new = psutil.net_io_counters()

    down = (net_new.bytes_recv - net_old.bytes_recv) / 1024
    up = (net_new.bytes_sent - net_old.bytes_sent) / 1024

    net_old = net_new

    text = f"""
{current_time}
{date_text}
CPU  : {cpu} %
RAM  : {ram} %
NET ↓ {down:.0f} KB/s
NET ↑ {up:.0f} KB/s
"""

    label.config(text=text)

    root.after(1000, update)

update()

root.mainloop()