import tkinter as tk
import time
import psutil
from datetime import datetime
import ctypes
import os
import sys

# =========================
# LOAD DLL (SAFE)
# =========================
temp_available = False
computer = None

def get_path(file):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, file)
    return os.path.join(os.getcwd(), file)

try:
    import clr

    def load_dll(name):
        path = get_path(name)
        if os.path.exists(path):
            clr.AddReference(path)
        else:
            print("❌ Missing:", name)

    # load đúng thứ tự
    load_dll("System.Runtime.CompilerServices.Unsafe.dll")
    load_dll("System.Memory.dll")
    load_dll("System.Buffers.dll")
    load_dll("LibreHardwareMonitorLib.dll")

    from LibreHardwareMonitor import Hardware

    computer = Hardware.Computer()
    computer.IsCpuEnabled = True
    computer.Open()

    temp_available = True

except Exception as e:
    print("❌ LHM error:", e)
    temp_available = False

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

GRAPH_WIDTH = 80
GRAPH_HEIGHT = 14
GRAPH_POINTS = 40

TEXT_X = 0
GRAPH_X = 130

UPDATE_INTERVAL = 1000

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

def get_active_network():
    stats = psutil.net_if_stats()
    for name, s in stats.items():
        if s.isup and not name.lower().startswith("loopback"):
            if "wi-fi" in name.lower() or "wlan" in name.lower():
                return "WiFi"
            return "Ethernet"
    return ""

# =========================
# TEMP
# =========================
def get_cpu_temp():
    if not temp_available or not computer:
        return None

    try:
        for hw in computer.Hardware:
            hw.Update()
            if "CPU" in hw.Name:
                for sensor in hw.Sensors:
                    if "Temperature" in str(sensor.SensorType):
                        if "Package" in sensor.Name or "Core Max" in sensor.Name:
                            return sensor.Value
    except:
        return None

    return None

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
# FORMAT
# =========================
weekday = ["T2","T3","T4","T5","T6","T7","CN"]

def format_speed(kb):
    return f"{kb/1024:.1f} MB/s" if kb > 1024 else f"{kb:.0f} KB/s"

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

    net_name = get_active_network()
    temp = get_cpu_temp()

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

    # TEMP
    if temp is not None:
        draw_text(TEXT_X, y, f"Temp {temp:.0f}°C", COLOR_TEMP, FONT_SIZE)
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

    canvas.config(width=240, height=y+10)

    root.after(UPDATE_INTERVAL, update)

update()
root.mainloop()