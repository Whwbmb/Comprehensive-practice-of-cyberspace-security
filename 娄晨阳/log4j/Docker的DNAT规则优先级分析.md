是的，**Docker 的端口映射（DNAT）规则的优先级**确实比你手动配置的 **iptables 规则优先级更高**，因为 Docker 的网络规则会在 **PREROUTING 阶段**就先于手动配置的 `iptables` 规则生效。

------

## 🧠 **原因分析**

1. **Docker 的端口映射是基于 DNAT 规则**（即目标地址转换）。

   - Docker 在创建容器时，会在 `iptables` 的 `nat` 表中生成 `DOCKER` 链。
   - 在 `PREROUTING` 链中插入了调用 `DOCKER` 链的规则。

2. **请求匹配顺序如下：**

   - ```
     iptables
     ```

      的处理顺序是：

     - `PREROUTING` → `INPUT` → `FORWARD` → `POSTROUTING`

   - Docker 的 `DNAT` 规则插入在 `PREROUTING` 链中，且比 `INPUT` 链更早执行。

   - 也就是说：

     - **Docker 的 DNAT 规则先于 INPUT 链中的规则生效**
     - 只要请求命中 Docker 的端口映射规则，`iptables` 在 `INPUT` 链中设置的 `DROP` 或 `REJECT` 规则就不会再生效。

3. **优先级示例：**

- 例如，存在以下两条规则：

```bash
# Docker 端口映射（在 nat 表的 DOCKER 链中）
8        2   120 DNAT       tcp -- 0.0.0.0/0            0.0.0.0/0            tcp dpt:22220 to:172.17.0.2:8080

# iptables 规则（在 filter 表的 INPUT 链中）
sudo iptables -A INPUT -p tcp --dport 22220 -j REJECT
```

🔎 **流程是这样的：**

- 当你访问 `22220` 端口时：
   ✅ Docker 的 DNAT 规则会在 `PREROUTING` 阶段首先匹配并触发。
   ✅ 连接被直接重定向到容器的 `172.17.0.2:8080`。
   ❌ 因为 Docker 已经在 `PREROUTING` 进行了 DNAT，后面的 `INPUT` 规则就**不会再触发**。

------

## 🚨 **为什么 Docker 的 DNAT 规则优先级更高？**

✅ Docker 将自己的规则注入在 `nat` 表的 `PREROUTING` 链中，而不是 `INPUT` 链。
 ✅ 这意味着当流量匹配 DNAT 规则时，它会直接在 `PREROUTING` 被重定向，根本不会再走到 `INPUT` 链中。

------

## 💡 **解决方法**

### 🔹 方法 1：在 `PREROUTING` 之前手动禁止 Docker 的 DNAT 规则

👉 你可以在 `PREROUTING` 链中插入规则，优先于 Docker 的 DNAT 规则，使其无法重定向。

例如：

```bash
# 在 PREROUTING 链中拒绝目标端口 22220 的流量
sudo iptables -t nat -I PREROUTING -p tcp --dport 22220 -j DROP
```

> **解释：**
>  `-I` 会将规则插入在第一个位置，从而在 Docker 规则之前生效。

------

### 🔹 方法 2：禁用 Docker 自动创建的端口映射

👉 Docker 的 DNAT 规则是通过 `-p` 选项生成的。
 👉 你可以通过不使用 `-p` 选项，或使用 `--network` 指定网络来避免 Docker 自动生成 DNAT 规则。

例如：

```bash
# 不使用 -p，Docker 就不会生成 DNAT 规则
docker run --network host -d my-container
```

------

### 🔹 方法 3：在 `DOCKER` 链中删除 Docker 的 DNAT 规则

👉 直接删除 Docker 生成的规则（会在下次重启 Docker 时恢复）：

```bash
# 查看 DOCKER 链
sudo iptables -t nat -L DOCKER --line-numbers
# 删除特定规则（例如第8条）
sudo iptables -t nat -D DOCKER 8
```

------

## ✅ **总结**

- Docker 的 DNAT 规则优先级更高，因为它在 `PREROUTING` 触发，而 `INPUT` 规则在之后才会触发。
- 最有效的解决方法是：
  - 在 `PREROUTING` 链中插入 `DROP` 规则，优先于 Docker 的 DNAT 规则。
  - 或者直接禁用 Docker 的自动端口映射。
  - 也可以删除 Docker 自动创建的 DNAT 规则。
- **推荐方法：方法 1（PREROUTING 中插入 DROP 规则）最为直接有效。** 🔥