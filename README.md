# TradingAgents

AI 驱动的金融智能体框架，基于 Claude-skill 架构构建。

## 功能特性

- **股票分析**：深度分析特定股票的技术面、基本面、新闻和市场情绪
- **持仓跟踪**：追踪知名投资者（如 Warren Buffett）的最新持仓变化
- **股票筛选**：根据复杂条件筛选符合要求的股票
- **自然语言查询**：支持中英文自然语言查询

## 快速开始

### 安装

```bash
git clone https://github.com/TauricResearch/TradingAgents.git
cd TradingAgents

# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -e .
```

### 配置

创建 `.env` 文件：

```bash
# 必需
ANTHROPIC_API_KEY=your_anthropic_api_key
FINNHUB_API_KEY=your_finnhub_api_key

# 可选（用于网络搜索）
SERPER_API_KEY=your_serper_api_key
JINA_API_KEY=your_jina_api_key
```

### CLI 使用

```bash
# 分析股票
python run_agent.py analyze AAPL

# 跟踪投资者持仓
python run_agent.py track "Warren Buffett"

# 筛选股票
python run_agent.py screen "high dividend yield tech stocks"

# 自然语言查询
python run_agent.py ask "分析一下苹果公司的股票"
```

### API 服务

```bash
# 启动服务器
python api_server.py

# 访问文档
open http://localhost:8000/docs
```

**API 端点：**

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/analyze` | POST | 分析股票 |
| `/api/v1/track` | POST | 跟踪持仓 |
| `/api/v1/screen` | POST | 筛选股票 |
| `/api/v1/ask` | POST | 自然语言查询 |
| `/api/v1/agents` | GET | 列出可用智能体 |
| `/health` | GET | 健康检查 |

**请求示例：**

```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL"}'
```

### Python 使用

```python
import asyncio
from tradingagents import FinancialAgentOrchestrator, AgentConfig, TaskType

async def main():
    orchestrator = FinancialAgentOrchestrator()

    result = await orchestrator.run(
        task_type=TaskType.STOCK_ANALYSIS,
        target="AAPL",
    )
    print(result["report"])

asyncio.run(main())
```

## 架构

```
TradingAgents/
├── run_agent.py          # CLI 入口
├── api_server.py         # FastAPI 服务
├── templates/            # 规划文件模板
├── runtime/              # 运行时文件（git-ignored）
└── tradingagents/
    ├── core/             # 核心智能体
    │   ├── orchestrator.py
    │   ├── master_agent.py
    │   ├── working_agent.py
    │   ├── state_checker.py
    │   └── subagents/    # 子智能体
    │       ├── fundamentals_analyst.py
    │       ├── sentiment_analyst.py
    │       ├── news_analyst.py
    │       ├── technical_analyst.py
    │       ├── holdings_hunter.py
    │       └── alpha_hound.py
    └── dataflows/        # 数据工具
```

### 子智能体

| 智能体 | 职责 |
|--------|------|
| **Fundamentals Analyst** | 分析公司财务报表和基本面指标 |
| **Technical Analyst** | 分析技术指标（MACD、RSI、布林带等） |
| **News Analyst** | 收集和分析相关新闻 |
| **Sentiment Analyst** | 分析市场情绪 |
| **Holdings Hunter** | 追踪机构和知名投资者持仓 |
| **Alpha Hound** | 基于复杂条件筛选股票 |

### Planning-with-Files

系统使用 Claude-skill 的 "planning-with-files" 模式，在 `runtime/` 目录中维护：

- `task_plan.md` - 任务计划
- `findings.md` - 研究发现
- `progress.md` - 执行日志

## 配置选项

详见 `tradingagents/core/config.py`：

```python
from tradingagents import AgentConfig

config = AgentConfig(
    llm_provider="anthropic",           # anthropic, openai, google
    deep_think_llm="claude-sonnet-4-20250514",
    online_tools=True,                  # 使用在线工具
    max_retries=3,
)
```

## 测试

```bash
# 测试 API
python test_api.py --test quick

# 完整测试
python test_api.py --test all
```

## License

Apache 2.0
