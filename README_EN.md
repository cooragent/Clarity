# Clarity

<p align="center">
  <strong>Financial Analysis Agent Built on Native Claude-skill Architecture</strong>
</p>

<p align="center">
  English | <a href="./README.md">简体中文</a>
</p>

<p align="center">
  <a href="https://www.cooragent.com/">
    <img src="https://img.shields.io/badge/Powered%20by-Cooragent-blue?style=flat-square" alt="Powered by Cooragent">
  </a>
  <a href="https://github.com/cooragent/Clarity/stargazers">
    <img src="https://img.shields.io/github/stars/cooragent/Clarity?style=flat-square" alt="GitHub Stars">
  </a>
  <a href="https://github.com/cooragent/Clarity/issues">
    <img src="https://img.shields.io/github/issues/cooragent/Clarity?style=flat-square" alt="GitHub Issues">
  </a>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#usage">Usage</a> •
  <a href="#workflow">Workflow</a> •
  <a href="#architecture">Architecture</a>
</p>

> 🌟 **If you find this project helpful, please give us a Star! Your support keeps us improving!**
> 
> 💡 **Feel free to submit Issues or PRs. We value your feedback and suggestions!**

---

## Introduction

Clarity is a financial analysis agent framework built on the **native Claude-skill** architecture. It adopts the **Planning-with-Files** pattern, using persistent task plans, research findings, and progress logs to coordinate multiple specialized sub-agents for complex financial analysis tasks.

### Key Features

- 🧠 **Native Claude-skill Architecture**: Following Anthropic's recommended agent design patterns
- 📁 **Planning-with-Files**: Context persistence through file system, solving LLM's "forgetting" problem in long tasks
- 🤖 **Multi-Agent Collaboration**: 6 specialized sub-agents working together with clear division of labor
- 📊 **Decision Dashboard**: Daily market scanning with potential stock recommendations
- 🔔 **Multi-Channel Notifications**: WeChat Work, Feishu, Telegram, Email, and more
- 🌐 **Multi-Market Support**: A-shares, Hong Kong stocks, and US stocks (NASDAQ)

---

## Features

| Feature | Description | Command |
|:--------|:------------|:--------|
| **Stock Analysis** | Deep analysis of technicals, fundamentals, news, and market sentiment | `analyze AAPL` |
| **Holdings Tracking** | Track holdings of famous investors (e.g., Warren Buffett) | `track "Warren Buffett"` |
| **Stock Screening** | Filter stocks based on complex criteria | `screen "high dividend tech"` |
| **Natural Language Query** | Support for English and Chinese queries | `ask "analyze Apple"` |
| **Decision Dashboard** | Daily market scan with stock recommendations | `dashboard` |

---

## Quick Start

### Installation

```bash
git clone https://github.com/your-org/Clarity.git
cd Clarity

# Using uv (recommended)
uv sync
```

### Configuration

Create a `.env` file:

```bash
# ===== Required =====
OPENAI_API_KEY=your_openai_api_key
FINNHUB_API_KEY=your_finnhub_api_key

# ===== Optional: Web Search =====
SERPER_API_KEY=your_serper_api_key
JINA_API_KEY=your_jina_api_key

# ===== Optional: Notification Channels =====
# WeChat Work Bot
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx

# Feishu/Lark Bot
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx

# Telegram Bot
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=123456789

# Email (auto-detect SMTP for Gmail, Outlook, etc.)
EMAIL_SENDER=your@gmail.com
EMAIL_PASSWORD=app_password

# Pushover (iOS/Android push)
PUSHOVER_USER_KEY=xxx
PUSHOVER_API_TOKEN=xxx

# Custom Webhook (DingTalk, Discord, Slack, Bark, etc.)
CUSTOM_WEBHOOK_URLS=https://discord.com/api/webhooks/xxx
```

#### Qwen (OpenAI-compatible mode)

```bash
# ===== Optional: Qwen =====
# Switch at runtime via CLI: uv run run_agent.py --model qwen ...
QWEN_API_KEY=your_dashscope_api_key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-latest
```

For web search in Qwen mode, set `SERPER_API_KEY` (recommended). If not set, it will fall back to scraping Google News, which may be rate-limited.

---

## Usage

### Web UI

```bash
# activate env
source .venv/bin/activate 

# Start Web interface
uv run python webui.py

# Create a public link (via Gradio Share)
uv run python webui.py --share
```

<video src="assets/ui.mp4" controls width="800"></video>

Visit http://localhost:7860 to use the graphical interface.

### CLI Commands

```bash
# Analyze a stock
uv run python run_agent.py analyze AAPL
uv run python run_agent.py analyze NVDA --date 2025-01-15
uv run python run_agent.py --model qwen analyze AAPL

# Track investor holdings
uv run python run_agent.py track "Warren Buffett"

# Screen stocks
uv run python run_agent.py screen "high dividend yield tech stocks"

# Natural language query
uv run python run_agent.py ask "analyze Apple stock"

# Decision dashboard
uv run python run_agent.py dashboard                           # Scan A-shares + US stocks
uv run python run_agent.py dashboard -m A股 港股              # Scan specific markets
uv run python run_agent.py dashboard -n 20 -o report.md       # Top 20, save to file
uv run python run_agent.py dashboard --push                   # Scan and push notifications
uv run python run_agent.py dashboard -p --push-to telegram    # Push to Telegram only
uv run python run_agent.py dashboard --interval 30            # Run every 30 minutes
uv run python run_agent.py dashboard -i 60 --push             # Run hourly and push
```

### Python Code

```python
import asyncio
from tradingagents import FinancialAgentOrchestrator, AgentConfig, TaskType

async def main():
    orchestrator = FinancialAgentOrchestrator()

    # Analyze a stock
    result = await orchestrator.run(
        task_type=TaskType.STOCK_ANALYSIS,
        target="AAPL",
    )
    print(result["report"])

asyncio.run(main())
```

```python
# Using notification service
from tradingagents.core import NotificationService

notification = NotificationService()
notification.send("# Test Report\nThis is a Markdown message")
```

---

## Workflow

Using `run_track("Warren Buffett")` as an example:

```
User Input: uv run python run_agent.py track "Warren Buffett"
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    run_agent.py                             │
│                                                             │
│  1. Load .env environment variables                         │
│  2. Create AgentConfig                                      │
│  3. Create FinancialAgentOrchestrator                       │
│  4. Call orchestrator.run(task_type=HOLDINGS_TRACKING, ...) │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│               FinancialAgentOrchestrator                    │
│                                                             │
│  1. MasterAgent.create_task_plan()  ──► Init task_plan.md   │
│  2. WorkingAgent.execute_plan()     ──► Execute SubAgents   │
│  3. StateChecker.validate_step()    ──► Validate/Retry      │
│  4. MasterAgent.synthesize_results() ──► Generate report    │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   SubAgents Execution                        │
│                                                             │
│  Step 1: HoldingsHunter                                     │
│    ├─► Search SEC 13F filings                               │
│    ├─► Parse holdings data                                  │
│    └─► Generate holdings report                             │
│                                                             │
│  Step 2: NewsAnalyst                                        │
│    └─► Search and analyze related news                      │
│                                                             │
│  After each step, update Planning Files:                    │
│    • findings.md  ←  Append analysis results                │
│    • progress.md  ←  Append progress logs                   │
│    • task_plan.md ←  Update status table                    │
└─────────────────────────────────────────────────────────────┘
```

### Planning-with-Files Pattern

The system uses three persistent files to manage long-running tasks:

| File | Purpose | Update Timing |
|:-----|:--------|:--------------|
| `task_plan.md` | Task plan, phase status, SubAgent assignments | Task start, status changes |
| `findings.md` | Research findings, API data, analysis results | After each SubAgent completes |
| `progress.md` | Execution logs, error records, retry tracking | After each operation |

**Core Rules:**
- **2-Action Rule**: Update `findings.md` after every 2 actions
- **Re-read Before Decisions**: Re-read `task_plan.md` before critical decisions
- **Error Persistence**: All errors are logged to files to avoid repeating mistakes

---

## Architecture

```
Clarity/
├── run_agent.py          # CLI entry point
├── webui.py              # Web UI (Gradio)
├── templates/            # Planning file templates
├── runtime/              # Runtime files (git-ignored)
│   ├── task_plan.md
│   ├── findings.md
│   ├── progress.md
│   └── reports/
└── tradingagents/
    ├── core/             # Core agents
    │   ├── orchestrator.py     # Orchestrator
    │   ├── master_agent.py     # Master agent (planning)
    │   ├── working_agent.py    # Working agent (execution)
    │   ├── state_checker.py    # State checker
    │   ├── notification.py     # Notification service
    │   ├── subagents/          # Sub-agents
    │   │   ├── fundamentals_analyst.py
    │   │   ├── sentiment_analyst.py
    │   │   ├── news_analyst.py
    │   │   ├── technical_analyst.py
    │   │   ├── holdings_hunter.py
    │   │   ├── alpha_hound.py
    │   │   └── daily_dashboard.py
    │   └── tools/              # Tools
    │       ├── finnhub_tools.py
    │       ├── search_tools.py
    │       ├── dashboard_scanner.py
    │       └── data_provider/
    └── dataflows/        # Data utilities
```

### Sub-Agents

| Agent | Responsibility | Use Case |
|:------|:---------------|:---------|
| **Fundamentals Analyst** | Analyze financial statements and fundamental metrics | Stock Analysis |
| **Technical Analyst** | Analyze technical indicators (MACD, RSI, Bollinger Bands, etc.) | Stock Analysis |
| **News Analyst** | Collect and analyze relevant news | All Tasks |
| **Sentiment Analyst** | Analyze market sentiment and social media discussions | Stock Analysis |
| **Holdings Hunter** | Track institutional and famous investor holdings | Holdings Tracking |
| **Alpha Hound** | Screen stocks based on complex criteria | Stock Screening |
| **Daily Dashboard** | Daily market scan qualified stock  | Decision Dashboard |

### Notification Channels

| Channel | Environment Variables | Message Format |
|:--------|:---------------------|:---------------|
| WeChat Work | `WECHAT_WEBHOOK_URL` | Markdown |
| Feishu/Lark | `FEISHU_WEBHOOK_URL` | Markdown Card |
| Telegram | `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` | Markdown |
| Email | `EMAIL_SENDER` + `EMAIL_PASSWORD` | HTML |
| Pushover | `PUSHOVER_USER_KEY` + `PUSHOVER_API_TOKEN` | Plain Text |
| Custom Webhook | `CUSTOM_WEBHOOK_URLS` | Auto-adapt |

---

## Configuration Options

See `tradingagents/core/config.py`:

```python
from tradingagents import AgentConfig

config = AgentConfig(
    llm_provider="openai",              # openai, anthropic, google
    deep_think_llm="gpt-5.2",
    online_tools=True,                
    max_retries=3,
)
```

---

## Support & Contributing

This project is supported by cooragent team. Cooragent is an AI agent platform , dedicated to making everyone a commander of AI agents, which adapt, evolve, and stay aligned with users.

### 🌟 Support Us

If you find this project helpful:

- ⭐ **Star the project** - This is the best encouragement for us!
- 🐛 **Submit Issues** - Report bugs or suggest features
- 🔀 **Submit PRs** - Contributions to code and documentation are welcome
- 💬 **Join the community** - Share your experience with other users

### 📮 Contact Us

- 🌐 FeiShu: [cooragent](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=251mf86f-8106-4361-81aa-05fa856abc05)
- 📧 Feedback: Please submit via [GitHub Issues](https://github.com/cooragent/Clarity/issues)

---


## Star History

<a href="https://star-history.com/#cooragent/Clarity&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=cooragent/Clarity&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=cooragent/Clarity&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=cooragent/Clarity&type=Date" />
 </picture>
</a>
