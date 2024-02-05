import socket
import requests
import threading
import random
import json
import struct
import sys
import datetime
import queue
import inspect
import select
from io import BytesIO


from until import *

# ipv6==>local ipv4
class LocalPortManagement:...


class Clinet:
    def __init__(self,ipv6socket:socket.socket,ipv4addr,ipv4prot,localport,local_socket_type,portmanagement:LocalPortManagement) -> None:
        #ipv4addr 本地运行的目标服务端的ip
        #ipv4port 本地运行的目标服务端的端口
        #localport 本地代理程序所使用的udp端口 强制使用该端口与服务端通信
        #lcoal_socket_type 本地代理程序所使用的协议 目前写死为udp
        self._ipv6socket = ipv6socket
        #理应在次判断local_socket_type
        self._udpsocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self._localport =localport
        self._udpsocket.bind(("127.0.0.1",localport)) #对udpsocket绑定端口 已便目标服务端和我们通信
        self._recvfromaddres = (ipv4addr,ipv4prot) #目标服务端绑定的端口及本地ip
        self.MSGSIZE = 1024*1024*10
        self.v4tov6queue = queue.Queue()
        self.v6tov4queue = queue.Queue()
        self.portmanagement = portmanagement


        self.THREAD_FLG = True
        pass
    
    def socket_read(self,socket:socket.socket,size:int):#
        tempdata = bytes()
        while size != 0:
            data = socket.recv(size)
            tempdata+=data
            size -= len(data)
        return tempdata


    def read_data_from_client(self):
        msgsize = self.socket_read(self._ipv6socket,4)
        size = struct.unpack("i",msgsize)[0]
        if size == len("wait connection..."):
            data = self.socket_read(self._ipv6socket,size)
            if data.decode("utf-8") == "wait connection...":
                return None
        return data
    
    def write_data_to_client(self,data):
        packdata = struct.pack("i",len(data))
        self._ipv6socket.sendall(packdata)
        self._ipv6socket.sendall(data)

        
    
    def write_data_to_local_app(self,data):
        self._udpsocket.sendto(data,self._recvfromaddres)

    def read_data_from_local_app(self,timeout=1):#超时10s就认为客户端已断开链接
        readable,_,_ = select.select([self._udpsocket],[],[],timeout)
        if readable:
            data = self._udpsocket.recv(self.MSGSIZE)
            return data
        else:
            return b""



    

    #client ---> queue
    def _thread_read_client2localapp(self):
        while self.THREAD_FLG:
            try:
                data = self.read_data_from_client()
                if data is None:
                    pass
                elif len(data) == 0:
                    self.THREAD_FLG = False
                    print("某个帕鲁断开了链接.")
                    pass
                else:
                    self.v6tov4queue.put(data)
            except Exception as e:
                self.THREAD_FLG = False
                print("某个帕鲁断开了链接.")

        pass
    #queue ---> localapp
    def _thread_write_client2localapp(self):
        while self.THREAD_FLG:
            try:
                data = self.v6tov4queue.get(timeout=1)
                if len(data) != 0:
                    self.write_data_to_local_app(data)
            except Exception as e:
                continue

    def client2localapp(self):
        self._client2localapp_thread_read = threading.Thread(target=self._thread_read_client2localapp,args=())
        self._client2localapp_thread_read.start()
        self._client2localapp_thread_write = threading.Thread(target=self._thread_write_client2localapp,args=())
        self._client2localapp_thread_write.start()

        pass

    #localapp ---> queue
    def _thread_read_localapp2client(self):
        while self.THREAD_FLG:
            try:
                data = self.read_data_from_local_app()
                #print(f"服务端发出\t{len(data)}\t")
                if len(data) > 0:
                    self.v4tov6queue.put(data)
            except Exception as e:
                print(f"line:{inspect.currentframe().f_lineno} error{e}")
        pass
    #queue ---> client
    def _thread_write_localapp2client(self):
        while self.THREAD_FLG:
            try:
                data = self.v4tov6queue.get(timeout=1)
                if len(data)> 0:
                    self.write_data_to_client(data)
            except Exception as e:
                continue

        pass
    def localapp2client(self):
        self._localapp2client_thread_read = threading.Thread(target=self._thread_read_localapp2client,args=())
        self._localapp2client_thread_read.start()
        self._localapp2client_thread_write = threading.Thread(target=self._thread_write_localapp2client,args=())
        self._localapp2client_thread_write.start()
        pass






    def start(self):
        self.client2localapp()
        self.localapp2client()
        self._client2localapp_thread_read.join()
        self._client2localapp_thread_write.join()
        self._localapp2client_thread_read.join()
        self._localapp2client_thread_write.join()
        self.shutdown()
        
    def shutdown(self):
        self.THREAD_FLG = False
        self._ipv6socket.close()
        self._udpsocket.close()
        self.portmanagement.set_destport_notuse(self.get_client_allocation_port())
        pass
        
    def get_client_addresandport(self):
        return self._recvfromaddres
    
    def get_client_allocation_port(self):
        return self._localport
        
        

class LocalPortManagement:
    def __init__(self,minprot,maxport) -> None:
        self.minport = minprot
        self.maxport = maxport
        self.shoudcount = maxport-minprot
        self.useport = set()
        pass
    
    def get_random_port(self):
        if len(self.useport) == self.shoudcount:
            return -1
        else:
            while True:
                randport = random.randrange(self.minport,self.maxport)
                if randport not in self.useport:
                    self.useport.add(randport)
                    return randport
                
    def set_destport_notuse(self,port):
        self.useport.remove(port)
        pass


class PalServerProcMain:
    def __init__(self,server_name:str,server_ipv6,server_v6port,server_ipv4,server_v4port,use_iptype=socket.AF_INET6,heartbeat_port=4396) -> None:
        self.server_name = server_name
        
        self.serverv6_addres = (server_ipv6,server_v6port)
        self.serverv4_addres = (server_ipv4,server_v4port)
        self.use_server_addres = (server_ipv6,server_v6port) if use_iptype == socket.AF_INET6 else (server_ipv4,server_v4port)
        self.heartbeat_port = heartbeat_port
        self.choose_ip_type = use_iptype #默认使用ip6
        self.protmanagement = LocalPortManagement(65500,65532)
        self.clientlist = list()
        pass
    
    
    def register_server(self):
        servername = self.server_name
        ip_v6 = self.serverv6_addres[0]
        v6port = self.serverv6_addres[1]
        ip_v4 = self.serverv4_addres[0]
        v4port =self.serverv4_addres[1]
        heartbeatport = self.heartbeat_port
        params = {
            "servername" : servername,
            "ip_v6" : ip_v6,
            "v6port":v6port,
            "ip_v4":ip_v4,
            "v4port":v4port,
            "heartbeatport":heartbeatport
        }
        #注册服务器前先开启心跳包服务器
        heartbeat_thread = threading.Thread(target=self.heartbeat_thread,args=())
        heartbeat_thread.start()
        response = requests.get("http://47.94.97.121:4396/register_server",params=params)    
        result = json.loads(response.text)
        if not result["status"]:
            print("服务器注册失败 请联系管理人员.")
            return False
        return True


    def heartbeat_thread(self):
        heartbeat_server = socket.socket(self.choose_ip_type,socket.SOCK_DGRAM)
        heartbeat_server.bind((self.use_server_addres[0],self.heartbeat_port))
        print(f"本地心跳包绑定至{self.use_server_addres}")
        while True:
            data,heartbeat_client_addres = heartbeat_server.recvfrom(1024*1024)
            timestr = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            print(f"{timestr}:验证服务存活的心跳包")
            if data.decode("utf-8") == "heartbeat":
                msg = "alive"
                heartbeat_server.sendto(struct.pack("I",len(msg)),heartbeat_client_addres) 
                heartbeat_server.sendto(struct.pack(str(len(msg))+"s",msg.encode("utf-8")),heartbeat_client_addres)
            else:
                break
    
    
    def start(self):
        if self.register_server():
            pass
            self.server_socket = socket.socket(self.choose_ip_type,socket.SOCK_STREAM)
            self.server_socket.bind(self.use_server_addres)
            self.server_socket.listen(32)
            while True:
                client_socket,addresinfo = self.server_socket.accept()
                print(f"{addresinfo}pal来电了")
                client_local_port = self.protmanagement.get_random_port()
                palclient = Clinet(client_socket,"127.0.0.1",8211,client_local_port,socket.SOCK_DGRAM,self.protmanagement)
                self.clientlist.append(palclient)
                threading.Thread(target=palclient.start(),args=()).start()
                
        else:
            print("启动代理服务端失败!")
        pass








if __name__ == "__main__":
    ipv6_address_list = get_local_ipv6_addres()
    index = 0
    for ipv6 in ipv6_address_list:
        print("%d.%s"%(index,ipv6))
        index+=1
    while True:
        try:
            selectindex = int(input("选择一个正确的IPV6地址,通常以24开头,且注意不要选到临时ipv6地址(需要命令行ipconfig/ifconfig确认):"))
            break
        except ValueError:
            print("输入无效请重新输入.")
    ipv6select = ""
    if selectindex > len(ipv6_address_list)-1:
        print("超出范围,默认选择最后一个")
        ipv6select = ipv6_address_list[-1]
    else:
        ipv6select = ipv6_address_list[selectindex]
    while True:
        try:
            selectindex = int(input("选择目标服务程序所使用的协议类型:\n0.tcp\ip\n1.udp\n"))
            break
        except ValueError:
            print("输入无效请重新输入.")
    if selectindex > 1:
        print("超出范围,默任使用UDP")
        protocol_type = PROTOCOL_TYPE[-1]
    else:
        protocol_type = PROTOCOL_TYPE[selectindex]

    
    with open("./cs_config.json","r") as f:
        cfg = json.load(f)
    
    servername = cfg["server"]["server_name"]
    ip_v6 = ipv6select
    v6port = cfg["server"]["ipv6_port"]
    ip_v4 = ""
    v4port = cfg["server"]["ipv4_port"]
    heartbeatport = cfg["server"]["heartbeatport"]
    pal_server = PalServerProcMain(servername,ip_v6,v6port,ip_v4,v4port,socket.AF_INET6,heartbeatport)
    pal_server.start()
    
    
    
    
    
    

