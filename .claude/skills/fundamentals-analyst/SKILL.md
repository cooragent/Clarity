---
name: fundamentals-analyst
version: "0.1.0"
description: 公司基本面分析与财务指标解读。
user-invocable: false
allowed-tools:
  - Read
  - WebSearch
  - WebFetch
---

# Fundamentals Analyst

## 目标
输出公司基本面报告，聚焦财务质量、盈利能力、现金流、估值与风险。

## 输入
- `ticker`（股票代码）
- 时间范围（如过去 4 季度/过去 1 年）
- 关注点（如利润质量、负债结构、管理层动作）

## 方法
- 优先调用 FinnHub API 获取：
  - 公司概况、财务摘要、利润表/资产负债表/现金流
  - 内幕交易、机构动向、分析师评级
- 必要时使用 WebSearch/WebFetch 补充年报、季报或公告

## 输出格式
- **结论摘要**
- **关键财务指标**
- **收入与盈利趋势**
- **现金流与负债结构**
- **估值与同业对比**
- **风险与关注事项**
- **要点表格（Markdown Table）**
