# 📧 Auto Report System

> 自动汇报生成系统

## 目录结构

```
reports/
├── README.md           # 本文件
├── last_report.json    # 上次汇报的时间戳记录
├── history.csv         # 所有汇报的历史记录
└── drafts/             # 自动生成的汇报草稿
    └── weekly_YYYY-MM-DD.md
```

## 文件说明

### `last_report.json`

记录上次汇报的时间区间，用于增量筛选新内容：

```json
{
  "last_report_id": "weekly-2025-12-01",
  "last_report_type": "weekly",
  "period_start": "2025-11-24T00:00:00",
  "period_end": "2025-12-01T00:00:00",
  "generated_at": "2025-12-01T10:30:00",
  "draft_path": "reports/drafts/weekly_2025-12-01.md"
}
```

### `history.csv`

所有汇报的历史记录：

| 字段 | 说明 |
|------|------|
| `report_id` | 汇报唯一标识 |
| `type` | `weekly` / `monthly` / `adhoc` |
| `period_start` | 统计周期开始 |
| `period_end` | 统计周期结束 |
| `generated_at` | 生成时间 |
| `draft_path` | 草稿文件路径 |
| `experiments_count` | 包含的实验数量 |
| `insights_count` | 包含的洞见数量 |
| `summary` | 一句话摘要 |

## 使用方式

### 生成周报

```bash
python scripts/generate_report.py --type weekly
```

### 生成指定时间段报告

```bash
python scripts/generate_report.py --type adhoc \
  --start "2025-11-25" \
  --end "2025-12-01"
```

## 汇报结构

生成的汇报草稿包含以下章节：

1. **Overview** - 本周期最重要的变化（2-4 句）
2. **New Experiments Completed** - 按 project/topic 列出完成的实验
3. **Key Insights & Design Decisions** - 按 topic 汇总重要洞见
4. **Open Questions & Next Steps** - 从 `next_steps.md` 抽取 P0/P1
5. **Appendix** - 链接到各仓库和关键 logg 文件

## 数据流

```
experiments_index/index.csv  ──┐
                               │
logg/**/*.md (mtime filter)  ──┼──→ generate_report.py ──→ drafts/weekly_*.md
                               │
status/next_steps.md  ─────────┘
```

## 注意事项

- 脚本**不会**编造数据，只汇总实际存在的内容
- 如果某个字段为空，会用 `TODO` 占位
- 生成后建议人工审核再发送

