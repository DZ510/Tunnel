from fastapi import FastAPI,Path
import select
import json
import socket
import threading
import time
import struct
app = FastAPI()



class ServerList:
    def __init__(self,cache_path:str) -> None:
        self.Server_list = list()
        self._server_name_list = set()
        self._socket_list = dict()
        self._udp_format = "I 1024s"
        pass

    def send_heartbeat(self,server_dict:dict,interval = 5):
        ipv4 = server_dict["server_ipv4"]
        ipv6 = server_dict["server_ipv6"]
        heartbeat_port = server_dict["heartbeat"]
        #默认使用ipv6
        server_addres = (ipv6,heartbeat_port)
        socket_udp  = socket.socket(socket.AF_INET6,socket.SOCK_DGRAM)
 
        while True:
            try:
                socket_udp.sendto("heartbeat".encode("utf-8"),server_addres)
                ready,_,_ = select.select([socket_udp],[],[],10)
                if ready:
                    data,responsive_client = socket_udp.recvfrom(4)
                    size = struct.unpack("I",data)
                    ready,_,_ = select.select([socket_udp],[],[],1)
                    if not ready:
                        server_dict["status"] = False
                        self._server_name_list.remove(server_dict["server_name"])
                        break
                    data,responsive_client = socket_udp.recvfrom(size[0])
                    if data.decode("utf-8") != "alive":
                        server_dict["status"] = False
                        self._server_name_list.remove(server_dict["server_name"])
                        break
                    else:
                        server_dict["status"] = True
                else:
                    server_dict["status"] = False
                    self._server_name_list.remove(server_dict["server_name"])
                    break
                # socket.sendall(struct.pack(self._udp_format,*(len("heartbeat"),"heartbeat")))
                time.sleep(interval)
            except BrokenPipeError:
                server_dict["status"] = False
                self._server_name_list.remove(server_dict["server_name"])
                break
        socket_udp.close()



    def append_server(self,server_dict:dict):
        if self.check_server_name_is_already_exist(server_dict):
            return False
        else:
            server_name = server_dict.get("server_name","")
            self._server_name_list.add(server_name)
            server_dict["status"] = False
            server_ipv6 = server_dict.get("server_ipv6","")
            server_v6port = server_dict.get("server_v6port",-1)
            ipv6flg = True
            if server_ipv6 == "" or server_v6port == -1:
                ipv6flg = False
            server_ipv4 = server_dict.get("server_ipv4","")
            server_v4port = server_dict.get("server_v4port",-1)
            ipv4flg = False
            if server_ipv4 == "" or server_v4port == -1:
                ipv4flg = False
            
            ipv4connect_status = False
            if ipv4flg:
                try:
                    ipv4connect_status = True
                    delayed_val = 5
                    heartbeat_thread = threading.Thread(target=self.send_heartbeat, args=(server_dict, delayed_val))
                    heartbeat_thread.start()
                except (socket.error,ConnectionRefusedError) as e:
                    print("ipv4 链接失败.尝试ipv6...")
                    #这里什么都不做因为有可能ipv6心跳端口开通
                    pass
            if (ipv4connect_status is False) and (ipv6flg):
                try:
                    delayed_val = 5
                    heartbeat_thread = threading.Thread(target=self.send_heartbeat, args=(server_dict, delayed_val))
                    heartbeat_thread.start()
                except (socket.error,ConnectionRefusedError)as e:
                    print("ipv6/ipv4 链接失败.servername:%s  服务器注册失败"%(server_name))
                    return False

            self.Server_list.append(server_dict)
            return True
        pass

    def check_server_is_alive(self,server_dict:dict):
        return server_dict.get("status",False)

    def check_server_name_is_already_exist(self,server_dict:dict):
        servername = server_dict.get("server_name","")
        if servername in self._server_name_list:
            return True
        else:
            return False

    def reconnect_server(self,server:dict):
        pass

    def destory_server(self,server:dict):
        pass

    def get_server_list(self):
        ret_serverlist = self.Server_list.copy()
        for serverobj in ret_serverlist:
            if self.check_server_is_alive(serverobj):
                pass
            else:
                self.Server_list.remove(serverobj)
        return self.Server_list.copy()

SERVER_LIST = [
    {
        "server_name":"fdgs",
        "server_ipv6":"::",
        "server_v6port":8211,
        "server_ipv4":"",
        "server_v4port":8211,
        "heartbeat":8848,
    }
]

SERVER_LIST_OBJ = ServerList("./cfg.json")


@app.get("/getserverlist")
async def getserverlist():
    server_list = SERVER_LIST_OBJ.get_server_list()
    return json.dumps(server_list)

@app.get("/register_server")
async def register_server(servername:str, ip_v6:str, v6port:int, ip_v4:str, v4port:int, heartbeatport:int):
    global SERVER_LIST_OBJ
    serverdict = \
    {
        "server_name":servername,
        "server_ipv6":ip_v6,
        "server_v6port":v6port,
        "server_ipv4":ip_v4,
        "server_v4port":v4port,
        "heartbeat":heartbeatport,
    }
    if SERVER_LIST_OBJ.append_server(serverdict):
        return {"status":True}
    else:
        return {"status":False}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,host="0.0.0.0",port = 4396)
