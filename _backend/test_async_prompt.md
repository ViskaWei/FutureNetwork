# 🧪 测试异步执行系统

> 这是一个测试 prompt，用于验证异步执行 + 信号文件机制

---

## 测试目标

1. ✅ 后台执行训练（不阻塞 Agent）
2. ✅ 信号文件自动生成
3. ✅ 完成后通知
4. ✅ `check` 命令能检测到完成状态

---

## Prompt 正文

```text
你是实验执行助理。请执行以下测试任务。

═══════════════════════════════════════
⚠️ 异步执行模式测试
═══════════════════════════════════════

【Step 1】后台启动测试任务（模拟 30 秒训练）

```bash
cd ~/VIT
mkdir -p signals logs

# 测试任务：sleep 30 秒模拟训练
EXP_ID="TEST-20251204-async-01"

nohup bash -c '
    echo "=== 测试开始: $(date) ==="
    echo "模拟训练中..."
    for i in {1..6}; do
        echo "Epoch $i/6 完成"
        sleep 5
    done
    echo "=== 测试结束: $(date) ==="
    
    # 写信号文件
    echo "done $(date)" > signals/TEST-20251204-async-01.done
    
    # 完成通知
    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║  ✅ 测试完成！                                            ║"
    echo "║  👉 输入: check TEST-20251204-async-01                    ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo -e "\a\a\a"
' > logs/TEST-20251204-async-01.log 2>&1 &

echo "✅ 测试任务已启动 (PID: $!)"
echo "📄 日志: logs/TEST-20251204-async-01.log"
echo "⏱️ 预计 30 秒后完成"
echo ""
echo "💡 完成后输入: check TEST-20251204-async-01"
```

启动后立即告诉用户："测试任务已在后台启动，约 30 秒后完成。届时输入 `check TEST-20251204-async-01` 继续。"

然后 **结束当前回合**，不要等待。

---

【Step 2】用户输入 `check TEST-20251204-async-01` 后

```bash
cd ~/VIT

# 检查信号文件
if [ -f "signals/TEST-20251204-async-01.done" ]; then
    echo "✅ 测试完成！"
    echo "信号文件内容: $(cat signals/TEST-20251204-async-01.done)"
    echo ""
    echo "📄 日志内容:"
    cat logs/TEST-20251204-async-01.log
else
    echo "⏳ 测试进行中..."
    echo "最近日志:"
    tail -10 logs/TEST-20251204-async-01.log
fi
```

---

【Step 3】写测试报告（验证跨仓库写入）

```bash
cat << 'EOF' > /home/swei20/Physics_Informed_AI/logg/test_async_result.md
# 异步执行系统测试报告

> date: $(date +%Y-%m-%d) | status: ✅ 通过

## 测试结果

| 测试项 | 结果 |
|--------|------|
| 后台执行 | ✅ |
| 信号文件 | ✅ |
| 完成通知 | ✅ |
| check 命令 | ✅ |
| 跨仓库写入 | ✅ |

## 结论

异步执行系统工作正常！
EOF

echo "✅ 测试报告已写入: /home/swei20/Physics_Informed_AI/logg/test_async_result.md"
```

---

## 预期流程

```
Agent 执行 Step 1 → "测试任务已启动，30秒后输入 check"
                    ↓
              (Agent 结束回合)
                    ↓
              等待 30 秒
                    ↓
User: check TEST-20251204-async-01
                    ↓
Agent 执行 Step 2 → "✅ 测试完成！"
                    ↓
Agent 执行 Step 3 → 写测试报告
```

## 成功标准

- [ ] Step 1 执行后 Agent 立即返回（不等待）
- [ ] 30 秒后信号文件 `~/VIT/signals/TEST-20251204-async-01.done` 存在
- [ ] check 命令能检测到完成状态
- [ ] 测试报告写入成功
```

---

## 清理命令（测试完成后）

```bash
rm -f ~/VIT/signals/TEST-20251204-async-01.done
rm -f ~/VIT/logs/TEST-20251204-async-01.log
rm -f /home/swei20/Physics_Informed_AI/logg/test_async_result.md
```

