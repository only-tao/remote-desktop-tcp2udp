from socket import *

HOST = '127.0.0.1'
PORT = 8888
BUFSIZ = 1024
ADDRESS = (HOST, PORT)

udpClientSocket = socket(AF_INET, SOCK_DGRAM)#TODO1 udpclient初始化

while True:
    data = input('>')
    if not data:
        break

    # 发送数据
    udpClientSocket.sendto(data.encode('utf-8'), ADDRESS)#TODO2 client sentto
    # 接收数据
    data, ADDR = udpClientSocket.recvfrom(BUFSIZ)
    if not data:
        break
    print("服务器端响应：", data.decode('utf-8'))

udpClientSocket.close()
