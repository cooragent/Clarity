---
name: holdings-hunter
version: "0.1.0"
description: 追踪金融大佬/机构最新持仓与变动。
user-invocable: false
allowed-tools:
  - Read
  - WebSearch
  - WebFetch
---

# Holdings Hunter

## 目标
定位并整理某位金融大佬或机构的**最新持仓**与变动情况。

## 输入
- 目标人物或机构名称
- 市场/地区（美股/港股/私募等）
- 时间范围（最新一期或特定日期）

## 方法
- 优先使用权威披露来源：
  - SEC 13F/13D/13G
  - HKEX 披露易
  - 公司公告/基金季报
- 使用 SERPER_API 搜索最新披露
- 使用 JINA_API 抽取披露页面关键信息

## 输出格式
- **最新披露来源与日期**
- **核心持仓列表（Ticker/仓位/变动）**
- **增持/减持要点**
- **不确定性与缺口说明**
- **要点表格（Markdown Table）**
