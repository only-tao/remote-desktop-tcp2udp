import struct
import socket
from PIL import ImageGrab
from PIL import Image
from cv2 import cv2
import numpy as np
import threading
import time
import pyautogui as ag
import mouse
from keyboard import getKeycodeMapping
import io

# 作为server服务器
# 画面周期
IDLE = 0.05
# 鼠标滚轮灵敏度
SCROLL_NUM = 5
bufsize = 65536
host = ('127.0.0.1', 800)
addrc = ()
# soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# soc.bind(host)
# soc.listen(1)
# 压缩比 1-100 数值越小，压缩比越高，图片质量损失越严重
conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
conn.bind(host)
IMQUALITY = 50

lock = threading.Lock()


# if sys.platform == "win32":
#     from ._keyboard_win import keycodeMapping
# elif platform.system() == "Linux":
#     from ._keyboard_x11 import keycodeMapping
# elif sys.platform == "darwin":
#     from ._keyboard_osx import keycodeMapping


def ctrl(conn, ):
    '''
    读取控制命令，并在本机还原操作
    '''
    keycodeMapping = {}

    def Op(key, op, ox, oy):
        # print(key, op, ox, oy)
        if key == 4:
            # 鼠标移动
            mouse.move(ox, oy)
        elif key == 1:
            if op == 100:
                # 左键按下
                ag.mouseDown(button=ag.LEFT)
            elif op == 117:
                # 左键弹起
                ag.mouseUp(button=ag.LEFT)
        elif key == 2:
            # 滚轮事件
            if op == 0:
                # 向上
                ag.scroll(-SCROLL_NUM)
            else:
                # 向下
                ag.scroll(SCROLL_NUM)
        elif key == 3:
            # 鼠标右键
            if op == 100:
                # 右键按下
                ag.mouseDown(button=ag.RIGHT)
            elif op == 117:
                # 右键弹起
                ag.mouseUp(button=ag.RIGHT)
        else:
            k = keycodeMapping.get(key)
            if k is not None:
                if op == 100:
                    ag.keyDown(k)
                elif op == 117:
                    ag.keyUp(k)

    try:
        plat = b''
        while True:
            data, addr = conn.recvfrom(3 - len(plat))
            addrc = addr
            plat += data  # conn.recv(3-len(plat))
            if len(plat) == 3:
                break
        print("Plat:", plat.decode())
        keycodeMapping = getKeycodeMapping(plat)
        base_len = 6
        while True:
            cmd = b''
            rest = base_len - 0
            while rest > 0:
                data, addr = conn.recvfrom(rest)
                addrc = addr
                cmd += data  # conn.recv(rest)
                rest -= len(cmd)
            key = cmd[0]
            op = cmd[1]
            x = struct.unpack('>H', cmd[2:4])[0]  # struct主要是用来处理C结构数据的，读入时先转换为Python的 字符串 类型，然后再转换为Python的结构化类
            y = struct.unpack('>H', cmd[4:6])[0]  # python -> uint32 32位的字符
            Op(key, op, x, y)
    except:
        return


# 压缩后np图像
image_old_decode = None
# 编码后的图像
image_grab_new = None


def handle(conn, ):
    global image_old_decode, image_grab_new
    lock.acquire()
    if image_grab_new is None:
        image_grab = ImageGrab.grab()
        # 添加压缩代码##
        compress_rate = 0.5
        heigh, width = image_grab.height,image_grab.width
        img = cv2.cvtColor(np.asarray(image_grab), cv2.COLOR_RGB2BGR)
        image_resize = cv2.resize(img, (int(width * compress_rate), int(heigh* compress_rate )),
                                  interpolation=cv2.INTER_AREA)
        image_grab = Image.fromarray(cv2.cvtColor(image_resize,cv2.COLOR_BGR2RGB))
        image_original_array = np.asarray(image_grab)  # cut screen
        _, image_grab_new = cv2.imencode(
            ".jpg", image_original_array, [cv2.IMWRITE_JPEG_QUALITY, IMQUALITY])  # change to jpg?
        image_new_array = np.asarray(image_grab_new, np.uint8)
        image_old_decode = cv2.imdecode(image_new_array, cv2.IMREAD_COLOR)
    lock.release()
    lenb = struct.pack(">BI", 1, len(image_grab_new))
    conn.sendto(image_grab_new, addrc)
    # conn.sendto(lenb, addrc)
    # for i in range(len(image_grab_new) // bufsize + 1):
    #     if bufsize * (i + 1) > len(image_grab_new):
    #         conn.sendto(image_grab_new[bufsize * i:], addrc)
    #     else:
    #         conn.sendto(image_grab_new[bufsize * i:bufsize * (i + 1)], addrc)
    # conn.sendall(lenb)
    # conn.sendall(image_grab_new)
    while True:
        # fix for linux
        time.sleep(IDLE)
        image_grab = ImageGrab.grab()
        compress_rate = 0.5
        heigh, width = image_grab.height, image_grab.width
        img = cv2.cvtColor(np.asarray(image_grab), cv2.COLOR_RGB2BGR)
        image_resize = cv2.resize(img, (int(width * compress_rate), int(heigh * compress_rate )),
                                  interpolation=cv2.INTER_AREA)
        image_grab = Image.fromarray(cv2.cvtColor(image_resize, cv2.COLOR_BGR2RGB))
        imgnpn = np.asarray(image_grab)
        _, timbyt = cv2.imencode(
            ".jpg", imgnpn, [cv2.IMWRITE_JPEG_QUALITY, IMQUALITY])
        image_new_array = np.asarray(timbyt, np.uint8)
        imgnew = cv2.imdecode(image_new_array, cv2.IMREAD_COLOR)
        # 计算图像差值
        imgs = imgnew ^ image_old_decode
        if (imgs != 0).any():
            # 画质改变
            pass
        else:
            continue
        image_grab_new = timbyt
        image_old_decode = imgnew
        # 无损压缩
        _, image_diff_encode = cv2.imencode(".png", imgs)
        l1 = len(image_grab_new)  # 原图像大小
        l2 = len(image_diff_encode)  # 差异图像大小
        if False:#l1 > l2:
            # 传差异化图像
            lenb = struct.pack(">BI", 0, l2)  # bi = struct.pack(">I",234) =>  bi-> bi[0],bi[1],bi[2],bi[3] 4字节
            conn.sendto(lenb, addrc)
            for i in range(len(image_grab_new) // bufsize + 1):
                if bufsize * (i + 1) > len(image_grab_new):
                    conn.sendto(image_grab_new[bufsize * i:], addrc)
                else:
                    conn.sendto(image_grab_new[bufsize * i:bufsize * (i + 1)], addrc)
            # conn.sendall(lenb)
            # conn.sendall(image_diff_encode)
        else:
            # 传原编码图像
            conn.sendto(image_grab_new,addrc)
            # lenb = struct.pack(">BI", 1, l1)
            # conn.sendto(lenb, addrc)
            # for i in range(len(image_grab_new) // bufsize + 1):
            #     if bufsize * (i + 1) > len(image_grab_new):
            #         conn.sendto(image_grab_new[bufsize * i:], addrc)
            #     else:
            #         conn.sendto(image_grab_new[bufsize * i:bufsize * (i + 1)], addrc)
            # conn.sendall(lenb)
            # conn.sendall(image_grab_new)


# def main():
# conn, addr = soc.accept()
while True:
    _, addr = conn.recvfrom(5)
    addrc = addr
    t1 = threading.Thread(target=handle, args=(conn,))
    t2 = threading.Thread(target=ctrl, args=(conn,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    # handle(conn)
    # ctrl(conn)

# if __name__ == '__main__':
#     main()
