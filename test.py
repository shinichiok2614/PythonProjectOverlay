import clr
import time
import os
import sys

# =========================
# LOAD DLL
# =========================
base = os.getcwd()
sys.path.append(base)

clr.AddReference("System.Runtime.CompilerServices.Unsafe")
clr.AddReference("System.Memory")
clr.AddReference("System.Buffers")
clr.AddReference("System.Management")
clr.AddReference("LibreHardwareMonitorLib")

# noinspection PyUnresolvedReferences
from LibreHardwareMonitor import Hardware

# =========================
# INIT
# =========================
computer = Hardware.Computer()
computer.IsCpuEnabled = True
computer.Open()

# =========================
# READ TEMP
# =========================
def get_cpu_temp():
    for hw in computer.Hardware:
        hw.Update()

        for sensor in hw.Sensors:
            if sensor.Value is None:
                continue

            if sensor.SensorType == Hardware.SensorType.Temperature:
                if "CPU" in sensor.Name:
                    return sensor.Value

    return None

# =========================
# LOOP
# =========================
while True:
    temp = get_cpu_temp()

    if temp:
        print(f"CPU Temp: {temp:.1f}°C")
    else:
        print("Temp: N/A")

    time.sleep(1)