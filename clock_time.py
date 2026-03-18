import tkinter as tk
import time

# Tạo cửa sổ
root = tk.Tk()

# Bỏ khung cửa sổ
root.overrideredirect(True)

# Luôn nằm trên cùng
root.attributes("-topmost", True)

# Màu nền (để làm trong suốt)
root.configure(bg="black")

# lấy chiều cao màn hình
screen_height = root.winfo_screenheight()

# vị trí góc trái dưới
root.geometry(f"+0+{screen_height-80}")

# Label hiển thị giờ
label = tk.Label(
    root,
    font=("Arial", 10),
    fg="red",
    bg="black"
)

label.pack()

# Cập nhật giờ
def update_time():
    # current = time.strftime("%H:%M:%S")
    current = time.strftime("%H:%M")
    label.config(text=current)
    root.after(1000, update_time)

update_time()

# Làm nền trong suốt
root.wm_attributes("-transparentcolor", "black")

root.mainloop()