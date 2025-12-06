# 📘 Experiment Report: Network Anomaly Evaluation Using Mininet

---
> **Name:** Evaluating the Impact of Network Anomalies on Traffic Performance Using Mininet  
> **ID:** `FN-20251206-network-01`  
> **Topic ｜ MVP:** `FN` | `network` ｜ MVP-0.0 ~ MVP-2.1  
> **Author:** Viska Wei  
> **Date:** 2025-12-06  
> **Project:** `FutureNetwork`  
> **Status:** 🔄 In Progress
---

## 🔗 Upstream Links

| Type | Link | Description |
|------|------|-------------|
| 🧠 Hub | [`network_hub_20251206.md`](./network_hub_20251206.md) | Hypothesis: H1, H2 |
| 🗺️ Roadmap | [`network_roadmap_20251206.md`](./network_roadmap_20251206.md) | MVP design |
| 📋 Kanban | [`kanban.md`](../../_backend/status/kanban.md) | Experiment queue |

---

# 📑 Table of Contents

- [⚡ Key Findings](#-key-findings-for-hub-extraction)
- [1. 🎯 Objective](#1--objective)
- [2. 🧪 Experiment Design](#2--experiment-design)
- [3. 📊 Figures & Results](#3--figures--results)
- [4. 💡 Insights](#4--insights)
- [5. 📝 Conclusions](#5--conclusions)
- [6. 📎 Appendix](#6--appendix)

---

## ⚡ 核心结论速览（供 Hub 提取）

> **本节在实验完成后第一时间填写。**
> **30行内应该有关键信息**

### 一句话总结

> **[TODO: 实验完成后填写 - 用一句话概括本实验最重要的发现，包含关键数字]**

### 对假设的验证

| 验证问题 | 结果 | 结论 |
|---------|------|------|
| H1: Anomalies measurably impact performance | ⏳ | TODO |
| H1.1: TCP throughput drops >50% at 10% loss | ⏳ | TODO |
| H1.2: RTT scales linearly with delay | ⏳ | TODO |
| H2.1: UDP loss matches injected loss | ⏳ | TODO |
| H2.2: HTTP shows compounded effects | ⏳ | TODO |

### 设计启示（1-2 条）

| 启示 | 具体建议 |
|------|---------|
| [TODO] | [TODO] |
| [TODO] | [TODO] |

### 关键数字

| 指标 | 值 |
|------|-----|
| TCP Throughput @ 10% loss | [TODO] |
| RTT @ 50ms delay | [TODO] |
| HTTP download time degradation | [TODO] |

---

# 1. 🎯 目标

## 1.1 实验目的

**核心问题**：How do network anomalies (packet loss, delay, jitter, bandwidth drops) quantitatively impact traffic performance in TCP, UDP, and HTTP?

**Motivation**：
- Real-world networks exhibit anomalies such as packet loss, delay, jitter, bandwidth drops, and random corruption
- These conditions significantly affect the performance of latency-sensitive and throughput-sensitive applications
- Need a controlled, reproducible environment to quantitatively analyze how different anomalies influence traffic patterns

**回答的问题**：
- Q1: How does packet loss affect TCP/UDP throughput?
- Q2: How do delay and jitter impact RTT and latency-sensitive apps?
- Q3: How do bandwidth limits constrain throughput?
- Q4: How do anomalies compound at the application layer (HTTP)?

**对应假设**：
- 验证假设：H1 (Anomalies have measurable impact)
- 验证假设：H2 (Different protocols respond differently)

## 1.2 预期结果

| 场景 | 预期结果 | 判断标准 |
|------|---------|---------|
| TCP @ 10% loss | Throughput drops >50% | Due to cwnd collapse |
| TCP @ 20% loss | Throughput drops >80% | Severe cwnd limitation |
| UDP @ any loss | Loss rate ≈ injected rate | No retransmission |
| RTT @ delay | RTT = baseline + 2×delay | Round-trip adds delay twice |
| HTTP @ combined | Download time >2× baseline | TCP + retransmit overhead |

---

# 2. 🧪 实验设计

## 2.1 测试环境

| 配置项 | 值 |
|--------|-----|
| **平台** | Mininet (Linux-based network emulator) |
| **拓扑** | Simple: Host1 -- Switch -- Host2 |
| **链路** | Virtual Ethernet (veth pairs) |
| **异常注入** | tc netem + tbf |
| **测量工具** | iperf3, ping, curl/wget |

**网络拓扑**：

```
┌──────────┐                           ┌──────────┐
│  Host1   │──────[ s1-eth1 ]──────────│  Host2   │
│ (Server) │        Switch             │ (Client) │
│ 10.0.0.1 │                           │ 10.0.0.2 │
└──────────┘                           └──────────┘
        ↑                                    ↑
    iperf3 -s                           iperf3 -c
    HTTP server                         curl/wget
                                        ping
```

## 2.2 异常注入方法

### tc netem 命令参考

```bash
# Packet Loss
tc qdisc add dev s1-eth1 root netem loss 5%

# Delay with Jitter
tc qdisc add dev s1-eth1 root netem delay 50ms 10ms

# Bandwidth Limit (via tbf)
tc qdisc add dev s1-eth1 root tbf rate 10mbit burst 32kbit latency 400ms

# Combined
tc qdisc add dev s1-eth1 root netem loss 5% delay 50ms

# Clear
tc qdisc del dev s1-eth1 root
```

### 异常参数配置

| 异常类型 | 参数范围 | 说明 |
|---------|---------|------|
| **Packet Loss** | 0%, 1%, 5%, 10%, 20% | 随机丢包 |
| **Delay** | 0, 10, 25, 50, 100 ms | 固定延迟 |
| **Jitter** | ±10ms (with delay) | 延迟波动 |
| **Bandwidth** | 1, 5, 10 Mbps | 带宽限制 |
| **Corruption** | 0.1%, 1% (optional) | 比特翻转 |
| **Reordering** | 25% (optional) | 乱序 |

## 2.3 测量工具与方法

### iperf3 (TCP/UDP Throughput)

```bash
# Server
iperf3 -s

# Client - TCP
iperf3 -c 10.0.0.1 -t 30 -i 1

# Client - UDP (100Mbps target)
iperf3 -c 10.0.0.1 -u -b 100M -t 30 -i 1
```

**采集指标**：
- TCP: Throughput (Mbps), Retransmits, Cwnd
- UDP: Throughput (Mbps), Jitter, Lost/Total datagrams

### ping (Latency/Jitter)

```bash
ping -c 100 10.0.0.1
```

**采集指标**：
- RTT: min/avg/max/mdev
- Packet loss %

### curl/wget (HTTP Performance)

```bash
# Server: Simple HTTP server
python3 -m http.server 8000

# Client: Download with timing
curl -o /dev/null -w "time_total: %{time_total}\n" http://10.0.0.1:8000/testfile_1mb
```

**采集指标**：
- Total download time
- Transfer speed

## 2.4 评价指标

| 指标 | 公式/定义 | 用途 |
|------|----------|------|
| **TCP Throughput** | iperf3 reported Mbps | 主要性能指标 |
| **UDP Throughput** | iperf3 reported Mbps | UDP性能 |
| **UDP Loss Rate** | Lost packets / Total packets | UDP可靠性 |
| **RTT** | ping round-trip time (ms) | 延迟指标 |
| **Jitter** | RTT variation (mdev) | 延迟稳定性 |
| **HTTP Download Time** | curl time_total (s) | 应用层性能 |
| **Throughput Ratio** | Measured / Baseline | 相对性能降级 |

---

# 以下章节实验完成后填写

## 3. 📊 实验图表

> **TODO: 实验完成后添加图表**

### 图 1：TCP Throughput vs Packet Loss Rate

![图片](./img/tcp_throughput_vs_loss.png)

**Figure 1. TCP throughput degradation as packet loss increases**

**关键观察**：
- [TODO]
- [TODO]

---

### 图 2：RTT vs Injected Delay

![图片](./img/rtt_vs_delay.png)

**Figure 2. RTT correlation with injected delay**

**关键观察**：
- [TODO]

---

### 图 3：UDP Loss Rate vs Injected Loss

![图片](./img/udp_loss_correlation.png)

**Figure 3. UDP measured loss vs injected loss correlation**

**关键观察**：
- [TODO]

---

### 图 4：HTTP Download Time Under Anomalies

![图片](./img/http_download_time.png)

**Figure 4. HTTP download time under various anomaly conditions**

**关键观察**：
- [TODO]

---

# 4. 💡 关键洞见

> **TODO: 实验完成后填写**

## 4.1 宏观层洞见

> 用于指导架构设计、理解问题本质的高层次发现。

[TODO]

## 4.2 协议层洞见

> TCP vs UDP vs HTTP 的不同响应特性。

[TODO]

## 4.3 实验层细节洞见

> 具体的实验观察和技术细节。

[TODO]

---

# 5. 📝 结论

## 5.1 核心发现

> **TODO: 实验完成后填写**

**假设验证**：
- ⏳ H1.1: TCP throughput @ 10% loss → ?
- ⏳ H1.2: RTT linear with delay → ?
- ⏳ H2.1: UDP loss matches injection → ?
- ⏳ H2.2: HTTP shows compounding → ?

## 5.2 关键结论（2-4 条）

| # | 结论 | 证据 |
|---|------|------|
| 1 | **[TODO]** | [TODO] |
| 2 | **[TODO]** | [TODO] |
| 3 | **[TODO]** | [TODO] |

## 5.3 设计启示

### 网络设计原则

| 原则 | 建议 | 原因 |
|------|------|------|
| [TODO] | [TODO] | [TODO] |

### ⚠️ 常见陷阱

| 常见做法 | 实验证据 |
|----------|----------|
| [TODO] | [TODO] |

## 5.4 关键数字速查

| 指标 | 值 | 配置/条件 |
|------|-----|----------|
| TCP throughput @ 5% loss | [TODO] | iperf3 30s |
| TCP throughput @ 10% loss | [TODO] | iperf3 30s |
| RTT slope | [TODO] | ms RTT per ms delay |
| HTTP degradation @ 5%+50ms | [TODO] | curl 1MB file |

## 5.5 下一步工作

> 基于本实验结果，建议的后续方向。

| 方向 | 具体任务 | 优先级 | 对应 MVP |
|------|----------|--------|---------|
| Congestion Control Comparison | Test CUBIC vs BBR under loss | 🟡 P1 | Future |
| ABR Streaming | Video streaming under anomalies | 🟢 P2 | Future |
| Real Network Validation | Compare Mininet vs real network | 🟢 P2 | Future |

---

# 6. 📎 附录

## 6.1 数值结果表

> **TODO: 实验完成后填写完整数据**

### 6.1.1 Baseline Results (MVP-0.0)

| 指标 | 值 | 工具 |
|------|-----|------|
| TCP Throughput | [TODO] Mbps | iperf3 |
| UDP Throughput | [TODO] Mbps | iperf3 -u |
| RTT | [TODO] ms | ping |
| HTTP Download (1MB) | [TODO] s | curl |

### 6.1.2 Packet Loss Sweep (MVP-1.0)

| Loss Rate | TCP Throughput | UDP Throughput | UDP Loss | Ratio vs Baseline |
|-----------|----------------|----------------|----------|-------------------|
| 0% | [TODO] | [TODO] | [TODO] | 1.00 |
| 1% | [TODO] | [TODO] | [TODO] | [TODO] |
| 5% | [TODO] | [TODO] | [TODO] | [TODO] |
| 10% | [TODO] | [TODO] | [TODO] | [TODO] |
| 20% | [TODO] | [TODO] | [TODO] | [TODO] |

### 6.1.3 Delay Sweep (MVP-1.1)

| Delay (ms) | RTT (ms) | Jitter (ms) | TCP Throughput |
|------------|----------|-------------|----------------|
| 0 | [TODO] | [TODO] | [TODO] |
| 10 | [TODO] | [TODO] | [TODO] |
| 25 | [TODO] | [TODO] | [TODO] |
| 50 | [TODO] | [TODO] | [TODO] |
| 100 | [TODO] | [TODO] | [TODO] |

### 6.1.4 Bandwidth Limit (MVP-1.2)

| Limit (Mbps) | TCP Throughput | UDP Throughput |
|--------------|----------------|----------------|
| 1 | [TODO] | [TODO] |
| 5 | [TODO] | [TODO] |
| 10 | [TODO] | [TODO] |

### 6.1.5 HTTP Performance (MVP-2.0)

| Condition | Download Time (s) | Ratio vs Baseline |
|-----------|-------------------|-------------------|
| Baseline | [TODO] | 1.00 |
| 5% loss | [TODO] | [TODO] |
| 50ms delay | [TODO] | [TODO] |
| 5% + 50ms | [TODO] | [TODO] |

---

## 6.2 实验流程记录

### 6.2.1 环境与配置

| 项目 | 值 |
|------|-----|
| **平台** | Ubuntu 20.04+ / WSL2 |
| **Mininet** | 2.3.0+ (系统级安装) |
| **iperf3** | 3.x |
| **Python** | 3.8+ (系统 Python) |

**🚀 快速启动**：
```bash
# 1. 安装 Mininet (Linux only, 系统级)
sudo apt install mininet iperf3 curl

# 2. 测试拓扑
sudo mn --topo single,2

# 3. 运行 baseline
cd network/scripts
sudo python3 run_baseline.py
```

> ⚠️ **Note**: Mininet 是系统级工具，不需要 conda/virtualenv

### 6.2.2 执行命令

```bash
# Step 1: 启动 Mininet
sudo mn --topo single,2

# Step 2: 在 h1 启动服务
mininet> h1 iperf3 -s &
mininet> h1 python3 -m http.server 8000 &

# Step 3: Baseline 测试
mininet> h2 iperf3 -c h1 -t 30
mininet> h2 iperf3 -c h1 -u -b 100M -t 30
mininet> h2 ping -c 100 h1
mininet> h2 curl -o /dev/null -w "%{time_total}" http://h1:8000/testfile

# Step 4: 注入异常（示例：5% loss）
mininet> sh tc qdisc add dev s1-eth1 root netem loss 5%

# Step 5: 带异常测试
mininet> h2 iperf3 -c h1 -t 30

# Step 6: 清除异常
mininet> sh tc qdisc del dev s1-eth1 root
```

### 6.2.3 自动化脚本框架

```python
#!/usr/bin/env python3
"""
Network Anomaly Evaluation Script
Automates Mininet tests with tc netem
"""

from mininet.net import Mininet
from mininet.node import Controller
from mininet.topo import SingleSwitchTopo
from mininet.link import TCLink
import subprocess
import json
import time

# Anomaly configurations
LOSS_RATES = [0, 1, 5, 10, 20]  # percent
DELAYS = [0, 10, 25, 50, 100]   # ms
BANDWIDTHS = [1, 5, 10]         # Mbps

def run_experiment():
    # Create topology
    topo = SingleSwitchTopo(2)
    net = Mininet(topo=topo, link=TCLink, controller=Controller)
    net.start()
    
    h1, h2 = net.get('h1', 'h2')
    
    # Start servers on h1
    h1.cmd('iperf3 -s -D')
    h1.cmd('cd /tmp && python3 -m http.server 8000 &')
    time.sleep(1)
    
    results = {'baseline': {}, 'loss': {}, 'delay': {}, 'bandwidth': {}}
    
    # TODO: Implement test loops
    # ...
    
    net.stop()
    return results

if __name__ == '__main__':
    results = run_experiment()
    print(json.dumps(results, indent=2))
```

---

## 6.3 相关文件

| 类型 | 路径 | 说明 |
|------|------|------|
| Hub | `logg/network/network_hub_20251206.md` | 假设金字塔 |
| Roadmap | `logg/network/network_roadmap_20251206.md` | MVP 设计 |
| 本报告 | `logg/network/exp_network_anomaly_mininet_20251206.md` | 当前文件 |
| 图表 | `logg/network/img/` | 实验图表 |
| 脚本 | `logg/network/scripts/` | 自动化脚本 |

---

## 6.4 预期产出

本实验完成后将产出：

1. **量化数据**：
   - TCP throughput vs loss rate 曲线
   - RTT vs delay 线性关系
   - UDP loss correlation
   - HTTP performance degradation curves

2. **可复用框架**：
   - Mininet-based "network anomaly evaluation" testbed
   - Automated test scripts
   - Data collection and plotting tools

3. **教学/研究价值**：
   - Results useful for teaching network fundamentals
   - Demo for congestion control, ABR streaming research
   - Baseline for further network optimization studies

---

## 🔗 Cross-Repo Metadata

| Field | Value |
|-------|-------|
| **experiment_id** | `FN-20251206-network-01` |
| **project** | FutureNetwork |
| **topic** | network |
| **source_repo_path** | `logg/network/` |
| **output_path** | `logg/network/results/` |

---

> **模板使用说明**：
> 
> **工作流程**：
> 1. **实验前**：§1（目标）、§2（实验设计）已填写 ✅
> 2. **实验中**：记录结果到 §6.1，添加图表到 §3，记录流程到 §6.2
> 3. **实验后**：填写 §4（洞见）、§5（结论）
> 4. **最后**：填写 ⚡核心结论速览，同步到 hub.md
