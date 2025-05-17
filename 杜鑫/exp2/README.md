
# 网安实践实验二
---
## 拓扑搭建
候选镜像经过测试，可用列表如下：

- drupal 远程代码执行 （CVE-2019-6339）
- wordpress 命令执行 （CVE-2016-10033）
- Webmin 远程代码执行 （CVE-2022-0824）
- jenkins 代码执行 （CVE-2017-1000353）
- liferay 命令执行 (CVE-2020-7961)
- ~~ofbiz 远程代码执行 (CVE-2020-9496)~~
- ~~samba 代码执行 (CVE-2017-7494)~~
- ~~rsync-common 未授权访问~~
- phpimap 命令执行 (CVE-2018-19518)
- Nexus Repository Manager3 EL注入 (CVE-2018-16621)
- Druid 任意文件读取 （CVE-2021-36749）

scan port scanner/portscan/tcp

故搭建下面结构的网络：

![](./img/网络结构.png)


---
## 第一层漏洞

启动场景后的开放端口中，可以有效访问的两个分别为wordpress和liferay的端口：

![](./img/初始端口对外开放情况.png)

### wordpress 命令执行 （CVE-2016-10033）

在kali进入msf的终端，开始搜索指定类型的漏洞：

![](./img/进入msf的终端并开始搜索漏洞.png)

搜索到指定给的漏洞后，通过`use`命令进入模块，并查看模块的相关信息：

![](./img/使用搜索到的模组并进行相应的信息查看.png)

通过info的信息修改ip和port

![](./img/wordpress修改ip和端口.png)

![](./img/wordpress修改ip和端口2.png)

修改完必须的参数后发动攻击：

![](./img/wordpress%20getshell.png)

得到flag

![](./img/攻破wordpress.png)


需要注意这里有一个问题，在ip为 192.168.131.10 这台虚拟机中，Metasploit的版本为6.4

![](./img/10verison.png)

而另外一个更新过的ip为 192.168.131.6 的虚拟机中Metasploit的版本高达6.4.56

Metasploit 在最新的 dev 分支里，默认的 HTTP Stager Server 在把第一阶段的 prestager 脚本 (“wget…”) 送出去之后就立刻关掉了。
而在 6.4.9 里，这个内置的文件服务器会一直挂着，等机器再去拉真正的 Meterpreter 二进制的时候还在，于是就能成功。

![](./img/6versin.png)

这导致了对于这个漏洞，在老版本的Metasploit钟可以正常利用其攻击模组实现攻击，连接到shell，而在新的Metasploit中却不可以



### liferay 命令执行 (CVE-2020-7961)

和之前的wordpress一样处理，搜索相关的漏洞，找到后使用msf自带的攻击模块：

![](./img/liferay漏洞模块.png)

同样设置相关的参数

![](./img/设置相关参数.png)

设置完后进行攻击：

![](./img/liferay启动后攻击成功.png)

连接shell成功后在`/tmp`路径得到flag

![](./img/liferay得到flag.png)

---


## 第二层漏洞：

在获得了第一层的shell后，需要进入meterpreter中查看ip网段

![](./img/发现第一层内网网段.png)

然后配置路由代理，使后面的攻击能够访问内网：

![](./img/第一层配置autoroute代理.png)

完毕后将session放入后台

![](./img/liferayshell放入后台.png)

扫描第二层的开放情况：

![](./img/第二层扫描.png)

搜索第二层的一个漏洞webmin的模块，找到后启用并配置参数

![](./img/webmin配置参数如下.png)

配置完后启动攻击得到session

![](./img/webmin开启sessions.png)

对得到的session进行升级，方便后面配置route路由

![](./img/webmin升级session.png)

进入升级后的session查看ip发现是双网卡

![](./img/webmin发现是双网卡.png)

和第一层的一样配置路由以供下一层内网使用：

![](./img/webmin配置路由.png)

接着顺手getflag

![](./img/webmingetflag.png)

## 第四层漏洞

