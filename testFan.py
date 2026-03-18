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
computer.IsFanControllerEnabled = True
computer.IsCpuEnabled = True
computer.Open()

for hw in computer.Hardware:
    hw.Update()
    print("===", hw.Name)

    for s in hw.Sensors:
        if s.Value is not None:
            print(s.SensorType, s.Name, s.Value)