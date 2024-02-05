import socket
import requests
import json
import queue
import threading
import time
import inspect
import traceback
import select
import struct

from io import BytesIO


class LocalAgent:
    def __init__(self,server_ipv6,server_ipv6port,server_ipv4,server_ipv4port,use_ipv6:bool,local_addres,local_port):
        self.READ_SZIE = 1024*1024
        self.WRITE_SIZE = 1024*1024
        self.socket_server = socket.socket(socket.AF_INET6,socket.SOCK_STREAM)
        if use_ipv6:
            server_info = (server_ipv6,server_ipv6port)
            self.socket_server.connect(server_info)
            pass
        else:
            server_info = (server_ipv4,server_ipv4port)
            self.socket_server.connect(server_info)
            pass
        local_addresinfo = (local_addres,local_port)
        self.socket_local = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.socket_local.bind(local_addresinfo)
        self.v6tov4_queue = queue.Queue() #
        self.v4tov6_queue = queue.Queue()
        self.local_addres = None
        self.THREAD_FLG = True


    def socket_read(self,dest_socket:socket.socket,size:int):
        tempdata = bytes()
        while size!=0:
            data = dest_socket.recv(size)
            size -= len(data)
            tempdata+=data
        return tempdata


    def server_socket_read(self):
        msgsize = self.socket_read(self.socket_server,4)
        size = struct.unpack("i",msgsize)[0]
        tempbytes = BytesIO()
        #print(f"从服务端收回{size}个字节数据")
        while size!=0:
            data = self.socket_read(self.socket_server,size)
            tempbytes.write(data)
            size -= len(data)
        tempbytes.seek(0)
        return tempbytes.read()
    
    def server_socket_write(self,data:bytes):
        packsize = struct.pack("i",len(data))
        self.socket_server.sendall(packsize)
        self.socket_server.sendall(data)


    def local_wirte(self,data):
        return self.socket_local.sendto(data,self.local_addres)
        pass

    def local_read(self,timeout=5):
        readable,_,_ = select.select([self.socket_local],[],[],timeout)
        if readable:
            data,addres = self.socket_local.recvfrom(self.READ_SZIE)
            self.local_addres = addres
            return data
        else:
            time.sleep(1)
            return "wait connecting...".encode("utf-8")
        pass
    


    def _thread_read_server2localapp(self):
        while self.THREAD_FLG:
            try:
                data = self.server_socket_read()
                if len(data) > 0:
                    self.v6tov4_queue.put(data)
            except socket.error as e:
                print(f"line:{inspect.currentframe().f_lineno}  error:{e}")
                self.THREAD_FLG =False

    def _thread_write_server2localapp(self):
        while self.THREAD_FLG:
            try:
                data = self.v4tov6_queue.get()
                if len(data) > 0:
                    self.server_socket_write(data)
            except socket.error as e:
                print(f"line:{inspect.currentframe().f_lineno}  error:{e}")
                self.THREAD_FLG =False

    def v6_to_v4_thread(self):
        server2localapp_thread_read = threading.Thread(target=self._thread_read_server2localapp,args=())
        server2localapp_thread_read.start()
        server2localapp_thread_write = threading.Thread(target=self._thread_write_server2localapp,args=())
        server2localapp_thread_write.start()


    def _thread_read_localapp2server(self):
        while self.THREAD_FLG:
            try:
                data = self.local_read()
                if len(data) > 0:
                    self.v4tov6_queue.put(data)
            except socket.error as e:
                print(f"line:{inspect.currentframe().f_lineno}  error:{e}")
                self.THREAD_FLG



    def _thread_write_localapp2server(self):
        while self.THREAD_FLG:
            try:
                data = self.v6tov4_queue.get()
                if len(data) > 0:
                    self.local_wirte(data)
            except socket.error as e:
                print(f"line:{inspect.currentframe().f_lineno}  error:{e}")
                self.THREAD_FLG

    def v4_to_v6_thread(self):
        localapp2server_thread_read = threading.Thread(target=self._thread_read_localapp2server,args=())
        localapp2server_thread_read.start()
        localapp2server_thread_write = threading.Thread(target=self._thread_write_localapp2server,args=())
        localapp2server_thread_write.start()
    

    def start(self):
        self.v6_to_v4_thread()
        self.v4_to_v6_thread()

        pass

    def shutdown(self):
        #注意 由于udp的无连接特性  会导致一些线程一直recv demo 暂不修复
        self.THREAD_FLG = False

        pass

        
    def free(self):
        self.shutdown()
        self.socket_server.close()
        self.socket_local.close()





def main():
    #该链接属于中继服务器
    #用于获取所有注册到该中继服务器游戏服务端信息#
    #该服务器是我在阿里云白嫖一个月的免费服务器 贡献出来给大家来存游戏服务端的信息
    #当然 如果你也可以直接手动输入
    try:
        response =  requests.get("http://47.94.97.121:4396/getserverlist",headers={"accept":"application/json"})
        serverlist = json.loads(json.loads(response.text))
    except Exception as e:
        serverlist = []
    serveraddlist = [("::",-1)]
    index = 1
    for serverinfo in serverlist:
        servername = serverinfo["server_name"]
        server_ipv6 = serverinfo["server_ipv6"]
        server_ipv6_port = serverinfo["server_v6port"]
        serveraddlist.append((server_ipv6,server_ipv6_port))
        print(f"{index}.{servername}")
        index+=1
    while True:
        select_index = int(input("请选择一个服务器,或者输入0 手动输入目标服务器信息"))
        if select_index == 0:
            ipv6 = input("目标服务器的ipv6地址:")
            v6port = int(input("目标服务器的Tunnel端口:"))
            break
            pass
        elif select_index < 0 or select_index > len(serveraddlist)-1:
            print("选择错误 请重新选择")
            continue
        else:
            ipv6,v6port  = serveraddlist[select_index]
            break
    try:
        localagnet = LocalAgent(ipv6,v6port,"",-1,True,"127.0.0.1",8211)  #8211为本地游戏所使用的端口 幻兽帕鲁通常为8211
        localagnet.start()
        while True:
            try:
                time.sleep(10)
            except KeyboardInterrupt as e:
                localagnet.free()


    except Exception as e:
        print(f"{e}")


    pass
if __name__ == "__main__":
    main()