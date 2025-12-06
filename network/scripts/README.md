# Network Anomaly Evaluation - Scripts

> MVP-0.0: Mininet Testbed Setup & Baseline Collection

---

## 🚀 Quick Start

### 1. 安装 Mininet (Linux Only)

```bash
# Ubuntu/Debian - 系统级安装
sudo apt update
sudo apt install mininet iperf3 curl

# 验证安装
sudo mn --version
```

### 2. 测试拓扑

```bash
# 创建简单拓扑
sudo mn --topo single,2

# 在 Mininet CLI 中测试
mininet> h1 ping h2
mininet> exit
```

### 3. 运行 Baseline 测试

```bash
cd network/scripts
sudo python3 run_baseline.py
```

---

## 📁 文件结构

```
scripts/
├── init.sh              # 环境变量 + 检查工具
├── run_baseline.py      # MVP-0.0: Baseline 测试
├── run_loss_sweep.py    # MVP-1.0: Packet Loss 测试 (TODO)
└── README.md            # 本文件
```

---

## ⚠️ 注意事项

### Mininet 是系统级工具

- **不需要** conda / virtualenv / venv
- 直接用 `sudo apt install mininet` 安装
- 运行需要 **root 权限**: `sudo python3 run_baseline.py`

### 只能在 Linux 上运行

Mininet 使用 Linux kernel namespaces，只能在 Linux 上运行。

**macOS 用户选项**：
1. **Ubuntu VM**: VirtualBox/VMware + Ubuntu
2. **Docker**: Linux 容器
3. **Cloud**: AWS/GCP Linux 实例

---

## 📊 输出

测试结果保存在 `../results/` 目录：
- `baseline_YYYYMMDD_HHMMSS.json`

---

## 🔗 相关文件

| 文件 | 说明 |
|------|------|
| [`../exp_network_anomaly_mininet_20251206.md`](../exp_network_anomaly_mininet_20251206.md) | 实验报告 |
| [`../network_hub_20251206.md`](../network_hub_20251206.md) | 智库导航 |
| [`../network_roadmap_20251206.md`](../network_roadmap_20251206.md) | 实验路线图 |
