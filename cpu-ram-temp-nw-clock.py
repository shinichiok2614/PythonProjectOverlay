import tkinter as tk
import time
import psutil

root = tk.Tk()

# bỏ khung
root.overrideredirect(True)

# luôn trên cùng
root.attributes("-topmost", True)

# nền trong suốt
root.configure(bg="black")
root.wm_attributes("-transparentcolor", "black")

# chữ
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
root.geometry(f"+0+{screen_height-150}")

# network trước đó
net_old = psutil.net_io_counters()

def update():

    global net_old

    # giờ
    current_time = time.strftime("%H:%M:%S")

    # CPU
    cpu = psutil.cpu_percent()

    # RAM
    ram = psutil.virtual_memory().percent

    # Network
    net_new = psutil.net_io_counters()

    down = (net_new.bytes_recv - net_old.bytes_recv) / 1024
    up = (net_new.bytes_sent - net_old.bytes_sent) / 1024

    net_old = net_new

    # nhiệt độ (nếu có)
    temp = "N/A"
    try:
        temps = psutil.sensors_temperatures()
        for name in temps:
            temp = f"{temps[name][0].current:.1f}°C"
            break
    except:
        pass

    text = f"""
{current_time}
CPU  : {cpu} %
RAM  : {ram} %
TEMP : {temp}
NET ↓ {down:.0f} KB/s
NET ↑ {up:.0f} KB/s
"""

    label.config(text=text)

    root.after(1000, update)

update()

root.mainloop()