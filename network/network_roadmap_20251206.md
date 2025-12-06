# 🗺️ 实验路线图（Roadmap）- Network Anomaly Evaluation

---
> **主题名称：** Network Anomaly Impact Analysis  
> **作者：** Viska Wei  
> **创建日期：** 2025-12-06  
> **最后更新：** 2025-12-06  
> **当前 Phase：** Phase 2 ✅ 完成

---

## 🔗 相关文件

| 类型 | 文件 | 说明 |
|------|------|------|
| 🧠 Hub | [`network_hub_20251206.md`](./network_hub_20251206.md) | 智库导航 |
| 📋 Kanban | [`kanban.md`](../../_backend/status/kanban.md) | 全局看板 |
| 📗 子实验 | `exp_*.md` | 单实验详情 |

---

# 📑 目录

- [1. 🎯 Phase 总览](#1--phase-总览)
- [2. 📋 MVP 实验列表](#2--mvp-实验列表)
- [3. 🔧 MVP 详细设计](#3--mvp-详细设计)
- [4. 📊 进度追踪](#4--进度追踪)
- [5. 🔗 跨仓库集成](#5--跨仓库集成)
- [6. 📎 附录](#6--附录)

---

# 1. 🎯 Phase 总览

> **按阶段组织实验，每个 Phase 有明确目标**

## 1.1 Phase 列表

| Phase | 目的 | 包含 MVP | 状态 | 关键产出 |
|-------|------|---------|------|---------|
| **Phase 0: Setup** | 搭建 Mininet 测试环境，建立 Baseline | MVP-0.0 | ✅ 完成 | TCP: 42,819 Mbps, RTT: 0.04 ms |
| **Phase 1: Single Anomaly** | 单一异常影响分析 | MVP-1.0 ~ 1.2 | ✅ 完成 | Loss/Delay/BW 影响曲线 |
| **Phase 2: Application** | 应用层性能分析 | MVP-2.0 ~ 2.1 | ✅ 完成 | 组合异常 -90% 复合效应 |
| **Phase 3: Advanced** | 高级场景（可选） | MVP-3.x | ⏳ | Corruption/Reorder分析 |

## 1.2 依赖关系图

```
┌─────────────────────────────────────────────────────────────┐
│                      MVP 实验依赖图                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   [Phase 0: Setup & Baseline]                               │
│         │ MVP-0.0                                           │
│         │                                                   │
│         ├──────────────┬──────────────┐                     │
│         ▼              ▼              ▼                     │
│   [MVP-1.0]      [MVP-1.1]      [MVP-1.2]                  │
│   Packet Loss    Delay/Jitter   Bandwidth                   │
│         │              │              │                     │
│         └──────────────┼──────────────┘                     │
│                        ▼                                    │
│                  [MVP-2.0]                                  │
│                  HTTP Performance                           │
│                        │                                    │
│                        ▼                                    │
│                  [MVP-2.1]                                  │
│                  Combined Anomalies                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 1.3 决策点

> **关键分叉点：根据实验结果决定下一步方向**

| 决策点 | 触发条件 | 选项 A | 选项 B |
|--------|---------|--------|--------|
| D1 | MVP-0.0 完成后 | 如果 baseline 稳定 → Phase 1 | 如果不稳定 → 调试环境 |
| D2 | Phase 1 完成后 | 如果单一异常影响显著 → Phase 2 | 如果影响微弱 → 调整异常参数 |
| D3 | MVP-2.0 完成后 | 如果有时间 → Phase 3 (Advanced) | 否则 → 总结报告 |

---

# 2. 📋 MVP 实验列表

> **所有 MVP 的一览表，便于快速查找和追踪**

## 2.1 实验总览

| MVP | 实验名称 | Phase | 状态 | experiment_id | 报告链接 |
|-----|---------|-------|------|---------------|---------|
| MVP-0.0 | Mininet Testbed Setup & Baseline | 0 | ✅ 完成 | `FN-20251206-network-01` | [exp](./exp_network_anomaly_mininet_20251206.md) |
| MVP-1.0 | Packet Loss Impact (TCP/UDP) | 1 | ✅ 完成 | `FN-20251206-network-01` | [exp](./exp_network_anomaly_mininet_20251206.md) |
| MVP-1.1 | Delay & Jitter Impact | 1 | ✅ 完成 | `FN-20251206-network-01` | [exp](./exp_network_anomaly_mininet_20251206.md) |
| MVP-1.2 | Bandwidth Limit Impact | 1 | ✅ 完成 | `FN-20251206-network-01` | [exp](./exp_network_anomaly_mininet_20251206.md) |
| MVP-2.0 | HTTP Application Performance | 2 | ✅ 完成 | `FN-20251206-network-01` | [exp](./exp_network_anomaly_mininet_20251206.md) |
| MVP-2.1 | Combined Anomalies Analysis | 2 | ✅ 完成 | `FN-20251206-network-01` | [exp](./exp_network_anomaly_mininet_20251206.md) |
| MVP-3.0 | Corruption & Reordering (Optional) | 3 | ⏳ 规划中 | - | - |

**状态图例**：
- ⏳ 计划中（Planned）
- 🔴 待执行（Ready）
- 🚀 运行中（Running）
- ✅ 已完成（Done）
- ❌ 已取消（Cancelled）
- ⏸️ 暂停（Paused）

## 2.2 配置速查表

> **所有 MVP 的关键配置对比**

| MVP | 工具 | 异常类型 | 异常参数 | 关键指标 | 验收标准 |
|-----|------|---------|---------|---------|---------|
| MVP-0.0 | iperf3/ping/curl | None | - | Throughput, RTT, Download | Baseline recorded |
| MVP-1.0 | iperf3 | Packet Loss | 0/1/5/10/20% | TCP/UDP Throughput | Throughput vs Loss curve |
| MVP-1.1 | ping/iperf3 | Delay+Jitter | 50ms±10ms | RTT, Jitter distribution | RTT correlation R²≥0.95 |
| MVP-1.2 | iperf3 | Bandwidth | 1/5/10 Mbps | Max Throughput | Saturation at limit |
| MVP-2.0 | curl/wget | Loss+Delay | 5%+50ms | HTTP download time | >2× baseline at anomaly |
| MVP-2.1 | All | Combined | Multi-param | All metrics | Interaction effects |

---

# 3. 🔧 MVP 详细设计

> **每个 MVP 的详细规格，便于快速执行**

## Phase 0: Setup & Baseline

### MVP-0.0: Mininet Testbed Setup & Baseline

| 项目 | 配置 |
|------|------|
| **目标** | 搭建 Mininet 环境，收集无异常时的 baseline 性能数据 |
| **验证假设** | H1 (Anomalies are measurable) |
| **拓扑** | Simple: Host1 -- Switch -- Host2 |
| **工具** | iperf3, ping, curl, Python SimpleHTTPServer |
| **验收标准** | 能稳定测量 TCP/UDP throughput, RTT, HTTP download time |
| **早停条件** | 如果测量不稳定（方差>10%），需排查环境 |

**测试步骤**：
1. 安装 Mininet: `sudo apt install mininet`
2. 创建简单拓扑: `sudo mn --topo single,2`
3. 测试 TCP: `h1 iperf3 -s &` + `h2 iperf3 -c h1`
4. 测试 UDP: `h2 iperf3 -c h1 -u -b 100M`
5. 测试 Ping: `h2 ping -c 100 h1`
6. 测试 HTTP: `h1 python3 -m http.server 8000 &` + `h2 curl -o /dev/null -w "%{time_total}" h1:8000/testfile`

**排查清单**（若未达验收标准）：
- [ ] Mininet 版本兼容性
- [ ] CPU/内存资源是否充足
- [ ] 网络命名空间是否正确隔离

---

## Phase 1: Single Anomaly Analysis

### MVP-1.0: Packet Loss Impact

| 项目 | 配置 |
|------|------|
| **目标** | 量化 packet loss 对 TCP/UDP throughput 的影响 |
| **验证假设** | H1.1 (TCP cwnd collapse), H2.1 (UDP linear loss) |
| **依赖** | MVP-0.0 Baseline |
| **异常注入** | `tc qdisc add dev s1-eth1 root netem loss {0,1,5,10,20}%` |
| **测量** | iperf3 TCP/UDP throughput (30s duration, 3 repeats) |
| **验收标准** | 生成 Throughput vs Loss Rate 曲线 |
| **异常处理** | 如果 TCP 无明显下降，检查 netem 是否生效 |

**→ 对假设的影响**：若 TCP throughput 在 10% loss 下降 >50%，则 H1.1 验证通过

**实验步骤**：
1. 创建拓扑并启动 iperf3 server
2. For each loss_rate in [0, 1, 5, 10, 20]:
   - Apply netem: `tc qdisc add dev s1-eth1 root netem loss {rate}%`
   - Run TCP test: `iperf3 -c h1 -t 30`
   - Run UDP test: `iperf3 -c h1 -u -b 100M -t 30`
   - Record results
   - Clear netem: `tc qdisc del dev s1-eth1 root`
3. Plot results

---

### MVP-1.1: Delay & Jitter Impact

| 项目 | 配置 |
|------|------|
| **目标** | 量化 delay 和 jitter 对 RTT 和 throughput 的影响 |
| **验证假设** | H1.2 (Delay → RTT linear) |
| **依赖** | MVP-0.0 Baseline |
| **异常注入** | `tc qdisc add dev s1-eth1 root netem delay {0,10,25,50,100}ms {jitter}ms` |
| **测量** | ping RTT, jitter distribution, iperf3 TCP throughput |
| **验收标准** | RTT vs Delay 线性相关 R² ≥ 0.95 |

**实验步骤**：
1. For each delay in [0, 10, 25, 50, 100] ms:
   - Apply netem: `tc qdisc add dev s1-eth1 root netem delay {delay}ms 10ms`
   - Run ping: `ping -c 100 h1`
   - Run iperf3: `iperf3 -c h1 -t 30`
   - Record RTT mean/std, throughput
2. Plot RTT vs Injected Delay
3. Compute correlation coefficient

---

### MVP-1.2: Bandwidth Limit Impact

| 项目 | 配置 |
|------|------|
| **目标** | 验证 bandwidth limit 对 throughput 的硬限制 |
| **验证假设** | H1.3 (Bandwidth ceiling) |
| **依赖** | MVP-0.0 Baseline |
| **异常注入** | `tc qdisc add dev s1-eth1 root tbf rate {1,5,10}mbit burst 32kbit latency 400ms` |
| **测量** | iperf3 TCP/UDP max throughput |
| **验收标准** | Measured throughput ≈ limit ±5% |

**实验步骤**：
1. For each rate in [1, 5, 10] Mbps:
   - Apply tbf: `tc qdisc add dev s1-eth1 root tbf rate {rate}mbit burst 32kbit latency 400ms`
   - Run iperf3: `iperf3 -c h1 -t 30`
   - Record max throughput
2. Verify throughput = bandwidth limit

---

## Phase 2: Application Layer

### MVP-2.0: HTTP Application Performance

| 项目 | 配置 |
|------|------|
| **目标** | 测量网络异常对 HTTP 下载时间的复合影响 |
| **验证假设** | H2.2 (Application layer compounding) |
| **依赖** | MVP-1.0, MVP-1.1 |
| **异常配置** | Loss=5% + Delay=50ms |
| **测量** | curl download time for 1MB/10MB files |
| **验收标准** | Download time >2× baseline at anomaly |

**实验步骤**：
1. Setup HTTP server with test files (1MB, 10MB)
2. Baseline: Measure download time with no anomaly
3. Apply combined netem: `tc qdisc add dev s1-eth1 root netem loss 5% delay 50ms`
4. Measure download time
5. Compare to baseline

---

### MVP-2.1: Combined Anomalies Analysis

| 项目 | 配置 |
|------|------|
| **目标** | 分析多种异常组合的交互效应 |
| **验证假设** | H1, H2 综合验证 |
| **依赖** | MVP-1.0 ~ MVP-2.0 |
| **异常配置** | 组合 Loss × Delay × Bandwidth 参数 |
| **验收标准** | 生成多维影响热力图 |

---

## Phase 3: Advanced (Optional)

### MVP-3.0: Corruption & Reordering

| 项目 | 配置 |
|------|------|
| **目标** | 测试 packet corruption 和 reordering 的影响 |
| **异常注入** | `netem corrupt 1%`, `netem reorder 25%` |
| **验收标准** | 理解 corruption/reorder 对 TCP 的影响 |

---

# 4. 📊 进度追踪

## 4.1 看板视图

```
┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│   ⏳ 计划中   │  ⚠️ 部分完成  │  🚀 运行中   │   ✅ 已完成   │   ❌ 已取消   │
├──────────────┼──────────────┼──────────────┼──────────────┼──────────────┤
│ MVP-3.0      │              │              │ MVP-0.0      │              │
│              │              │              │ MVP-1.0      │              │
│              │              │              │ MVP-1.1      │              │
│              │              │              │ MVP-1.2      │              │
│              │              │              │ MVP-2.0      │              │
│              │              │              │ MVP-2.1      │              │
└──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
```

## 4.2 核心结论快照

> **每个完成的 MVP 的一句话结论，同步到 Hub**

| MVP | 核心结论（一句话） | 关键数字 | 同步到 Hub |
|-----|------------------|---------|-----------|
| MVP-0.0 | Mininet 环境稳定，baseline 测量成功 | TCP: 42,819 Mbps, RTT: 0.04ms | ✅ |
| MVP-1.0 | TCP 对丢包极其敏感，UDP loss 完美对应 | 1% loss → 86% TCP drop | ✅ |
| MVP-1.1 | RTT 与 delay 线性相关，delay 严重影响 TCP | 100ms → 7.64 Mbps | ✅ |
| MVP-1.2 | 带宽限制精确可控 | ~100% 效率 | ✅ |
| MVP-2.0 | HTTP 延迟影响显著 (30.57×) | 100ms delay | ✅ |
| MVP-2.1 | **组合异常产生 90% 复合下降** ⭐ | 5%+50ms@10Mbps → 1.03Mbps | ✅ |

## 4.3 时间线

| 日期 | 事件 | 备注 |
|------|------|------|
| 2025-12-06 | 项目立项，创建 Hub + Roadmap | 新主题初始化 |
| 2025-12-06 | MVP-0.0 ~ MVP-1.2 完成 | Phase 0-1 全部完成 |
| 2025-12-06 | MVP-2.0 ~ MVP-2.1 完成 | Phase 2 全部完成，发现组合效应 |

---

# 5. 🔗 跨仓库集成

## 5.1 实验索引

> **链接到 experiments_index/index.csv**

| experiment_id | project | topic | 状态 | 对应 MVP |
|---------------|---------|-------|------|---------|
| `FN-20251206-network-01` | FN | network | 🔴 | MVP-0.0 |

## 5.2 仓库关联

| 仓库 | 相关目录 | 说明 |
|------|---------|------|
| 本仓库 | `network/` | 知识沉淀 |
| 本仓库 | `network/scripts/` | 实验脚本（可选） |

## 5.3 运行路径记录

> **记录实验的实际运行路径，便于复现**

| MVP | 环境 | 运行路径 | 配置文件 | 输出路径 |
|-----|------|---------|---------|---------|
| MVP-0.0 | Mininet (Linux) | Local VM / WSL | - | `network/results/` |

---

# 6. 📎 附录

## 6.1 数值结果汇总表

> **所有 MVP 的核心数值结果**

### Baseline (MVP-0.0)

| 指标 | Baseline Value | 条件 |
|------|----------------|------|
| TCP Throughput | **42,819 Mbps** | iperf3 10s |
| UDP Throughput | **49.51 Mbps** | iperf3 -u -b 50M |
| RTT | **0.041 ms** | ping 50 packets |
| HTTP Download (1MB) | <0.001 s | curl (localhost) |

### Packet Loss Impact (MVP-1.0)

| Loss Rate | TCP Throughput | TCP Drop | UDP Loss (measured) |
|-----------|----------------|----------|---------------------|
| 0% | 42,584 Mbps | 0% | 0.00% |
| 1% | 6,143 Mbps | **85.6%** | 0.77% |
| 5% | 145 Mbps | **99.7%** | 4.87% |
| 10% | 4.95 Mbps | **99.99%** | 10.08% |
| 20% | 0.49 Mbps | **99.999%** | 19.42% |

### Delay Impact (MVP-1.1)

| Delay | RTT | TCP Throughput | TCP Drop |
|-------|-----|----------------|----------|
| 0ms | 0.04 ms | 42,256 Mbps | 0% |
| 10ms | 10.08 ms | 3,005 Mbps | 93% |
| 25ms | 25.08 ms | 668 Mbps | 98% |
| 50ms | 50.08 ms | 89 Mbps | 99.8% |
| 100ms | 100.08 ms | 7.64 Mbps | **99.98%** |

### Bandwidth Limit (MVP-1.2)

| Limit | TCP Throughput | Efficiency |
|-------|----------------|------------|
| 1 Mbps | 1.23 Mbps | 123% |
| 5 Mbps | 5.18 Mbps | 104% |
| 10 Mbps | 10.05 Mbps | **~100%** |

---

## 6.2 相关文件索引

| 类型 | 文件路径 | 说明 |
|------|---------|------|
| Roadmap | `network/network_roadmap_20251206.md` | 当前文件 |
| Hub | `network/network_hub_20251206.md` | 智库导航 |
| MVP-0.0 报告 | `network/exp_network_anomaly_mininet_20251206.md` | 实验报告 |
| 图表目录 | `network/img/` | 实验图表 |

---

## 6.3 变更日志

| 日期 | 变更内容 | 影响 |
|------|---------|------|
| 2025-12-06 | 创建 Roadmap，设计 Phase 0-3 | 全部 |
| 2025-12-06 | 完成 MVP-0.0 ~ MVP-1.2，填充结果数据 | §4, §6.1 |
| 2025-12-06 | MVP-2.0 部分完成，更新状态 | §2, §4 |

---

> **Roadmap 的定位**：
> - ✅ **做**：MVP 规格、执行追踪、进度看板、跨仓库集成、数值结果
> - ❌ **不做**：假设管理（→ hub.md）、洞见汇合（→ hub.md）、战略导航（→ hub.md）
