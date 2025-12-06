# 🤖 实验 Coding Prompt 模板 (v3.1 - 训练自动化)

---
> **日期：** YYYY-MM-DD | **来源：** `logg/[topic]/sessions/session_*.md`

---

## 🚨🚨🚨 跨仓库写入规则（置顶警告）🚨🚨🚨

> **所有写入 `/home/swei20/Physics_Informed_AI/` 知识中心的操作，必须使用终端命令！**
>
> - ❌ **禁止**：使用 IDE 编辑功能（write/search_replace 等工具）直接写入知识中心
> - ✅ **必须**：使用终端命令（`cat << 'EOF' >`、`echo >>`、`cp`、`tee`）写入
>
> **原因**：Cursor IDE 跨仓库写入会弹出确认框，打断自动化工作流。

```bash
# ✅ 正确方式示例
KNOWLEDGE_CENTER="/home/swei20/Physics_Informed_AI"

# 写入新文件
cat << 'EOF' > "$KNOWLEDGE_CENTER/logg/[topic]/exp_xxx.md"
[报告内容]
EOF

# 追加内容
echo "| MVP-X | exp | Phase | ✅ |" >> "$KNOWLEDGE_CENTER/logg/[topic]/[topic]_roadmap.md"

# 复制文件
cp ./local_report.md "$KNOWLEDGE_CENTER/logg/[topic]/"
```

---

## ⚠️ 执行模式：驱动器 + 自动健康检查 + 失败修复

**核心原则**：使用 `driver.py` 自动管理训练生命周期

```
Agent 用 driver.py 启动训练
    ↓
驱动器自动执行：
├─ 前 5 分钟健康检查（NaN/OOM/Loss爆炸）
├─ 健康检查通过 → 等待训练完成
├─ 健康检查失败 → 自动终止 + 输出修复建议
└─ 训练完成 → 自动后处理（生成 summary.json）
    ↓
如果成功：继续生成图表和报告
如果失败：根据修复建议调整后重试
```

---

## 🚀 仓库路由

| Topic | 代码仓库 | ID 前缀 |
|-------|---------|---------|
| `diffusion` | `~/SpecDiffusion` | `SD-` |
| `cnn/swin/ridge/pca/gta/noise/moe` | `~/VIT` | `VIT-` |
| `distill/latent/probe` | `~/BlindSpotDenoiser` | `BS-` |

**知识中心**：`/home/swei20/Physics_Informed_AI/`（所有报告保存到这里）
**驱动器脚本**：`/home/swei20/Physics_Informed_AI/_backend/scripts/training/driver.py`

---

# 📋 Prompt 正文

```text
你是实验执行助理。按以下规格执行实验。

🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨
⚠️ 跨仓库写入规则（最高优先级）
🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨

所有写入 /home/swei20/Physics_Informed_AI/ 的操作：
❌ 禁止：使用 IDE 工具（write、search_replace、edit_file 等）
✅ 必须：使用终端命令（cat << 'EOF' >、echo >>、cp、tee）

原因：IDE 跨仓库写入会触发确认弹窗，打断工作流。

🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨🚨

═══════════════════════════════════════
⚠️ 训练自动化模式
═══════════════════════════════════════

使用 driver.py 执行训练，它会自动：
1. 前 5 分钟健康检查（NaN、OOM、Loss 爆炸等）
2. 健康检查失败 → 自动终止 + 输出修复建议
3. 健康检查通过 → 等待训练完成
4. 训练完成 → 生成 metrics.csv、summary.json、report_draft.md

关键文件位置：
- 日志: [repo]/logs/[exp_id].log
- 信号: [repo]/signals/[exp_id].done (或 .failed)
- 摘要: [repo]/results/[exp_id]/summary.json
- 报告骨架: [repo]/results/[exp_id]/report_draft.md

═══════════════════════════════════════
执行流程（4 步）
═══════════════════════════════════════

【Step 1】使用 driver.py 启动训练
```bash
cd [repo_path]
source init.sh  # 激活环境

# 使用驱动器启动（自动健康检查 + 后处理）
python /home/swei20/Physics_Informed_AI/_backend/scripts/training/driver.py \
    --cmd "[训练命令]" \
    --exp-id [exp_id] \
    --health-time 300  # 可选：健康检查时长（秒），默认 5 分钟

# 例如：
python /home/swei20/Physics_Informed_AI/_backend/scripts/training/driver.py \
    --cmd "python scripts/run.py -f configs/exp/logg/base.yaml" \
    --exp-id VIT-20251204-cnn-01

# 或使用配置文件（会自动构建 python scripts/run.py -f CONFIG 命令）：
python /home/swei20/Physics_Informed_AI/_backend/scripts/training/driver.py \
    --config configs/exp/logg/base.yaml \
    --exp-id VIT-20251204-cnn-01
```

【Step 1b】如果健康检查失败
驱动器会自动输出：
- 失败原因
- 日志最后 20 行
- 针对性修复建议

根据修复建议调整配置后重试：
```bash
# 例如：NaN 检测 → 降低学习率
python .../driver.py \
    --cmd "python train.py --lr 1e-5" \
    --exp-id [exp_id]-fix1

# 例如：OOM → 减小 batch size
python .../driver.py \
    --cmd "python train.py --batch-size 16" \
    --exp-id [exp_id]-fix1
```

【Step 2】训练完成后 → 生成图表
驱动器已自动生成 summary.json，接下来生成图表：
```bash
# 读取摘要获取关键信息
cat [repo]/results/[exp_id]/summary.json

# 生成图表
python plot.py --exp_id [exp_id] \
    --output /home/swei20/Physics_Informed_AI/logg/[topic]/img/
```

【Step 3】撰写报告 🚨 必须用终端命令！禁止用 IDE！
# ⚠️ 下面所有写入知识中心的操作，必须用 run_terminal_cmd 执行 bash 命令
# ❌ 禁止：write()、search_replace()、edit_file() 等 IDE 工具
# ✅ 必须：cat << 'EOF' > 或 echo >> 通过终端写入
```bash
KNOWLEDGE_CENTER="/home/swei20/Physics_Informed_AI"

# 读取自动生成的报告骨架
cat [repo]/results/[exp_id]/report_draft.md

# 基于骨架和 summary.json 填充完整报告
# ⚠️ 必须用 cat << 'EOF' > 写入，不能用 IDE 编辑（跨仓库写入会触发确认弹窗）
cat << 'EOF' > "$KNOWLEDGE_CENTER/logg/[topic]/exp_[name]_YYYYMMDD.md"
# [实验名称]

> experiment_id: [exp_id] | date: YYYY-MM-DD | status: ✅ 完成

## ⚡ 核心结论速览
| 项目 | 内容 |
|------|------|
| **一句话总结** | [从 summary.json 提取] |
| **假设验证** | ❌/✅ H?.? |
| **关键数字** | R²=[final_r2], Loss=[final_loss] |
| **设计启示** | [总结] |

## 1. 目标
[实验目的]

## 2. 实验设计
[数据/模型/超参数]

## 3. 图表
![fig1](./img/[exp_id]_xxx.png)
[观察]

## 4. 洞见
- [关键发现]

## 5. 结论
[核心发现 + 设计启示]

## 6. 附录
### 6.1 数值结果
从 [repo]/results/[exp_id]/metrics.csv 提取

### 6.2 执行日志
[关键命令和输出]
EOF
```

【Step 4】更新追踪文件 🚨 必须用终端命令！禁止用 IDE！
# ⚠️ 所有追加/修改知识中心文件的操作，必须用 run_terminal_cmd 执行
# ❌ 禁止：write()、search_replace()、edit_file() 等 IDE 工具
# ✅ 必须：echo >> 或 cat << 'EOF' >> 通过终端追加
```bash
KNOWLEDGE_CENTER="/home/swei20/Physics_Informed_AI"

# 更新 kanban
echo "- [x] [exp_id]: [结论]" >> "$KNOWLEDGE_CENTER/status/kanban.md"

# 更新 roadmap §2.1 实验总览（追加实验条目）
cat << 'EOF' >> "$KNOWLEDGE_CENTER/logg/[topic]/[topic]_roadmap.md"
| [MVP-X.X] | [实验名称] | [Phase] | ✅ | [exp_id] | [链接](./exp_[name]_YYYYMMDD.md) |
EOF

# 更新 roadmap §4.2 核心结论快照（如有重要结论）
cat << 'EOF' >> "$KNOWLEDGE_CENTER/logg/[topic]/[topic]_roadmap.md"
### [exp_id]
- **结论**: [一句话总结]
- **关键数字**: R²=[value], MAE=[value]
- **设计启示**: [总结]
EOF

# 更新 hub §3 洞见汇合站（如有重要发现）
cat << 'EOF' >> "$KNOWLEDGE_CENTER/logg/[topic]/[topic]_hub.md"
#### [exp_id] 的发现
- **单点发现**: [关键发现]
- **汇合结论**: [与已有洞见的关联]
EOF

# ⚠️ 重要：跨仓库写入必须用终端命令（cat/echo/tee），不能用 IDE 编辑
# 原因：IDE 跨仓库写入会触发确认弹窗，打断工作流
```

═══════════════════════════════════════
驱动器参数速查
═══════════════════════════════════════

| 参数 | 说明 | 默认值 |
|------|------|--------|
| --cmd | 完整训练命令 | 必需（或 --config） |
| --config | 配置文件路径 | 必需（或 --cmd） |
| --exp-id | 实验 ID | 必需 |
| --health-time | 健康检查时长（秒） | 300 |
| --check-interval | 检查间隔（秒） | 10 |
| --skip-post | 跳过后处理 | false |
| --dry-run | 只显示命令不执行 | false |

═══════════════════════════════════════
交付物清单
═══════════════════════════════════════

| 类型 | 路径 |
|------|------|
| 训练日志 | `[repo]/logs/[exp_id].log` |
| 指标 CSV | `[repo]/results/[exp_id]/metrics.csv` |
| 摘要 JSON | `[repo]/results/[exp_id]/summary.json` |
| 报告骨架 | `[repo]/results/[exp_id]/report_draft.md` |
| 最终报告 | `/home/swei20/Physics_Informed_AI/logg/[topic]/exp_[name]_YYYYMMDD.md` |
| 图表 | `/home/swei20/Physics_Informed_AI/logg/[topic]/img/` |

🚨 完成后更新（必须用 run_terminal_cmd 执行 bash 命令）：
- `status/kanban.md` → Done 区域（用 `echo >>`）
- `logg/[topic]/[topic]_roadmap.md` §2.1 和 §4.2（用 `cat << 'EOF' >>`）
- `logg/[topic]/[topic]_hub.md` §3（如有重要洞见，用 `cat << 'EOF' >>`）

🚨🚨🚨 跨仓库写入规则（重申）🚨🚨🚨
❌ 禁止：使用 write()、search_replace()、edit_file() 等 IDE 工具写入知识中心
✅ 必须：使用 run_terminal_cmd 执行 cat/echo/tee 命令写入
原因：IDE 跨仓库写入会触发确认弹窗，打断自动化工作流
```

---

# 🎯 实验规格（填写区）

```yaml
experiment_id: "[PROJECT]-[YYYYMMDD]-[topic]-[序号]"
experiment_name: "[名称]"
repo_path: "~/VIT"  # 或 ~/BlindSpotDenoiser 或 ~/SpecDiffusion

# 训练命令（二选一）
train_cmd: "python scripts/xxx.py --config xxx.yaml"
# 或
config_file: "configs/exp/xxx.yaml"

# 数据
data:
  train_size: N
  target: "log_g"

# 模型
model:
  type: "[类型]"
  # [其他参数]

# 训练
training:
  epochs: N
  batch_size: N
  lr: 1e-4

# 健康检查配置（可选）
health_check:
  time: 300     # 健康检查时长（秒）
  interval: 10  # 检查间隔

# 要画的图
plots:
  - type: loss_curve
    save: "[exp_id]_loss.png"
  - type: pred_vs_true
    save: "[exp_id]_pred.png"
```

---

# ✅ 成功标准

| 检查项 | 状态 |
|--------|------|
| 驱动器启动成功 | ⬜ |
| 健康检查通过 | ⬜ |
| 训练正常完成 | ⬜ |
| summary.json 已生成 | ⬜ |
| 图表已生成 | ⬜ |
| 报告已写入知识中心 | ⬜ |
| kanban 已更新 | ⬜ |

---

# 🔧 故障排除

## 健康检查失败

驱动器会自动输出修复建议，常见场景：

| 问题 | 修复建议 |
|------|---------|
| NaN 检测 | 降低 lr / 添加 grad_clip / 检查数据 |
| OOM | 减小 batch_size / 使用 gradient accumulation |
| Loss 爆炸 | 降低 lr / 添加 warmup |
| CUDA 错误 | 检查 GPU 状态 / 重启 |

## 训练太久？

使用 `--skip-post` 跳过后处理，手动检查：
```bash
# 检查训练状态
cat [repo]/signals/[exp_id].done

# 手动运行后处理
python /home/swei20/Physics_Informed_AI/_backend/scripts/training/post_process.py \
    --exp-id [exp_id] --work-dir [repo]
```

---

> **使用说明**：
> 1. 填写「实验规格」部分
> 2. 复制「Prompt 正文」给 Agent
> 3. Agent 使用 driver.py 启动训练
> 4. 驱动器自动处理健康检查、等待、后处理
> 5. 如果失败，根据修复建议调整后重试
