import tkinter as tk
import time
import psutil
from datetime import datetime
import ctypes
import subprocess
import os
import sys

# =========================
# FIX PATH DLL (.NET)
# =========================
base_dir = os.getcwd()
sys.path.append(base_dir)

import clr

def load_dll(name):
    path = os.path.join(base_dir, name)
    if os.path.exists(path):
        clr.AddReference(path)

# load dependency trước
load_dll("System.Runtime.CompilerServices.Unsafe.dll")
load_dll("System.Memory.dll")
load_dll("System.Buffers.dll")

# load main
load_dll("LibreHardwareMonitorLib.dll")

from LibreHardwareMonitor import Hardware

# =========================
# INIT HARDWARE
# =========================
computer = Hardware.Computer()
computer.IsCpuEnabled = True
computer.IsMotherboardEnabled = True
computer.IsFanControllerEnabled = True

try:
    computer.Open()
    HW_OK = True
except:
    HW_OK = False

# =========================
# CONFIG
# =========================
FONT = "Consolas"
SIZE = 8
SIZE_TIME = 8

COLOR_TIME = "red"
COLOR_CPU = "#00BFFF"
COLOR_NET = "lime"
COLOR_TEMP = "orange"
COLOR_FAN = "cyan"

GRAPH_W = 40
GRAPH_H = 14
GRAPH_N = 40

TEXT_X = 0
GRAPH_X = 60

# =========================
# WINDOW
# =========================
root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.configure(bg="black")
root.wm_attributes("-transparentcolor", "black")

hwnd = ctypes.windll.user32.GetParent(root.winfo_id())

def set_click_through(enable=True):
    styles = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
    if enable:
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, styles | 0x80000 | 0x20)
    else:
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, styles & ~0x20)

set_click_through(True)

canvas = tk.Canvas(root, bg="black", highlightthickness=0)
canvas.pack()

root.geometry("+5+500")

# =========================
# DRAG SHIFT
# =========================
dragging = False
offset_x = 0
offset_y = 0

def start_drag(event):
    global dragging, offset_x, offset_y
    if event.state & 0x0001:  # SHIFT
        dragging = True
        offset_x = event.x
        offset_y = event.y
        set_click_through(False)

def do_drag(event):
    if dragging:
        x = root.winfo_pointerx() - offset_x
        y = root.winfo_pointery() - offset_y
        root.geometry(f"+{x}+{y}")

def stop_drag(event):
    global dragging
    dragging = False
    set_click_through(True)

canvas.bind("<Button-1>", start_drag)
canvas.bind("<B1-Motion>", do_drag)
canvas.bind("<ButtonRelease-1>", stop_drag)

# =========================
# NETWORK
# =========================
net_old = psutil.net_io_counters()
last_net = ""
last_check = 0

def get_net_name():
    global last_net, last_check

    if time.time() - last_check < 3:
        return last_net

    last_check = time.time()

    try:
        result = subprocess.check_output(
            "netsh wlan show interfaces",
            shell=True
        ).decode(errors="ignore")

        for line in result.split("\n"):
            if "SSID" in line and "BSSID" not in line:
                last_net = line.split(":")[1].strip()
                return last_net
    except:
        pass

    stats = psutil.net_if_stats()
    for name, s in stats.items():
        if s.isup and not name.lower().startswith("loopback"):
            last_net = name
            return name

    last_net = ""
    return ""

# =========================
# HARDWARE
# =========================
def get_hw():
    if not HW_OK:
        return None, None

    cpu_temp = None
    fan = None

    try:
        for hw in computer.Hardware:
            hw.Update()

            for s in hw.Sensors:
                if s.Value is None:
                    continue

                if s.SensorType == Hardware.SensorType.Temperature:
                    if "CPU" in s.Name:
                        cpu_temp = s.Value

                if s.SensorType == Hardware.SensorType.Fan:
                    fan = s.Value
    except:
        pass

    return cpu_temp, fan

# =========================
# GRAPH
# =========================
cpu_hist = []
net_hist = []

def push(arr, val):
    arr.append(val)
    if len(arr) > GRAPH_N:
        arr.pop(0)

def draw_graph(x, y, data, color):
    if len(data) < 2:
        return

    m = max(max(data), 1)
    step = GRAPH_W / GRAPH_N

    pts = []
    for i, v in enumerate(data):
        px = x + i * step
        py = y + GRAPH_H - (v / m * GRAPH_H)
        pts.extend([px, py])

    canvas.create_line(pts, fill=color, width=2)

def draw_text(x, y, text, color, size):
    canvas.create_text(x+1, y+1, text=text, fill="#111",
                       anchor="nw", font=(FONT, size, "bold"))
    canvas.create_text(x, y, text=text, fill=color,
                       anchor="nw", font=(FONT, size, "bold"))

# =========================
# UPDATE
# =========================
weekday = ["T2","T3","T4","T5","T6","T7","CN"]

def speed(kb):
    return f"{kb/1024:.1f} MB/s" if kb > 1024 else f"{kb:.0f} KB/s"

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

    net_name = get_net_name()
    temp, fan = get_hw()

    push(cpu_hist, cpu)
    push(net_hist, down)

    y = 0

    # TIME
    # draw_text(TEXT_X, y, now.strftime("%H:%M:%S"), COLOR_TIME, SIZE_TIME)
    draw_text(TEXT_X, y, now.strftime("%H:%M"), COLOR_TIME, SIZE_TIME)
    y += SIZE_TIME + 2

    draw_text(TEXT_X, y,
              f"{weekday[now.weekday()]} {now.day:02d}/{now.month:02d}",
              COLOR_TIME, SIZE)
    y += SIZE + 4

    # CPU
    draw_text(TEXT_X, y, f"CPU {cpu:>3}%", COLOR_CPU, SIZE)
    draw_graph(GRAPH_X, y+2, cpu_hist, COLOR_CPU)
    y += SIZE

    # RAM
    draw_text(TEXT_X, y, f"RAM {ram:>3}%", COLOR_CPU, SIZE)
    y += SIZE + 4

    # TEMP / FAN
    if temp:
        draw_text(TEXT_X, y, f"Temp {temp:.0f}°C", COLOR_TEMP, SIZE)
        y += SIZE +4

    if fan:
        draw_text(TEXT_X, y, f"Fan {fan:.0f} RPM", COLOR_FAN, SIZE)
        y += SIZE + 4

    # NETWORK
    if net_name:
        draw_text(TEXT_X, y, net_name, COLOR_NET, SIZE)
        draw_graph(GRAPH_X, y+2, net_hist, COLOR_NET)
        y += SIZE

        draw_text(TEXT_X, y, f"↓ {speed(down)}", COLOR_NET, SIZE)
        y += SIZE

        draw_text(TEXT_X, y, f"↑ {speed(up)}", COLOR_NET, SIZE)
        y += SIZE

    canvas.config(width=230, height=y+10)

    root.after(1000, update)

# =========================
# RUN
# =========================
update()
root.mainloop()