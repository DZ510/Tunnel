import socket

PROTOCOL_TYPE = [
    socket.SOCK_STREAM, #TCP
    socket.SOCK_DGRAM  #UDP
]


def get_local_ipv6_addres():
    ipv6list = list()

    try:
        hostname = socket.gethostname()
        ipv6addres = socket.getaddrinfo(hostname,None,socket.AF_INET6)
        for ipinfo in ipv6addres:
            ipv6list.append(ipinfo[4][0])
        return ipv6list
    except (socket.error,ConnectionRefusedError) as e:
        print(f"Error:{e}")
        pass
