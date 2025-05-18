### 🌟 **问题原因：Docker 自动重建规则**

在 Docker 环境中，**Docker 守护进程（`dockerd`）** 会自动管理和维护 iptables 规则。
 当你执行以下操作时，Docker 可能会自动重新生成 NAT 规则：

### ✅ **触发 Docker 自动创建规则的原因**

1. **容器重启**
   - 你重启了 `compassionate_lewin` 容器，Docker 会在容器重启时自动建立端口映射规则。
   - Docker 认为宿主机的 8080 端口需要映射到容器的 8080 端口，因此会自动生成 DNAT 规则。
2. **Docker 网络重载**
   - Docker 网络服务会定期同步 NAT 规则。
   - 如果 Docker 网络配置被修改或重新加载（如 Docker 网络重启或容器 IP 变更），Docker 会重新建立端口映射规则。
3. **Docker 守护进程重启**
   - 如果你重启了 Docker 守护进程（`systemctl restart docker`），Docker 会重新生成映射规则。
4. **容器配置端口映射**
   - 如果容器的 `docker run` 命令或 `docker-compose` 文件配置了端口映射（如 `-p 8080:8080`），Docker 会自动建立规则。
   - 即使你手动删除 iptables 规则，Docker 在容器重启后仍会根据配置重建。

------

### 🚀 **原因分析**

Docker 的端口映射机制通过以下步骤自动创建规则：

1. **创建 Docker 容器时**，Docker 监听到 `-p 8080:8080` 端口映射。
2. Docker 在 `DOCKER` 链中通过 **DNAT 规则**，将宿主机的 `8080` 端口映射到容器的 `8080` 端口。
3. 如果规则被删除，Docker 守护进程会在容器或网络重启后**自动重建规则**。

------

## 💡 **解决方案**

### ✅ **方法 1：阻止 Docker 自动生成规则**

👉 你可以通过 **修改 Docker 守护进程配置文件** 来防止 Docker 自动生成规则。

#### **步骤 1：修改 Docker 配置**

1. 打开 Docker 配置文件（通常是 `/etc/docker/daemon.json`）：

```bash
sudo nano /etc/docker/daemon.json
```

1. 添加以下配置，阻止 Docker 管理 iptables 规则：

```json
{
  "iptables": false
}
```

1. 重启 Docker 服务：

```bash
sudo systemctl restart docker
```

👉 **效果：**

- Docker 不会再自动生成 iptables 规则。
- 但是你需要手动创建 NAT 规则才能访问容器。

------

### ✅ **方法 2：通过 Docker 网络设置来控制端口映射**

👉 你可以在 `docker run` 时**不使用 `-p` 选项**，而是通过 Docker 网络直接连接。

#### **示例：**

1. 先创建 Docker 网络：

```bash
docker network create my_custom_network
```

1. 将容器加入该网络（而不是暴露端口）：

```bash
docker run -d --name compassionate_lewin --network=my_custom_network vulfocus/log4j2-rce-2021-12-09:1
```

1. 通过其他容器或宿主机内部通信（无需通过端口映射）。

------

### ✅ **方法 3：在生成规则后立即删除**

👉 如果你不想修改 Docker 配置，可以通过在容器启动后立即删除规则的方法来解决。

#### **示例：**

1. 容器启动后，通过以下命令删除 Docker 自动生成的规则：

```bash
sudo iptables -t nat -D DOCKER 8
```

1. 如果 Docker 重启后规则重新生成，可以使用 **脚本自动清除**：

在 `/etc/docker/daemon.json` 中，设置 `iptables=true`，然后创建脚本自动清理：

```bash
#!/bin/bash
# 定义要删除的规则编号
RULE_NUM=$(sudo iptables -t nat -L DOCKER --line-numbers | grep 'tcp dpt:8080 to:172.17.0.2:8080' | awk '{print $1}')
if [[ ! -z "$RULE_NUM" ]]; then
    sudo iptables -t nat -D DOCKER $RULE_NUM
fi
```

- 将脚本保存为 `/usr/local/bin/docker_fix.sh`
- 设置为 Docker 服务启动时自动运行：

```bash
chmod +x /usr/local/bin/docker_fix.sh
echo "/usr/local/bin/docker_fix.sh" | sudo tee -a /etc/rc.local
```

------

### ✅ **方法 4：利用 Docker Compose 限制端口绑定**

👉 在 `docker-compose.yml` 文件中，不要暴露宿主机端口，直接使用 Docker 内部网络通信。

#### **示例：**

```yaml
services:
  app:
    image: vulfocus/log4j2-rce-2021-12-09:1
    networks:
      - my_custom_network

networks:
  my_custom_network:
    driver: bridge
```

- 启动时使用 `docker-compose up -d`
- Docker 就不会再为该容器生成端口映射规则。

------

## 🔥 **推荐方法**

| 方法                         | 优劣                                               | 推荐场景                               |
| ---------------------------- | -------------------------------------------------- | -------------------------------------- |
| 方法 1：修改 Docker 配置     | **从根源上禁用规则生成**，但可能会影响其他容器通信 | 适合对 Docker 网络配置有完全掌控的环境 |
| 方法 2：通过 Docker 网络设置 | 直接通过 Docker 网络通信，避免端口暴露             | 适合服务内部通信，不需要外部访问       |
| 方法 3：删除规则             | 容器启动后清理规则，但每次都需要操作               | 快速临时解决方案                       |
| 方法 4：Docker Compose 限制  | 直接在 Compose 文件中配置，不需要外部端口          | 适合生产环境，自动化配置               |

------

## ✅ **最佳解决方案**

1. 如果你想要**完全屏蔽外部访问**，推荐使用 **方法 1** 或 **方法 2**。
2. 如果你只想在特定情况下禁用，推荐使用 **方法 3**。
3. 如果你使用 `Docker Compose` 进行管理，直接在 Compose 文件中配置是最好的选择。

------

> 🚀 **推荐最佳方法：修改 Docker 配置 + 使用 Docker 内部网络通信 🔥**