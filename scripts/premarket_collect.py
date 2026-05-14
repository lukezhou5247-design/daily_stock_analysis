#!/usr/bin/env python3
"""
盘前数据采集脚本 — 收集公告、隔夜市场、板块热度、持仓个股异动
由 cron agent 08:30 调用，输出 Markdown 供 LLM 分析

（已迁移至 lib/ 共享库）
"""

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

_lib_dir = str(Path(__file__).resolve().parent)
if _lib_dir not in sys.path:
    sys.path.insert(0, _lib_dir)

from lib import (
    get_quote, get_indices, get_sector_heat, get_announcements,
    load_portfolio, get_active_stocks,
)

CST = timezone(timedelta(hours=8))
now = datetime.now(CST)
today = now.strftime("%Y-%m-%d")


def market_overview_section() -> str:
    """用 Tushare 全市场日线数据生成昨日速览"""
    from lib.tushare_client import get_daily_all
    from datetime import datetime, timezone, timedelta

    data = get_daily_all()  # 默认昨天
    if not data:
        return ""

    cst = timezone(timedelta(hours=8))
    yesterday = (datetime.now(cst) - timedelta(days=1)).strftime("%Y年%m月%d日")

    up = sum(1 for x in data if x.get("pct_chg", 0) > 0)
    down = sum(1 for x in data if x.get("pct_chg", 0) < 0)
    flat = len(data) - up - down
    ratio = f"{up/max(down,1):.2f}:1"

    surge = sum(1 for x in data if x.get("pct_chg", 0) >= 5)
    plunge = sum(1 for x in data if x.get("pct_chg", 0) <= -5)
    limit_up = sum(1 for x in data if x.get("pct_chg", 0) >= 9.9)
    limit_down = sum(1 for x in data if x.get("pct_chg", 0) <= -9.9)

    total_amount = sum(x.get("amount", 0) for x in data) / 1e8

    return f"""
### 📊 昨日全市场速览（{yesterday}）

| 指标 | 数值 |
|------|------|
| 上涨家数 | {up} |
| 下跌家数 | {down} |
| 平盘 | {flat} |
| **涨跌比** | **{ratio}** |
| 总成交额 | {total_amount:.0f}亿 |

涨幅>=5%: {surge}只 | 跌幅>=5%: {plunge}只
涨停(>=9.9%): {limit_up}只 | 跌停(<=-9.9%): {limit_down}只
"""


def main():
    portfolio = load_portfolio()
    active = get_active_stocks(portfolio)

    print(f"# 📋 盘前数据采集 · {today}\n")

    # 1. 大盘指数
    indices = get_indices()
    print("## 📊 大盘指数\n")
    if indices:
        for name, info in indices.items():
            val = info["value"]
            pct = info.get("change_pct", 0)
            print(f"- {name}: **{val:.2f}**（{pct:+.2f}%）")
    else:
        print("（大盘数据获取失败）")
    print()

    # 2. 板块热度 TOP 10
    sectors = get_sector_heat(10)
    print("## 🔥 板块热度 TOP10\n")
    for s in sectors:
        emoji = "🟢" if s["change_pct"] > 0 else "🔴" if s["change_pct"] < 0 else "⚪"
        print(f"- {emoji} {s['name']}: {s['change_pct']:+.2f}%")
    print()

    # 3. 持仓股概况
    print("## 📈 持仓股概况\n")
    print("| 代码 | 名称 | 最新价 | 昨收 | 涨跌幅 | 振幅 | 换手率 |")
    print("|------|------|--------|------|--------|------|--------|")
    for st in active:
        q = get_quote(st["code"])
        if q:
            pre = q.get("pre_close", 0) or 0
            price = q.get("price", 0) or 0
            pct = (price - pre) / pre * 100 if pre else 0
            print(f"| {q['code']} | {q['name']} | {price:.2f} | {pre:.2f} | "
                  f"{pct:+.2f}% | {(q.get('amplitude') or 0):.2f}% | "
                  f"{(q.get('turnover') or 0):.2f}% |")
        else:
            print(f"| {st['code']} | {st['name']} | — | — | — | — | — |")
    print()

    # 4. 个股公告
    print("## 📄 最近公告\n")
    has_ann = False
    for st in active:
        anns = get_announcements(st["code"])
        if anns:
            has_ann = True
            print(f"### {st['name']} ({st['code']})\n")
            badge_map = {
                "业绩": "📊", "分红融资": "💰", "股东变动": "👤",
                "风险警示": "⚠️", "重大事项": "🔔", "公司治理": "🏛️",
            }
            for a in anns:
                badge = badge_map.get(a["type"], "📋")
                print(f"- {badge} **[{a['type']}]** {a['title']} ({a['date']})")
            print()
    if not has_ann:
        print("（近3日无新增公告）\n")

    # 5. 风险提示
    print("## ⚠️ 需关注的风险点\n")
    for st in active:
        q = get_quote(st["code"])
        cost_per_share = st.get("cost_per_share", 0)
        if not cost_per_share and st.get("shares", 0) > 0:
            cost_per_share = st.get("cost", 0) / st["shares"]
        if q and q.get("price") and cost_per_share > 0:
            price = q["price"]
            cost_dev = (price - cost_per_share) / cost_per_share * 100
            amp = q.get("amplitude", 0) or 0
            turnover = q.get("turnover", 0) or 0
            if cost_dev < -3:
                print(f"- 🔴 **{st['name']}** 跌破成本 {cost_dev:.1f}%")
            if amp > 5:
                print(f"- 🟡 **{st['name']}** 高波动标志（振幅 {amp:.1f}%）")
            if turnover > 10:
                print(f"- 🟡 **{st['name']}** 换手率异常（{turnover:.1f}%）")
    print()

    print(f"---\n*数据采集时间: {now.strftime('%H:%M')} CST | 来源: East Money*")
    print(market_overview_section())


if __name__ == "__main__":
    main()
