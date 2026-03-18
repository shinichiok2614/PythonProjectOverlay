import tkinter as tk
import time
import psutil
from datetime import datetime

root = tk.Tk()

root.overrideredirect(True)
root.attributes("-topmost", True)

root.configure(bg="black")
root.wm_attributes("-transparentcolor", "black")

# ===== LABEL =====

label_time = tk.Label(
    root,
    font=("Consolas", 8),
    fg="red",
    bg="black",
    justify="left",
    anchor="w",
    padx=0,
    pady=0
)

label_cpu = tk.Label(
    root,
    font=("Consolas", 8),
    fg="deepskyblue",
    bg="black",
    justify="left",
    anchor="w",
    padx=0,
    pady=0
)

label_net = tk.Label(
    root,
    font=("Consolas", 8),
    fg="lime",
    bg="black",
    justify="left",
    anchor="w",
    padx=0,
    pady=0
)

label_time.pack(anchor="w")
label_cpu.pack(anchor="w")
label_net.pack(anchor="w")

# vị trí góc trái dưới
screen_height = root.winfo_screenheight()
root.geometry(f"+0+{screen_height-170}")

net_old = psutil.net_io_counters()

weekday = ["T2","T3","T4","T5","T6","T7","CN"]

def update():
    global net_old

    now = datetime.now()

    current_time = now.strftime("%H:%M:%S")
    date_text = f"{weekday[now.weekday()]}-{now.day:02d}-{now.month:02d}"

    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent

    net_new = psutil.net_io_counters()
    down = (net_new.bytes_recv - net_old.bytes_recv) / 1024
    up = (net_new.bytes_sent - net_old.bytes_sent) / 1024
    net_old = net_new

    # KHÔNG có \n dư ở đầu
    label_time.config(text=f"{current_time}\n{date_text}")
    label_cpu.config(text=f"CPU  : {cpu} %\nRAM  : {ram} %")
    label_net.config(text=f"NET ↓ {down:.0f} KB/s\nNET ↑ {up:.0f} KB/s")

    root.after(1000, update)

update()
root.mainloop()