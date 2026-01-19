---
name: technical-analyst
version: "0.1.0"
description: 技术指标与价格走势分析。
user-invocable: false
allowed-tools:
  - Read
  - WebSearch
  - WebFetch
---

# Technical Analyst

## 目标
从价格与技术指标中识别趋势、关键位与潜在信号。

## 输入
- `ticker`（股票代码）
- 时间窗口（如近 90/180 天）
- 指标偏好（可选）

## 方法
- 趋势判断：均线、结构高低点
- 动量判断：MACD/RSI/ATR 等
- 支撑/压力：关键价位与量价配合

## 输出格式
- **趋势结论**
- **关键指标解读**
- **关键价位与结构**
- **潜在交易含义**
- **要点表格（Markdown Table）**
