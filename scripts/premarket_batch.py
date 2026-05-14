#!/usr/bin/env python3
"""
早盘全景 — 每日 08:00 执行

框架 v3.0（王世辰版6模块全景框架）：
  1. 大局观（指数/隔夜外盘/今日预判/情绪/消息面）
  2. 题材机会解析（主线/支线/短线）
  3. 趋势票建仓方法（常驻模板）
  4. 持仓风险速查（复用 premarket_collect.py）
  5. 事件日历（复用 event_calendar.py）
  6. 总结：指数判断 + 主线策略 + 支线节奏 + 持仓风险

去重项（盘后复盘已覆盖，不再重复采集）：
  ✗ 大盘指数 & 板块热度 → postmarket_review 已输出
  ✗ 全市场情绪 & 涨停池 → postmarket_review 已输出
  ✗ 连板梯队 → postmarket_review 已输出
"""

import subprocess
import sys
import time as _time
from datetime import datetime, timezone, timedelta
from pathlib import Path

CST = timezone(timedelta(hours=8))
now = datetime.now(CST)
today = now.strftime("%Y-%m-%d")
date_str = now.strftime("%Y年%m月%d日 %H:%M")
time_str = now.strftime("%H:%M")

BASE_DIR = Path.home() / ".hermes" / "trading"

print(f"# ⚡ 早盘全景 · {date_str}")
print()

# ══════════════════════════════════════════════
# 1. 大局观
# ══════════════════════════════════════════════

print("## 1️⃣ 大局观")
print()
print("> 🤖 **由 LLM Agent 在收到本输出后从 web_search 补充：**")
print()

print("### 📊 指数")
print("> 昨±X%开→收±X%，X点，量能（放量/缩量），K线形态")
print()

print("### 🌏 隔夜外盘")
print("> - 美股：纳指/道指/标普 ±X%")
print("> - A50期货 ±X%")
print("> - 人民币汇率（离岸/在岸）")
print("> - 大宗商品（原油/黄金/铜/铝）")
print()

print("### 🎯 今日预判")
print("> - 高开 > XX 之上 → **多头趋势**")
print("> - 低开 < XX 之下 → **回踩**")
print("> - 中间位置 → **整理**")
print()

print("### 😤 情绪")
print("> - 昨日涨停家数：XX 家")
print("> - 市场情绪评估：偏暖 / 偏冷 / 分化")
print("> - 多头风标：XXX、XXX（**仅为情绪指标，不代表涨跌**）")
print("> - 空头风标：XXX、XXX（**仅为情绪指标，不代表涨跌**）")
print()

print("### 📰 消息面")
print("> - 昨夜重大政策/行业/公司消息（由 Agent 整理）")
print()

# ══════════════════════════════════════════════
# 2. 题材机会解析
# ══════════════════════════════════════════════

print("---")
print("## 2️⃣ 题材机会解析")
print()

print("### 🔴 主线（延续昨日最强）")
print("| 板块 | 核心标的 | 操作策略 |")
print("|------|---------|---------|")
print("| XXX | XXX、XXX | 追高/低吸/利润垫持股 |")
print()

print("### 🟡 支线（轮动/分化）")
print("| 板块 | 核心标的 | 操作策略 |")
print("|------|---------|---------|")
print("| XXX | XXX | 等调整/边打边撤 |")
print()

print("### ⚡ 短线（情绪博弈）")
print("> 略")
print()

# ══════════════════════════════════════════════
# 3. 趋势票建仓方法（常驻模板）
# ══════════════════════════════════════════════

print("---")
print("## 3️⃣ 趋势票建仓方法（常驻模板）")
print()

print("**量窒息埋伏逻辑：**")
print("1. 量窒息后收红 → 有向上选择方向的预期")
print("2. 支撑位止跌 + 消息刺激 + 题材预期 → 反弹概率高")
print()
print("**核心原则：**")
print("| 情况 | 操作 |")
print("|------|------|")
print("| 买入即浮盈 | 次日冲高减仓做利润垫 = **建仓成功** |")
print("| 买入即被套 | 不硬扛，止损出局，不恋战 |")
print()
print("> 🎯 **建仓成功标准**：买入即浮盈 → 次日冲高减仓做利润垫")
print("> 📉 **胜率说明**：10次建仓成1-2次，所有建仓成本全部回来")
print("> ⚠️ **严格止损**：破了成本或止损线无条件出局，不恋战")
print()

# ══════════════════════════════════════════════
# 4. 持仓风险速查（复用 premarket_collect.py）
# ══════════════════════════════════════════════

print("---")
print("## 4️⃣ 持仓风险速查")
print()

result = subprocess.run(
    ["python3", str(BASE_DIR / "premarket_collect.py")],
    capture_output=True, text=True, timeout=90
)
if result.returncode == 0:
    output = result.stdout
    # 只保留"最近公告"和"需关注的风险点"两个段
    sections = []
    for marker in ["## 📄 最近公告", "## ⚠️ 需关注的风险点"]:
        if marker in output:
            start = output.index(marker)
            rest = output[start:]
            next_section = None
            for i, ch in enumerate(rest[len(marker):], len(marker)):
                if rest[i:i+3] == "## " and not rest[i:i+4] == "## ":
                    next_section = i
                    break
            if next_section:
                sections.append(rest[:next_section])
            else:
                sections.append(rest)

    if sections:
        output_text = "\n".join(sections)
        lines = output_text.strip().split("\n")
        while lines and (lines[-1].strip() in ("#", "") or lines[-1].startswith("### ")):
            lines.pop()
        print("\n".join(lines))
    else:
        ann_start = output.find("## 📄 最近公告")
        risk_start = output.find("## ⚠️ 需关注的风险点")
        llm_start = output.find("### 📊 昨日全市场速览")
        if ann_start >= 0:
            end = risk_start if risk_start > ann_start else llm_start
            end = len(output) if end < 0 else end
            print(output[ann_start:end].strip())
        if risk_start >= 0:
            end = llm_start if llm_start > risk_start else len(output)
            end = len(output) if end < 0 else end
            print(output[risk_start:end].strip())
else:
    print(f"⚠️ 公告扫描脚本执行失败 (exit {result.returncode})")
    if result.stderr:
        print(f"```\n{result.stderr.strip()}\n```")

print()
print("> ⚠️ **风险确认清单（Agent 手动核查）：**")
print("> - 是否有新增大额减持公告？")
print("> - 是否有业绩暴雷/大幅下修？")
print("> - 是否有问询函/监管函/ST风险？")
print("> - 是否有正在进行的配股/增发？")
print("> - 今日到期/即将到期的限售解禁？")
print()

# ══════════════════════════════════════════════
# 5. 事件日历（复用 event_calendar.py）
# ══════════════════════════════════════════════

print("---")
print("## 5️⃣ 事件日历提醒")
print()

result = subprocess.run(
    ["python3", str(BASE_DIR / "event_calendar.py")],
    capture_output=True, text=True, timeout=120
)
if result.returncode == 0:
    output = result.stdout
    llm_marker = "## 💡 需要 LLM 评估的问题"
    if llm_marker in output:
        output = output.split(llm_marker)[0]
    print(output)
else:
    print(f"⚠️ 事件日历脚本执行失败 (exit {result.returncode})")
    if result.stderr:
        print(f"```\n{result.stderr.strip()}\n```")
print()

# ══════════════════════════════════════════════
# 6. 总结
# ══════════════════════════════════════════════

print("---")
print("## 6️⃣ 总结")
print()
print("> 🤖 **由 LLM Agent 根据上方数据生成：**")
print()
print("| 维度 | 判断 | 操作 |")
print("|------|------|------|")
print("| 指数 | XXX | XXX |")
print("| 主线策略 | XXX | 持仓/加仓/减仓 |")
print("| 支线节奏 | XXX | 观望/轻仓 |")
print("| 持仓风险 | XXX | XXX |")
print()

print(f"*数据采集完成: {time_str} CST*")
