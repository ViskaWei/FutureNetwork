# 🧠 智库导航（Hub）- Network Anomaly Evaluation

---
> **主题名称：** Network Anomaly Impact Analysis  
> **作者：** Viska Wei  
> **创建日期：** 2025-12-06  
> **最后更新：** 2025-12-06  
> **状态：** 🔄 探索中

---

## 🔗 相关文件

| 类型 | 文件 | 说明 |
|------|------|------|
| 📍 Roadmap | [`network_roadmap_20251206.md`](./network_roadmap_20251206.md) | 实验追踪与执行 |
| 📗 子实验 | `exp_*.md` | 单实验详情 |
| 📇 知识卡片 | `card_*.md` | 浓缩结论 |

---

# 📑 目录

- [1. 🌲 核心问题树](#1--核心问题树)
- [2. 🔺 假设金字塔](#2--假设金字塔)
- [3. 💡 洞见汇合站](#3--洞见汇合站)
- [4. 🧭 战略导航](#4--战略导航)
- [5. 📐 设计原则库](#5--设计原则库)
- [6. 📎 附录](#6--附录)

---

# 1. 🌲 核心问题树

> **用树状结构展示问题的从属关系，明确研究边界**

## 1.1 顶层问题

> **How do network anomalies (packet loss, delay, jitter, bandwidth drops) quantitatively impact traffic performance in TCP, UDP, and application-layer protocols?**

## 1.2 问题分解

```
🎯 顶层问题: How do network anomalies impact traffic performance?
│
├── Q1: TCP Sensitivity
│   ├── Q1.1: How does packet loss affect TCP throughput? → ⏳ 待验证 [MVP-1.0]
│   ├── Q1.2: At what loss rate does cwnd collapse occur? → ⏳ 待验证 [MVP-1.0]
│   └── Q1.3: How does delay affect TCP goodput? → ⏳ 待验证 [MVP-1.1]
│
├── Q2: UDP Behavior
│   ├── Q2.1: How does UDP loss correlate with injected loss? → ⏳ 待验证 [MVP-1.0]
│   └── Q2.2: What is the jitter impact on UDP streams? → ⏳ 待验证 [MVP-1.1]
│
├── Q3: Latency & Jitter
│   ├── Q3.1: How accurately does injected delay translate to measured RTT? → ⏳ 待验证 [MVP-1.1]
│   └── Q3.2: What is the jitter distribution under various conditions? → ⏳ 待验证 [MVP-1.1]
│
└── Q4: Application Layer (HTTP)
    ├── Q4.1: How do anomalies compound at application layer? → ⏳ 待验证 [MVP-2.0]
    └── Q4.2: What anomalies most affect download time? → ⏳ 待验证 [MVP-2.0]

状态图例:
✅ 已验证 | ❌ 已否定 | 🔄 进行中 | ⏳ 待验证 | 🚫 已关闭（不再追问）
```

## 1.3 问题边界

> **明确本研究「做什么」和「不做什么」**

| ✅ 本研究关注 | ❌ 本研究不关注 |
|-------------|---------------|
| Mininet模拟环境下的网络异常 | 真实生产环境部署 |
| TCP/UDP/HTTP基础协议性能 | 复杂应用层协议（QUIC, WebRTC等） |
| iperf3/ping/curl标准工具测量 | 自定义协议栈性能 |
| 可量化、可复现的异常注入 | 硬件故障模拟 |
| 单链路异常分析 | 多路径路由/负载均衡 |

---

# 2. 🔺 假设金字塔

> **从宏观战略假设 → 中观战术假设 → 微观可验证假设，层层递进**

## 2.1 L1 宏观假设（战略层）

> **决定整个研究方向的核心信念**

| # | 宏观假设 | 验证状态 | 如果成立 | 如果不成立 |
|---|---------|---------|---------|-----------|
| **H1** | Network anomalies have measurable, reproducible impact on traffic performance | ⏳ | Mininet testbed is valid for network research | Need real hardware testing |
| **H2** | Different protocols (TCP/UDP/HTTP) respond differently to the same anomaly | ⏳ | Protocol-specific optimizations possible | Universal mitigation strategy |

## 2.2 L2 中观假设（战术层）

> **宏观假设的具体实现路径**

| # | 中观假设 | 上层假设 | 验证状态 | 关键实验 |
|---|---------|---------|---------|---------|
| **H1.1** | Packet loss causes significant TCP throughput degradation (cwnd collapse) | H1 | ⏳ | MVP-1.0 |
| **H1.2** | Delay and jitter directly impact end-to-end latency measurements | H1 | ⏳ | MVP-1.1 |
| **H1.3** | Bandwidth limits create hard throughput ceilings | H1 | ⏳ | MVP-1.2 |
| **H2.1** | UDP loss rate matches injected loss rate (no retransmission) | H2 | ⏳ | MVP-1.0 |
| **H2.2** | HTTP performance shows compounded effects of multiple anomalies | H2 | ⏳ | MVP-2.0 |

## 2.3 L3 微观假设（可验证层）

> **每个假设对应一个具体实验，有明确的验收标准**

| # | 可验证假设 | 上层假设 | 验证标准 | 结果 | 来源 |
|---|-----------|---------|---------|------|------|
| **H1.1.1** | TCP throughput drops by >50% at 10% packet loss | H1.1 | Throughput ≤ 0.5× baseline | ⏳ | MVP-1.0 |
| **H1.1.2** | TCP throughput drops >80% at 20% packet loss | H1.1 | Throughput ≤ 0.2× baseline | ⏳ | MVP-1.0 |
| **H1.2.1** | Measured RTT increases linearly with injected delay | H1.2 | R² ≥ 0.95 for RTT vs delay | ⏳ | MVP-1.1 |
| **H1.2.2** | Jitter distribution follows injected ±variance | H1.2 | Measured jitter ≈ injected ±10% | ⏳ | MVP-1.1 |
| **H1.3.1** | Throughput saturates at bandwidth limit | H1.3 | Max throughput ≈ limit ±5% | ⏳ | MVP-1.2 |
| **H2.1.1** | UDP packet loss rate = injected loss rate ±2% | H2.1 | Measured loss ≈ injected | ⏳ | MVP-1.0 |
| **H2.2.1** | HTTP download time increases >3× at 10% loss + 100ms delay | H2.2 | Download time ≥ 3× baseline | ⏳ | MVP-2.0 |

## 2.4 假设依赖图

```
┌─────────────────────────────────────────────────────────────┐
│                      假设金字塔依赖图                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   L1: [H1 Anomalies Impact]          [H2 Protocol Diff]     │
│            │                              │                 │
│            ├─────────┬─────────┐          │                 │
│            ▼         ▼         ▼          ▼                 │
│   L2:  [H1.1]     [H1.2]    [H1.3]     [H2.1]    [H2.2]     │
│       PktLoss    Delay/Jit  Bandwidth   UDP       HTTP      │
│            │         │         │          │          │      │
│            ▼         ▼         ▼          ▼          ▼      │
│   L3: [H1.1.1]   [H1.2.1]  [H1.3.1]   [H2.1.1]  [H2.2.1]   │
│       [H1.1.2]   [H1.2.2]                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

# 3. 💡 洞见汇合站

> **多个实验的单点发现 → 汇合成高层结论和设计原则**

## 3.1 汇合点列表

| # | 汇合主题 | 单点来源 | 汇合结论 | 置信度 |
|---|---------|---------|---------|--------|
| C1 | [待实验完成后填写] | - | - | ⏳ |

## 3.2 汇合详情

> **实验完成后填写**

---

## 3.3 冲突性发现

> **不同实验得出矛盾结论时，记录并分析原因**

| 主题 | 实验 A 结论 | 实验 B 结论 | 可能原因 | 解决方案 |
|------|-----------|-----------|---------|---------|
| - | - | - | - | - |

---

# 4. 🧭 战略导航

> **基于已有洞见，推荐下一步研究方向**

## 4.1 方向状态总览

```
┌───────────────────────────────────────────────────────────────┐
│                        研究方向状态图                           │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│   🟡 待验证方向（Phase 1）                                      │
│   ├── Packet Loss Impact ← MVP-1.0                            │
│   ├── Delay/Jitter Impact ← MVP-1.1                           │
│   └── Bandwidth Limit Impact ← MVP-1.2                        │
│                                                               │
│   🟡 待验证方向（Phase 2）                                      │
│   ├── HTTP Application Performance ← MVP-2.0                   │
│   └── Combined Anomalies ← MVP-2.1                            │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

## 4.2 待验证方向

| 方向 | 依赖假设 | 需要实验 | 预计收益 |
|------|---------|---------|---------|
| Packet Loss Analysis | H1.1 | MVP-1.0 | 理解TCP敏感性 |
| Delay/Jitter Analysis | H1.2 | MVP-1.1 | 量化延迟影响 |
| Bandwidth Analysis | H1.3 | MVP-1.2 | 确定瓶颈阈值 |
| HTTP Performance | H2.2 | MVP-2.0 | 应用层影响 |

---

# 5. 📐 设计原则库

> **从实验中提炼的、可复用的设计原则**

## 5.1 待验证原则

| # | 原则名称 | 初步建议 | 需要验证 |
|---|---------|---------|---------|
| P1 | Loss Rate Threshold | TCP may need <5% loss for acceptable performance | MVP-1.0 |
| P2 | Delay Budget | End-to-end delay should consider jitter margin | MVP-1.1 |
| P3 | Bandwidth Planning | Provision bandwidth with overhead for anomalies | MVP-1.2 |

## 5.2 关键数字速查

> **实验完成后填写**

| 指标 | 值 | 条件 | 来源 |
|------|-----|------|------|
| TCP throughput @ 5% loss | TBD | iperf3 baseline | MVP-1.0 |
| RTT @ 50ms delay | TBD | ping baseline | MVP-1.1 |
| Max throughput @ 10Mbps limit | TBD | iperf3 | MVP-1.2 |

---

# 6. 📎 附录

## 6.1 物理/领域背景

### 6.1.1 TCP Congestion Control

TCP uses congestion window (cwnd) to regulate data flow. Packet loss triggers:
- Fast Retransmit (3 duplicate ACKs)
- cwnd halving (multiplicative decrease)
- Slow Start threshold update

At high loss rates, cwnd cannot grow, leading to severely degraded throughput.

### 6.1.2 tc netem

Linux Traffic Control (tc) with Network Emulator (netem) allows:
- `loss N%` - random packet loss
- `delay Xms Yms` - delay with optional jitter
- `rate Xmbit` - bandwidth limiting (via tbf)
- `corrupt N%` - bit flip corruption
- `reorder N%` - packet reordering

### 6.1.3 Mininet

Mininet creates realistic virtual networks using:
- Linux network namespaces
- Virtual Ethernet pairs (veth)
- OpenFlow-enabled switches
- Customizable topologies

---

## 6.2 术语表

| 术语 | 定义 | 备注 |
|------|------|------|
| cwnd | Congestion Window | TCP发送窗口大小 |
| RTT | Round-Trip Time | 数据包往返时间 |
| jitter | Delay variation | 延迟抖动 |
| netem | Network Emulator | tc的网络模拟模块 |
| tbf | Token Bucket Filter | 带宽限制队列 |

---

## 6.3 变更日志

| 日期 | 变更内容 | 影响章节 |
|------|---------|---------|
| 2025-12-06 | 创建 Hub，初始化假设金字塔 | 全部 |

---

> **Hub 的定位**：
> - ✅ **做**：问题梳理、假设管理、洞见汇合、战略导航、设计原则
> - ❌ **不做**：实验执行追踪（→ roadmap.md）、日常 backlog（→ kanban.md）
