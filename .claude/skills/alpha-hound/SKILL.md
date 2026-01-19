---
name: alpha-hound
version: "0.1.0"
description: 基于复杂条件筛选股票并输出候选列表。
user-invocable: false
allowed-tools:
  - Read
  - WebSearch
  - WebFetch
---

# Alpha Hound

## 目标
根据**复杂筛选条件**深度查询并筛选股票，输出候选与理由。

## 输入
- 条件集合（财务、估值、技术、行业、事件）
- 市场范围（美股/港股/全球）
- 时间窗口与更新频率

## 方法
1. **解析条件**：将自然语言条件拆为可查询字段
2. **FinnHub API 筛选**：基本面与财务指标
3. **SERPER_API 搜索**：新闻/事件/行业热点
4. **JINA_API 抽取**：提取网页核心证据
5. **交叉验证**：确认条件满足度与风险

## 输出格式
- **筛选条件摘要**
- **候选列表（含满足条件的证据）**
- **风险与不确定性**
- **建议的下一步验证**
- **要点表格（Markdown Table）**
