import tkinter as tk
import time
import psutil
from datetime import datetime
import ctypes
import subprocess
import os

# =========================
# LOAD LibreHardwareMonitor
# =========================
import clr
import os
import sys

base = os.getcwd()
sys.path.append(base)

# load dependency trước
clr.AddReference("System.Runtime.CompilerServices.Unsafe")
clr.AddReference("System.Memory")
clr.AddReference("System.Buffers")

# load main DLL
clr.AddReference("LibreHardwareMonitorLib")

from LibreHardwareMonitor import Hardware

computer = Hardware.Computer()
computer.IsCpuEnabled = True
computer.IsGpuEnabled = False
computer.IsMotherboardEnabled = True
computer.IsFanControllerEnabled = True
computer.Open()

# =========================
# CONFIG
# =========================
FONT_NAME = "Consolas"
FONT_SIZE = 16
FONT_TIME = 26

COLOR_TIME = "red"
COLOR_CPU = "#00BFFF"
COLOR_NET = "lime"
COLOR_TEMP = "orange"
COLOR_FAN = "cyan"

GRAPH_WIDTH = 80
GRAPH_HEIGHT = 14
GRAPH_POINTS = 40

TEXT_X = 0
GRAPH_X = 120

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

root.geometry("+5+500")

# =========================
# NETWORK
# =========================
net_old = psutil.net_io_counters()
last_net_name = ""
last_check = 0

def get_network_name():
    global last_net_name, last_check

    if time.time() - last_check < 3:
        return last_net_name

    last_check = time.time()

    try:
        result = subprocess.check_output(
            "netsh wlan show interfaces",
            shell=True
        ).decode(errors="ignore")

        for line in result.split("\n"):
            if "SSID" in line and "BSSID" not in line:
                last_net_name = line.split(":")[1].strip()
                return last_net_name
    except:
        pass

    # fallback ethernet
    stats = psutil.net_if_stats()
    for name, s in stats.items():
        if s.isup and not name.lower().startswith("loopback"):
            last_net_name = name
            return name

    last_net_name = ""
    return ""

# =========================
# HARDWARE (TEMP + FAN)
# =========================
def get_hwinfo():
    cpu_temp = None
    fan = None

    for hw in computer.Hardware:
        hw.Update()

        for sensor in hw.Sensors:
            if sensor.SensorType == Hardware.SensorType.Temperature:
                if "CPU" in sensor.Name:
                    cpu_temp = sensor.Value

            if sensor.SensorType == Hardware.SensorType.Fan:
                fan = sensor.Value

    return cpu_temp, fan

# =========================
# GRAPH
# =========================
cpu_hist = []
net_hist = []

def push(arr, val):
    arr.append(val)
    if len(arr) > GRAPH_POINTS:
        arr.pop(0)

def draw_graph(x, y, data, color):
    if len(data) < 2:
        return

    max_val = max(max(data), 1)
    step = GRAPH_WIDTH / GRAPH_POINTS

    pts = []
    for i, v in enumerate(data):
        px = x + i * step
        py = y + GRAPH_HEIGHT - (v / max_val * GRAPH_HEIGHT)
        pts.extend([px, py])

    canvas.create_line(pts, fill=color, width=2)

def draw_text(x, y, text, color, size):
    canvas.create_text(x+1, y+1, text=text, fill="#111",
                       anchor="nw", font=(FONT_NAME, size, "bold"))
    canvas.create_text(x, y, text=text, fill=color,
                       anchor="nw", font=(FONT_NAME, size, "bold"))

# =========================
# UPDATE
# =========================
weekday = ["T2","T3","T4","T5","T6","T7","CN"]

def format_speed(kb):
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

    net_name = get_network_name()
    temp, fan = get_hwinfo()

    push(cpu_hist, cpu)
    push(net_hist, down)

    y = 0

    # TIME
    draw_text(TEXT_X, y, now.strftime("%H:%M:%S"), COLOR_TIME, FONT_TIME)
    y += FONT_TIME

    draw_text(TEXT_X, y,
              f"{weekday[now.weekday()]} {now.day:02d}/{now.month:02d}",
              COLOR_TIME, FONT_SIZE)
    y += FONT_SIZE + 6

    # CPU
    draw_text(TEXT_X, y, f"CPU {cpu:>3}%", COLOR_CPU, FONT_SIZE)
    draw_graph(GRAPH_X, y+2, cpu_hist, COLOR_CPU)
    y += FONT_SIZE + 4

    # RAM
    draw_text(TEXT_X, y, f"RAM {ram:>3}%", COLOR_CPU, FONT_SIZE)
    y += FONT_SIZE + 4

    # TEMP + FAN
    if temp:
        draw_text(TEXT_X, y, f"Temp {temp:.0f}°C", COLOR_TEMP, FONT_SIZE)
        y += FONT_SIZE

    if fan:
        draw_text(TEXT_X, y, f"Fan {fan:.0f} RPM", COLOR_FAN, FONT_SIZE)
        y += FONT_SIZE + 4

    # NETWORK
    if net_name:
        draw_text(TEXT_X, y, net_name, COLOR_NET, FONT_SIZE)
        draw_graph(GRAPH_X, y+2, net_hist, COLOR_NET)
        y += FONT_SIZE

        draw_text(TEXT_X, y, f"↓ {format_speed(down)}", COLOR_NET, FONT_SIZE)
        y += FONT_SIZE

        draw_text(TEXT_X, y, f"↑ {format_speed(up)}", COLOR_NET, FONT_SIZE)
        y += FONT_SIZE

    canvas.config(width=220, height=y+10)

    root.after(1000, update)

update()
root.mainloop()