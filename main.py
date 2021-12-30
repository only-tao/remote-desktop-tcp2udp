import tkinter
import tkinter.messagebox
import struct
import socket
import numpy as np
from PIL import Image, ImageTk
import threading
import re
from cv2 import cv2
import time
import sys
import platform

import mediapipe as mp
import pyautogui
from gesture import hand_gesture
# import cv2
root = tkinter.Tk()

# 画面周期
IDLE = 0.05
# 放缩大小
scale = 1
# 原传输画面尺寸
fixw, fixh = 0, 0
# 放缩标志
wscale = False
# 屏幕显示画布
showcan = None
# socket缓冲区大小
bufsize = 10240
# 线程
thread = None
# socket
soc = None
# socks5
socks5 = None
# 平台
PLAT = b''
if sys.platform == "win32":
    PLAT = b'win'
elif sys.platform == "darwin":
    PLAT = b'osx'
elif platform.system() == "Linux":
    PLAT = b'x11'
#!!!! 初始化socket
def SetSocket():
    global soc, host_en

    host = host_en.get() # 得到host_en 内的内容，（就是输入框内的内容）
    if host is None:
        tkinter.messagebox.showinfo('提示', 'Host设置错误！')
        return
    host_split = host.split(":")
    if len(host_split) != 2:
        tkinter.messagebox.showinfo('提示', 'Host设置错误！')
        return
    else:
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #TODO1tcp 定义+连接，作为客户端 in SetSocket()
        #! connect(ip,port)   
        soc.connect((host_split[0], int(host_split[1])))
        #!2 现在查找数据从哪里来
# 通过移动滑条设置窗口的Scale
def SetScale(x):
    global scale, wscale
    scale = float(x) / 100
    wscale = True

def ShowScreen():
    global showcan, root, soc, thread, wscale
    if showcan is None:
        wscale = True
        showcan = tkinter.Toplevel(root)
        thread = threading.Thread(target=run)
        thread.start()
    else:
        soc.close()
        showcan.destroy()
stop_threads = False
def check_gesture(): 
    hand_gesture()
    
run_gesture = 0
def use_gesture():
    global run_gesture
    global stop_threads
    th2 = threading.Thread(target=check_gesture)
    
    stop_threads = False
    run_gesture = 1
    th2.start()
# GUI的排版
val = tkinter.StringVar()
host_lab = tkinter.Label(root, text="Host:") # host:...
host_en = tkinter.Entry(root, show=None, font=('Arial', 14), textvariable=val)
sca_lab = tkinter.Label(root, text="Scale:") # scale的按钮
window_scale = tkinter.Scale(root, from_=10, to=100, orient=tkinter.HORIZONTAL, length=100,
                    showvalue=100, resolution=0.1, tickinterval=50, command=SetScale)
                    # 设置窗口scale
show_btn = tkinter.Button(root, text="Show", command=ShowScreen)  # show 的按钮配置
gesture_btn = tkinter.Button(root, text="gesture", command=use_gesture)
#按钮设置位置
host_lab.grid(row=0, column=0, padx=10, pady=10, ipadx=0, ipady=0)
host_en.grid(row=0, column=1, padx=0, pady=0, ipadx=40, ipady=0) # 输入host数字的框
sca_lab.grid(row=1, column=0, padx=10, pady=10, ipadx=0, ipady=0)
window_scale.grid(row=1, column=1, padx=0, pady=0, ipadx=100, ipady=0)
gesture_btn.grid(row=2, column=0, padx=0, pady=10, ipadx=30, ipady=0)
show_btn.grid(row=2, column=1, padx=0, pady=10, ipadx=30, ipady=0)
# gesture_btn.grid()  # 原本gesture的位置是(2,0)
window_scale.set(100)
val.set('127.0.0.1:800')# 设置初始值

last_send = time.time()



def BindEvents(canvas):
    global soc, scale
    '''
    处理事件
    '''
    def EventDo(data):
        soc.sendall(data)
    # 鼠标左键

    def LeftDown(e):
        return EventDo(struct.pack('>BBHH', 1, 100, int(e.x/scale), int(e.y/scale)))

    def LeftUp(e):
        return EventDo(struct.pack('>BBHH', 1, 117, int(e.x/scale), int(e.y/scale)))
    canvas.bind(sequence="<1>", func=LeftDown)
    canvas.bind(sequence="<ButtonRelease-1>", func=LeftUp)

    # 鼠标右键
    def RightDown(e):
        return EventDo(struct.pack('>BBHH', 3, 100, int(e.x/scale), int(e.y/scale)))

    def RightUp(e):
        return EventDo(struct.pack('>BBHH', 3, 117, int(e.x/scale), int(e.y/scale)))
    canvas.bind(sequence="<3>", func=RightDown)
    canvas.bind(sequence="<ButtonRelease-3>", func=RightUp)

    # 鼠标滚轮
    if PLAT == b'win' or PLAT == 'osx':
        # windows/mac
        def Wheel(e):
            if e.delta < 0:
                return EventDo(struct.pack('>BBHH', 2, 0, int(e.x/scale), int(e.y/scale)))
            else:
                return EventDo(struct.pack('>BBHH', 2, 1, int(e.x/scale), int(e.y/scale)))
        canvas.bind(sequence="<MouseWheel>", func=Wheel)
    elif PLAT == b'x11':
        def WheelDown(e):
            return EventDo(struct.pack('>BBHH', 2, 0, int(e.x/scale), int(e.y/scale)))
        def WheelUp(e):
            return EventDo(struct.pack('>BBHH', 2, 1, int(e.x/scale), int(e.y/scale)))
        canvas.bind(sequence="<Button-4>", func=WheelUp)
        canvas.bind(sequence="<Button-5>", func=WheelDown)

    # 鼠标滑动
    # 100ms发送一次
    def Move(e):
        global last_send
        cu = time.time()
        if cu - last_send > IDLE:
            last_send = cu
            sx, sy = int(e.x/scale), int(e.y/scale)
            return EventDo(struct.pack('>BBHH', 4, 0, sx, sy))
    canvas.bind(sequence="<Motion>", func=Move)

    # 键盘
    def KeyDown(e):
        return EventDo(struct.pack('>BBHH', e.keycode, 100, int(e.x/scale), int(e.y/scale)))

    def KeyUp(e):
        return EventDo(struct.pack('>BBHH', e.keycode, 117, int(e.x/scale), int(e.y/scale)))
    canvas.bind(sequence="<KeyPress>", func=KeyDown)
    canvas.bind(sequence="<KeyRelease>", func=KeyUp)

# if click the "Show", the "run" will run
def run():
    global wscale, fixh, fixw, soc, showcan
    SetSocket() # 设置tcp连接与socks5代理
    # 发送平台信息
    soc.sendall(PLAT)
    length_bytes = soc.recv(5) #TODO2 得到infomation in run()
    imtype, length = struct.unpack(">BI", length_bytes)
    image_bytes = b''# 之后按照一定的规则处理数据=> image_bytes get length_bytes(length)
    while length > bufsize:  
        temporary = soc.recv(bufsize)
        image_bytes += temporary
        length -= len(temporary)
    while length > 0:
        temporary = soc.recv(length)
        image_bytes += temporary
        length -= len(temporary)
    data = np.frombuffer(image_bytes, dtype=np.uint8)
    image_seg = cv2.imdecode(data, cv2.IMREAD_COLOR)
    heigh, width, _ = image_seg.shape
    fixh, fixw = heigh, width
    imsh = cv2.cvtColor(image_seg, cv2.COLOR_BGR2RGBA)
    image_array = Image.fromarray(imsh)
    imgTK = ImageTk.PhotoImage(image=image_array)
    canvas = tkinter.Canvas(showcan, width=width, height=heigh, bg="white")
    canvas.focus_set()
    BindEvents(canvas)
    canvas.pack()
    canvas.create_image(0, 0, anchor=tkinter.NW, image=imgTK)
    heigh = int(heigh * scale)
    width = int(width * scale)
    while True:
        if wscale:
            heigh = int(fixh * scale)
            width = int(fixw * scale)
            canvas.config(width=width, height=heigh)
            wscale = False
        try:
            length_bytes = soc.recv(5)
            imtype, length = struct.unpack(">BI", length_bytes)
            image_bytes = b''
            while length > bufsize:
                temporary = soc.recv(bufsize)
                image_bytes += temporary
                length -= len(temporary)
            while length > 0:
                temporary = soc.recv(length)
                image_bytes += temporary
                length -= len(temporary)
            data = np.frombuffer(image_bytes, dtype=np.uint8)
            ims = cv2.imdecode(data, cv2.IMREAD_COLOR)
            if imtype == 1:
                # 全传
                image_seg = ims
            else:
                # 差异传
                image_seg = image_seg ^ ims
            imt = cv2.resize(image_seg, (width, heigh))
            imsh = cv2.cvtColor(imt, cv2.COLOR_RGB2RGBA)
            image_array = Image.fromarray(imsh)
            imgTK.paste(image_array)
        except:
            showcan = None
            ShowScreen()
            return


root.mainloop()
