# Financial Intelligence Agent Architecture

## Overview

This project implements a **Claude-skill style** financial intelligence agent using the **planning-with-files** pattern. The system coordinates multiple specialized SubAgents to perform complex financial analysis tasks.

## Task Types

The agent supports three main task types:

1. **Stock Screening** (`stock_screening`) - 根据复杂条件深度查询并筛选股票
2. **Holdings Tracking** (`holdings_tracking`) - 跟踪某个金融大佬的最新持仓
3. **Stock Analysis** (`stock_analysis`) - 深度分析某只特定股票

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FinancialAgentOrchestrator               │
│                         (Main Entry Point)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        MasterAgent                          │
│                   (Task Planning & Coordination)            │
│  - Analyzes user input                                      │
│  - Creates task plans                                       │
│  - Loads MCP tools (reference: youtu-agent)                 │
│  - Loads SubAgents as tools                                 │
│  - Synthesizes results                                      │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  WorkingAgent   │ │ StateChecker    │ │ PlanningManager │
│  (Execution)    │ │ (Monitoring)    │ │ (Files)         │
│                 │ │                 │ │                 │
│ - Executes plan │ │ - Checks state  │ │ - task_plan.md  │
│ - Manages steps │ │ - Retry logic   │ │ - findings.md   │
│ - Reports       │ │ - Replan trigger│ │ - progress.md   │
└─────────────────┘ └─────────────────┘ └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         SubAgents                           │
│                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │ Technical     │  │ Fundamentals  │  │ News          │   │
│  │ Analyst       │  │ Analyst       │  │ Analyst       │   │
│  └───────────────┘  └───────────────┘  └───────────────┘   │
│                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐   │
│  │ Sentiment     │  │ Holdings      │  │ Alpha         │   │
│  │ Analyst       │  │ Hunter        │  │ Hound         │   │
│  └───────────────┘  └───────────────┘  └───────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                          Tools                              │
│                                                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ FinnHub    │  │ SERPER     │  │ JINA       │            │
│  │ API        │  │ API        │  │ API        │            │
│  └────────────┘  └────────────┘  └────────────┘            │
│                                                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ Yahoo      │  │ Reddit     │  │ Google     │            │
│  │ Finance    │  │ Data       │  │ News       │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

## Planning-with-Files Pattern

The system uses three persistent markdown files as "working memory on disk":

### `task_plan.md`
- Contains the overall task plan with phases
- Tracks phase status (pending → in_progress → complete)
- Records errors and decisions
- Updated after each phase

### `findings.md`
- Stores research findings and discoveries
- Contains analysis reports from each SubAgent
- Updated after every 2 operations (2-Action Rule)

### `progress.md`
- Session log with timestamps
- Test results and error logs
- Retry tracking
- Updated throughout session

## SubAgents

### Technical Analyst
Analyzes market data and technical indicators (SMA, EMA, MACD, RSI, Bollinger Bands, ATR).

### Fundamentals Analyst
Analyzes company fundamentals including:
- Balance sheets
- Cash flow statements
- Income statements
- Insider sentiment and transactions

### News Analyst
Gathers and analyzes news from:
- FinnHub
- Google News
- Reddit
- Web search

### Sentiment Analyst
Analyzes social media sentiment from:
- Reddit discussions
- Web sentiment search

### Holdings Hunter (New)
Tracks institutional and guru holdings:
- SEC 13F filings
- Famous investor portfolios (Buffett, Dalio, Burry, etc.)
- Institutional holders

### Alpha Hound (New)
Screens stocks based on complex criteria:
- Fundamental metrics (PE, PB, market cap)
- Technical indicators
- Sector/industry filters
- Custom queries

## State Checking & Retry Logic

The StateCheckerAgent monitors execution:

1. **After each step**: Checks if successful
2. **On failure**:
   - Checks retry count (max 3 retries)
   - Analyzes error type
   - Recommends action: retry, skip, or replan
3. **On excessive failures**:
   - Triggers replanning if critical step fails
   - Skips non-critical steps after max retries

## Usage

### Command Line

```bash
# Analyze a stock
python run_agent.py analyze AAPL

# Track holdings
python run_agent.py track "Warren Buffett"

# Screen stocks
python run_agent.py screen "high dividend yield low PE"

# Natural language query
python run_agent.py ask "分析一下苹果公司的股票"
```

### Python API

```python
from tradingagents.core import (
    FinancialAgentOrchestrator,
    AgentConfig,
    TaskType,
)

# Create orchestrator
config = AgentConfig()
orchestrator = FinancialAgentOrchestrator(config)

# Run analysis
result = await orchestrator.run(
    task_type=TaskType.STOCK_ANALYSIS,
    target="AAPL",
    trade_date="2025-01-18",
)

# Or use convenience functions
from tradingagents.core import analyze_stock, track_holdings, screen_stocks

result = await analyze_stock("AAPL")
result = await track_holdings("Warren Buffett")
result = await screen_stocks("high dividend yield")
```

## Configuration

### Environment Variables

```bash
# LLM APIs
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key

# Financial Data
FINNHUB_API_KEY=your_key

# Search APIs
SERPER_API_KEY=your_key
JINA_API_KEY=your_key
```

### Config File

See `configs/agent_config.yaml` for full configuration options.

## References

- **planning-with-files**: Based on Claude skill pattern from `claude_skill/planning-with-files`
- **MCP Tools**: Loading pattern from `youtu-agent` (see `utu/utils/mcp_utils.py`)
- **FinnHub Tools**: Reference from `MiroFlow/src/utils/tool_utils.py`
- **Original TradingAgents**: Analyst patterns from original `tradingagents/agents/analysts/`

## File Structure

```
TradingAgents/
├── run_agent.py                 # Main entry point
├── configs/
│   └── agent_config.yaml        # Configuration
├── templates/
│   ├── task_plan.md             # Task plan template
│   ├── findings.md              # Findings template
│   └── progress.md              # Progress template
└── tradingagents/
    ├── core/
    │   ├── __init__.py
    │   ├── base_agent.py        # BaseSubAgent class
    │   ├── config.py            # Configuration classes
    │   ├── master_agent.py      # MasterAgent
    │   ├── working_agent.py     # WorkingAgent
    │   ├── state_checker.py     # StateCheckerAgent
    │   ├── planning_manager.py  # Planning file management
    │   ├── orchestrator.py      # Main orchestrator
    │   ├── subagents/
    │   │   ├── __init__.py
    │   │   ├── fundamentals_analyst.py
    │   │   ├── sentiment_analyst.py
    │   │   ├── news_analyst.py
    │   │   ├── technical_analyst.py
    │   │   ├── holdings_hunter.py    # New
    │   │   └── alpha_hound.py        # New
    │   └── tools/
    │       ├── __init__.py
    │       ├── finnhub_tools.py
    │       ├── search_tools.py
    │       └── web_tools.py
    └── dataflows/               # Original data utilities
```
