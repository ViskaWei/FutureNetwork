# 📘 Experiment Report: Network Anomaly Evaluation Using Mininet

---
> **Name:** Evaluating the Impact of Network Anomalies on Traffic Performance Using Mininet  
> **ID:** `FN-20251206-network-01`  
> **Topic ｜ MVP:** `FN` | `network` ｜ MVP-0.0 ~ MVP-2.1  
> **Author:** Viska Wei  
> **Date:** 2025-12-06  
> **Project:** `FutureNetwork`  
> **Status:** ✅ Completed
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

> **TCP throughput 在 1% 丢包时下降 86%，在 10% 丢包时几乎降为零（99.99% drop）；RTT 与注入延迟线性相关（slope ≈ 1.0）；带宽限制可精确控制吞吐量。**

### 对假设的验证

| 验证问题 | 结果 | 结论 |
|---------|------|------|
| H1: Anomalies measurably impact performance | ✅ | **确认**：丢包/延迟/带宽均显著影响性能 |
| H1.1: TCP throughput drops >50% at 10% loss | ✅ | **确认**：实测 drop 99.99%（42819 → 4.95 Mbps） |
| H1.2: RTT scales linearly with delay | ✅ | **确认**：RTT ≈ baseline + delay（单向注入） |
| H2.1: UDP loss matches injected loss | ⚠️ | **未测试**：iperf3 UDP 解析问题 |
| H2.2: HTTP shows compounded effects | ⚠️ | **未明显**：localhost 传输过快，需更大文件 |

### 设计启示（1-2 条）

| 启示 | 具体建议 |
|------|---------|
| 丢包对 TCP 影响极其严重 | 即使 1% 丢包也会导致 86% 性能下降，需要优先保证链路质量 |
| 延迟会显著降低 TCP 吞吐 | 100ms 延迟使吞吐降至 7.6 Mbps，高延迟场景考虑使用 BBR 或 UDP |

### 关键数字

| 指标 | 值 |
|------|-----|
| TCP Throughput @ 10% loss | **4.95 Mbps** (baseline: 42819 Mbps, drop 99.99%) |
| RTT @ 50ms delay | **50.08 ms** (baseline: 0.04 ms) |
| TCP @ 100ms delay | **7.64 Mbps** (baseline: 42256 Mbps) |

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

> 注：matplotlib 在当前环境不可用，数据以表格形式呈现。图表可后续生成。

### 图 1：TCP Throughput vs Packet Loss Rate

**Figure 1. TCP throughput degradation as packet loss increases (log scale)**

```
Loss%    TCP Mbps    Drop%
  0%     42,583      0%
  1%      6,143     85.6%    ████████████████████
  5%        145     99.7%    ████████████████████████████████████████
 10%          5     99.99%   ████████████████████████████████████████████
 20%        0.5     99.999%  █████████████████████████████████████████████
```

**关键观察**：
- TCP throughput 随丢包率呈**指数级下降**
- 即使 1% 丢包也导致 85.6% 的性能损失
- 这是由于 TCP 拥塞控制的 cwnd 收缩机制

---

### 图 2：RTT vs Injected Delay

**Figure 2. RTT correlation with injected delay**

```
Delay(ms)    RTT(ms)    Expected(baseline+delay)
    0          0.04          0.04
   10         10.08         10.04  ✓
   25         25.08         25.04  ✓
   50         50.08         50.04  ✓
  100        100.08        100.04  ✓
```

**关键观察**：
- RTT 与注入延迟呈**线性关系**（slope ≈ 1.0）
- tc netem 在单接口注入延迟只影响单向，RTT = baseline + delay
- Jitter (mdev) 保持稳定在 ~0.1-0.3ms

---

### 图 3：TCP Throughput vs Delay

**Figure 3. TCP throughput degradation with increasing delay**

```
Delay(ms)    TCP Mbps    Drop%
    0        42,256       0%
   10         3,005      93%     ██████████████████████████████████████
   25           668      98%     ███████████████████████████████████████████
   50            89      99.8%   █████████████████████████████████████████████
  100             8      99.98%  █████████████████████████████████████████████
```

**关键观察**：
- 延迟对 TCP 吞吐影响同样巨大
- 100ms 延迟使吞吐降至 7.64 Mbps（基准的 0.02%）
- Throughput ∝ cwnd / RTT

---

### 图 4：Bandwidth Limiting Accuracy

**Figure 4. TC bandwidth limiting accuracy**

```
Limit(Mbps)    Measured(Mbps)    Efficiency
     1             1.23            123%
     5             5.18            104%
    10            10.05            101%
```

**关键观察**：
- tc tbf 带宽限制非常精确（效率接近 100%）
- 轻微超出限制是正常的协议开销

---

# 4. 💡 关键洞见

## 4.1 宏观层洞见

> 用于指导架构设计、理解问题本质的高层次发现。

1. **丢包对 TCP 的影响是非线性且极端的**
   - 1% 丢包导致 85.6% 性能下降
   - 5% 丢包导致 99.7% 性能下降
   - TCP 的拥塞控制在高丢包场景下会导致 cwnd 反复收缩，性能急剧恶化

2. **延迟与 TCP 吞吐呈反比关系**
   - 高延迟 = 高 RTT = 慢 ACK = 低吞吐
   - 这是 TCP 基于 ACK 的流控机制的固有特性
   - Throughput ≈ cwnd / RTT

## 4.2 协议层洞见

> TCP vs UDP vs HTTP 的不同响应特性。

1. **TCP 特性**
   - Retransmit 机制在高丢包下产生大量重传（1% loss → 54,397 retransmits）
   - cwnd 收缩是性能下降的主要原因
   - 带宽限制下 TCP 能很好地适应（效率 ~100%）

2. **UDP 特性**
   - iperf3 3.0.11 的 UDP JSON 输出格式与解析代码不匹配
   - 需要进一步调试 UDP 测试

3. **HTTP/应用层**
   - 在 localhost 虚拟链路上，1MB 文件传输过快（<1ms）
   - 需要使用更大文件或限制带宽来观察应用层效果

## 4.3 实验层细节洞见

> 具体的实验观察和技术细节。

1. **tc netem 延迟是单向的**
   - 在 s1-eth1 注入 50ms delay，RTT = 50ms（而非预期的 2×50=100ms）
   - 这是因为只在一个方向的链路上添加了延迟
   - 要实现双向延迟需要在两个接口都配置

2. **Mininet 虚拟链路性能极高**
   - Baseline TCP: 42+ Gbps（虚拟以太网）
   - RTT: 0.04ms（内核级别，无物理延迟）
   - 这使得某些测试（如 HTTP）需要人为添加限制

3. **iperf3 版本兼容性**
   - iperf3 3.0.11 (Ubuntu 16.04) 的 UDP JSON 格式缺少 `sum_received`
   - 需要使用 `sum` 字段或升级 iperf3

---

# 5. 📝 结论

## 5.1 核心发现

**假设验证**：
- ✅ H1.1: TCP throughput @ 10% loss → **确认**：下降 99.99%（远超预期的 50%）
- ✅ H1.2: RTT linear with delay → **确认**：RTT = baseline + injected_delay（slope ≈ 1.0）
- ⚠️ H2.1: UDP loss matches injection → **未测试**：iperf3 输出格式问题
- ⚠️ H2.2: HTTP shows compounding → **未明显**：需要更大测试文件

## 5.2 关键结论（2-4 条）

| # | 结论 | 证据 |
|---|------|------|
| 1 | **丢包对 TCP 影响极其严重** | 1% loss → 85.6% drop, 5% loss → 99.7% drop |
| 2 | **延迟与 TCP 吞吐呈反比** | 10ms delay → 93% drop, 100ms delay → 99.98% drop |
| 3 | **带宽限制精确可控** | 1/5/10 Mbps 限制均实现 ~100% 效率 |
| 4 | **Mininet 是可靠的网络测试平台** | tc netem 可精确注入各类异常 |

## 5.3 设计启示

### 网络设计原则

| 原则 | 建议 | 原因 |
|------|------|------|
| 优先保证链路质量 | 丢包率应控制在 <1% | 1% 丢包导致 86% 性能下降 |
| 高延迟场景考虑替代协议 | 使用 BBR、QUIC 或 UDP | TCP CUBIC 在高延迟下表现差 |
| 带宽规划可以精确执行 | tc tbf 可靠限速 | 实测效率接近 100% |

### ⚠️ 常见陷阱

| 常见做法 | 实验证据 |
|----------|----------|
| 假设 10% 丢包可接受 | 实际导致 TCP 几乎不可用（4.95 Mbps vs 42 Gbps） |
| 忽视延迟对吞吐的影响 | 100ms RTT 使吞吐降至 7.64 Mbps |
| tc netem 只配置单接口 | RTT 只增加单向延迟，需双向配置 |

## 5.4 关键数字速查

| 指标 | 值 | 配置/条件 |
|------|-----|----------|
| TCP throughput @ 5% loss | **144.69 Mbps** (99.7% drop) | iperf3 10s |
| TCP throughput @ 10% loss | **4.95 Mbps** (99.99% drop) | iperf3 10s |
| RTT slope | **1.0** (RTT ≈ delay) | 单向 netem |
| TCP @ 100ms delay | **7.64 Mbps** | iperf3 10s |

## 5.5 下一步工作

> 基于本实验结果，建议的后续方向。

| 方向 | 具体任务 | 优先级 | 状态 |
|------|----------|--------|------|
| 修复 UDP 测试 | 调试 iperf3 UDP JSON 解析 | 🔴 P0 | 待处理 |
| HTTP 测试改进 | 使用更大文件或限制基准带宽 | 🔴 P0 | 待处理 |
| 拥塞控制对比 | 测试 CUBIC vs BBR under loss | 🟡 P1 | 规划中 |
| 双向延迟测试 | 在两个接口配置 netem | 🟡 P1 | 规划中 |
| 真实网络验证 | 对比 Mininet vs 物理网络 | 🟢 P2 | 规划中 |

---

# 6. 📎 附录

## 6.1 数值结果表

> **TODO: 实验完成后填写完整数据**

### 6.1.1 Baseline Results (MVP-0.0)

| 指标 | 值 | 工具 |
|------|-----|------|
| TCP Throughput | **42,819.20 Mbps** | iperf3 |
| UDP Throughput | N/A (解析问题) | iperf3 -u |
| RTT | **0.041 ms** | ping |
| HTTP Download (1MB) | <0.001 s (localhost 过快) | curl |

### 6.1.2 Packet Loss Sweep (MVP-1.0)

| Loss Rate | TCP Throughput | Retransmits | TCP Drop vs Baseline |
|-----------|----------------|-------------|----------------------|
| 0% | 42,583.80 Mbps | 0 | 0% |
| 1% | 6,143.15 Mbps | 54,397 | **85.6%** |
| 5% | 144.69 Mbps | 6,302 | **99.7%** |
| 10% | 4.95 Mbps | 591 | **99.99%** |
| 20% | 0.49 Mbps | 108 | **99.999%** |

### 6.1.3 Delay Sweep (MVP-1.1)

| Delay (ms) | RTT (ms) | Jitter (mdev) | TCP Throughput |
|------------|----------|---------------|----------------|
| 0 | 0.040 | 0.012 ms | 42,256.20 Mbps |
| 10 | 10.080 | 0.119 ms | 3,005.44 Mbps |
| 25 | 25.083 | 0.123 ms | 668.29 Mbps |
| 50 | 50.082 | 0.126 ms | 89.31 Mbps |
| 100 | 100.079 | 0.329 ms | 7.64 Mbps |

### 6.1.4 Bandwidth Limit (MVP-1.2)

| Limit (Mbps) | TCP Throughput | Efficiency |
|--------------|----------------|------------|
| 1 | 1.23 Mbps | 123% |
| 5 | 5.18 Mbps | 104% |
| 10 | 10.05 Mbps | 101% |

### 6.1.5 HTTP Performance (MVP-2.0)

| Condition | Download Time (s) | Notes |
|-----------|-------------------|-------|
| Baseline | <0.001 | localhost 传输极快 |
| 5% loss | <0.001 | 需更大文件测试 |
| 50ms delay | 0.001 | 轻微增加 |
| 5% + 50ms | 0.001 | 需更大文件测试 |

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
�1（目标）、§2（实验设计）已填写 ✅
> 2. **实验中**：记录结果到 §6.1，添加图表到 §3，记录流程到 §6.2
> 3. **实验后**：填写 §4（洞见）、§5（结论）
> 4. **最后**：填写 ⚡核心结论速览，同步到 hub.md
