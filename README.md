# Tunnel
### “地道”该工具是在玩幻兽帕鲁时的一个突发奇想。
在搭建帕鲁的服务端时发现服务端程序并不支持ipv6，然而国内的网络环境基本上已经普及ipv6，就有了一个想法，能否让帕鲁服务端支持ipv6，从而节省从云服务厂商处购买服务器的钱。刚开始想要逆一下服务端程序，给它上补丁，但是看到服务端程序的大小后就放弃了。后来在使用frp进行ipv4的反代时，想到可以写一个类似的程序运行在服务端，然后写一个客户端运行在玩家电脑上，监听127.0.0.1:8211 获取到请求数据后原封不动的通过ipv6打到服务端然后利用服务端运行的程序接受这个数据在打给帕鲁的服务端，以此利用ipv6进行游戏。

> 该脚本本质是一个隧道工具。

## 目的

当然是省钱啊，省下了买服务器的钱。

利用闲置的个人pc链接光猫即可获得一个公网ipv6成本几乎为”0“ 当然前提是你跌有闲置的个人pc，再然后就是ipv6的获取，一般来说ipv6获取问题不大，各大运营商都有支持，免费获取，是在不行就用sim卡插手机上，用usb共享网络给pc，pc也能获取到ipv6。

## 使用方法

该脚本分为三个部分，其中中继服务(relay_server)部分可以不需要，中继服务的作用就是能少一步手动输入ipv6的步骤(ipv6实在是太难记了)

### relay_server

`relay_server/service_main.py`

该脚本是中继服务，用来记录所有想要注册到该服务群的服务器ip及端口信息，同时也会验证注册到该服务群的服务器是否存活 目前你们可以不用关心这个，因为中继服务我使用白嫖的aliyun服务器运行了一个。上面啥都没，渗透大佬不要搞我哇。

### server

`server/client_server.py`

该脚本是运行在服务端的程序，该目录下还有个配置文件，默认设置即可(过年回老家了，来不及解释了，要上车了)。

### client

`client/client.py`

该脚本是运行在玩家电脑的脚本，运行该脚本并且指定完目标服务器后(连接成功没其他提示),此时玩家可以打开帕鲁然后连接"127.0.0.1:8211"即可直接连接到所选择的目标服务器

# 哦对，记得安装python3

中继服务需要使用pip包管理器来安装以下模块
`pip install fastapi`

客户端需要使用pip包管理器来安装以下模块
`pip install fastapi`

`pip install json`

服务端需要使用pip包管理器来安装以下模块
`pip install json`

`pip install requests`

