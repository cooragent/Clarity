# Task Plan: Financial Intelligence Agent Task

## Goal
[一句话描述最终目标，例如：深度分析 AAPL 股票并给出投资建议]

## Current Phase
Phase 1

## Task Type
<!-- 
  任务类型（三选一）：
  - stock_screening: 根据复杂条件深度查询并筛选股票
  - holdings_tracking: 跟踪某个金融大佬的最新持仓
  - stock_analysis: 深度分析某只特定股票
-->
[task_type]

## Input Context
<!-- 任务输入参数 -->
- **Target**: [股票代码 / 投资大佬名称 / 筛选条件]
- **Date Range**: [开始日期] - [结束日期]
- **Constraints**: [其他约束条件]

## Phases

### Phase 1: Requirements & Discovery
- [ ] 理解用户意图和任务类型
- [ ] 识别约束条件和需求
- [ ] 记录发现到 findings.md
- **Status:** in_progress
- **Assigned SubAgent:** MasterAgent

### Phase 2: Data Collection & Analysis
<!-- 根据任务类型选择性执行 -->
- [ ] 收集市场数据 (Technical Analyst)
- [ ] 收集新闻数据 (News Analyst)
- [ ] 收集社交媒体情绪 (Sentiment Analyst)
- [ ] 收集基本面数据 (Fundamentals Analyst)
- [ ] 查询大佬持仓 (Holdings Hunter) — 仅 holdings_tracking
- [ ] 复杂条件筛选 (Alpha Hound) — 仅 stock_screening
- **Status:** pending

### Phase 3: Synthesis & Report
- [ ] 汇总各分析师报告
- [ ] 生成综合分析结论
- [ ] 更新 findings.md
- **Status:** pending

### Phase 4: Decision & Recommendation
- [ ] 生成投资建议
- [ ] 风险评估
- [ ] 最终交易决策
- **Status:** pending

### Phase 5: Delivery
- [ ] 审核所有输出文件
- [ ] 确保交付物完整
- [ ] 交付给用户
- **Status:** pending

## Key Questions
1. [待回答的问题]
2. [待回答的问题]

## Decisions Made
| Decision | Rationale |
|----------|-----------|
|          |           |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
|       | 1       |            |

## SubAgent Assignments
<!-- 记录每个子任务的执行者和状态 -->
| SubAgent | Task | Status | Retry Count |
|----------|------|--------|-------------|
| MasterAgent | 任务规划 | pending | 0 |
| TechnicalAnalyst | 技术分析 | pending | 0 |
| FundamentalsAnalyst | 基本面分析 | pending | 0 |
| NewsAnalyst | 新闻分析 | pending | 0 |
| SentimentAnalyst | 情绪分析 | pending | 0 |
| HoldingsHunter | 持仓追踪 | pending | 0 |
| AlphaHound | 股票筛选 | pending | 0 |

## Notes
- 每个 Phase 完成后更新状态: pending → in_progress → complete
- 在重大决策前重读此计划（注意力操控）
- 记录所有错误 - 帮助避免重复
- 重试次数上限: 3 次
