from socket import *
from time import ctime

HOST = ''
PORT = 8888
BUFSIZ = 1024
ADDRESS = (HOST, PORT)

udpServerSocket = socket(AF_INET, SOCK_DGRAM)#TODO1 udp 初始化
udpServerSocket.bind(ADDRESS)      #TODO2 udp 绑定客户端口和地址

while True:
    print("waiting for message...")
    data, addr = udpServerSocket.recvfrom(BUFSIZ)#TODO3 recvfrom
    # get data and addr
    print("接收到数据：", data.decode('utf-8'))

    # content = '[%s] %s' % (bytes(ctime(), 'utf-8'), data.decode('utf-8'))
    content = "{}".format(data.decode('utf-8'))
    udpServerSocket.sendto(content.encode('utf-8'), addr)#TODO sendto 回传
    print('...received from and returned to:', addr)

udpServerSocket.close()
