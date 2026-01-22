


# Clarity

<p align="center">
  <strong>基于原生 Claude-skill 架构的金融分析智能体</strong>
</p>

<p align="center">
  <a href="./README_EN.md">English</a> | 简体中文
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
  <a href="#功能特性">功能特性</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#使用方法">使用方法</a> •
  <a href="#工作流程">工作流程</a> •
  <a href="#架构设计">架构设计</a>
</p>

> 🌟 **如果这个项目对您有帮助，请给我们一个 Star！您的支持是我们持续改进的动力！**
> 
> 💡 **欢迎提出 Issue 或 PR，我们非常重视您的反馈和建议！**

---

## 简介

Clarity 是一个基于 **原生 Claude-skill** 架构构建的金融分析智能体框架。它采用 **Planning-with-Files** 模式，通过持久化的任务计划、研究发现和进度日志来协调多个专业子智能体完成复杂的金融分析任务。

### 核心特点

- 🧠 **Claude-skill 原生架构**：遵循 Anthropic 推荐的智能体设计模式
- 📁 **Planning-with-Files**：通过文件系统持久化上下文，解决 LLM 长任务"遗忘"问题
- 🤖 **多智能体协作**：6 个专业子智能体分工明确，协同完成分析任务
- 📊 **决策仪表盘**：每日自动扫描市场，推荐值得关注的股票
- 🔔 **多渠道推送**：支持企业微信、飞书、Telegram、邮件等多种通知渠道
- 🌐 **多市场支持**：A 股、港股、美股（纳斯达克）全覆盖

---

## 功能特性

| 功能 | 描述 | 命令 |
|:-----|:-----|:-----|
| **持仓跟踪** | 追踪知名投资者（如 Warren Buffett）的最新持仓变化 | `track "Warren Buffett"` |
| **股票分析** | 深度分析特定股票的技术面、基本面、新闻和市场情绪 | `analyze AAPL` |
| **股票筛选** | 根据复杂条件筛选符合要求的股票 | `screen "高股息科技股"` |
| **自然语言查询** | 支持中英文自然语言查询 | `ask "分析苹果公司"` |
| **决策仪表盘** | 每日扫描热门股票并生成报告 | `dashboard` |

---

## 快速开始

### 安装

```bash
git clone https://github.com/your-org/Clarity.git
cd Clarity

# 使用 uv（推荐）
uv sync
```

### 配置

创建 `.env` 文件：

```bash
# ===== 必需配置 =====
OPENAI_API_KEY=your_openai_api_key
FINNHUB_API_KEY=your_finnhub_api_key

# ===== 可选：网络搜索 =====
SERPER_API_KEY=your_serper_api_key
JINA_API_KEY=your_jina_api_key

# ===== 可选：通知渠道 =====
# 企业微信机器人
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx

# 飞书机器人
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx

# Telegram Bot
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
TELEGRAM_CHAT_ID=123456789

# 邮件 (QQ/163/Gmail 等自动识别 SMTP)
EMAIL_SENDER=your@qq.com
EMAIL_PASSWORD=授权码

# Pushover (iOS/Android 推送)
PUSHOVER_USER_KEY=xxx
PUSHOVER_API_TOKEN=xxx

# 自定义 Webhook (钉钉、Discord、Slack、Bark 等)
CUSTOM_WEBHOOK_URLS=https://oapi.dingtalk.com/robot/send?access_token=xxx
```

#### Qwen（OpenAI 兼容模式）

```bash
# ===== 可选：Qwen =====
# 运行时通过 CLI 参数切换：uv run run_agent.py --model qwen ...
QWEN_API_KEY=your_dashscope_api_key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-latest
```

Qwen 模式下如需联网检索，建议配置 `SERPER_API_KEY`。未配置时会回退为抓取 Google News，可能触发频控。

---

## 使用方法

### Web UI

```bash
# 启动环境
source .venv/bin/activate 

# 启动 Web 界面
uv run python webui.py

# 创建公开链接（通过 Gradio Share）
uv run python webui.py --share
```

访问 http://localhost:7860 即可使用图形界面。

<video src="https://github.com/user-attachments/assets/678ece2c-2fd9-4214-8470-22e401647e4b" controls width="800"></video>

### CLI 命令

```bash
# 分析股票
uv run python run_agent.py analyze AAPL
uv run python run_agent.py analyze NVDA --date 2025-01-15
uv run python run_agent.py --model qwen analyze AAPL

# 跟踪投资者持仓
uv run python run_agent.py track "Warren Buffett"

# 筛选股票
uv run python run_agent.py screen "high dividend yield tech stocks"

# 自然语言查询
uv run python run_agent.py ask "分析一下苹果公司的股票"

# 决策仪表盘
uv run python run_agent.py dashboard                           # 扫描 A股+美股
uv run python run_agent.py dashboard -m A股 港股              # 扫描指定市场
uv run python run_agent.py dashboard -n 20 -o report.md       # 推荐20只，保存到文件
uv run python run_agent.py dashboard --push                   # 扫描并推送通知
uv run python run_agent.py dashboard -p --push-to wechat      # 仅推送到企业微信
```

### Python 代码

```python
import asyncio
from clarity import FinancialAgentOrchestrator, AgentConfig, TaskType

async def main():
    orchestrator = FinancialAgentOrchestrator()

    # 分析股票
    result = await orchestrator.run(
        task_type=TaskType.STOCK_ANALYSIS,
        target="AAPL",
    )
    print(result["report"])

asyncio.run(main())
```

```python
# 使用通知服务
from clarity.core import NotificationService

notification = NotificationService()
notification.send("# 测试报告\n这是 Markdown 格式的消息")
```

---

## 工作流程

以 `run_track("Warren Buffett")` 为例，展示系统工作流程：

```
用户输入: uv run python run_agent.py track "Warren Buffett"
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    run_agent.py                             │
│                                                             │
│  1. 加载 .env 环境变量                                       │
│  2. 创建 AgentConfig                                        │
│  3. 创建 FinancialAgentOrchestrator                         │
│  4. 调用 orchestrator.run(task_type=HOLDINGS_TRACKING, ...) │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│               FinancialAgentOrchestrator                    │
│                                                             │
│  1. MasterAgent.create_task_plan()  ──► 初始化 task_plan.md │
│  2. WorkingAgent.execute_plan()     ──► 执行各 SubAgent     │
│  3. StateChecker.validate_step()    ──► 验证/重试           │
│  4. MasterAgent.synthesize_results() ──► 合成最终报告       │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                   SubAgents 执行                             │
│                                                             │
│  Step 1: HoldingsHunter                                     │
│    ├─► 搜索 SEC 13F 文件                                    │
│    ├─► 解析持仓数据                                         │
│    └─► 生成持仓报告                                         │
│                                                             │
│  Step 2: NewsAnalyst                                        │
│    └─► 搜索相关新闻并分析                                   │
│                                                             │
│  每步执行后更新 Planning Files:                              │
│    • findings.md  ←  追加分析结果                           │
│    • progress.md  ←  追加进度日志                           │
│    • task_plan.md ←  更新状态表                             │
└─────────────────────────────────────────────────────────────┘
```

### Planning-with-Files 模式

系统使用三个持久化文件来管理长任务：

| 文件 | 作用 | 更新时机 |
|:-----|:-----|:---------|
| `task_plan.md` | 任务计划、阶段状态、SubAgent 分配 | 任务开始、状态变更 |
| `findings.md` | 研究发现、API 返回数据、分析结果 | 每个 SubAgent 完成后 |
| `progress.md` | 执行日志、错误记录、重试追踪 | 每步操作后 |

**核心规则：**
- **2-Action Rule**：每 2 次操作后更新 `findings.md`
- **决策前重读**：关键决策前重读 `task_plan.md`
- **错误持久化**：所有错误都记录到文件，避免重复犯错

---

## 架构设计

```
Clarity/
├── run_agent.py          # CLI 入口
├── webui.py              # Web UI (Gradio)
├── templates/            # 规划文件模板
├── runtime/              # 运行时文件（git-ignored）
│   ├── task_plan.md
│   ├── findings.md
│   ├── progress.md
│   └── reports/
└── clarity/
    ├── core/             # 核心智能体
    │   ├── orchestrator.py     # 编排器
    │   ├── master_agent.py     # 主智能体（规划）
    │   ├── working_agent.py    # 工作智能体（执行）
    │   ├── state_checker.py    # 状态检查器
    │   ├── notification.py     # 通知服务
    │   ├── subagents/          # 子智能体
    │   │   ├── fundamentals_analyst.py
    │   │   ├── sentiment_analyst.py
    │   │   ├── news_analyst.py
    │   │   ├── technical_analyst.py
    │   │   ├── holdings_hunter.py
    │   │   ├── alpha_hound.py
    │   │   └── daily_dashboard.py
    │   └── tools/              # 工具
    │       ├── finnhub_tools.py
    │       ├── search_tools.py
    │       ├── dashboard_scanner.py
    │       └── data_provider/
    └── dataflows/        # 数据工具
```

### 子智能体

| 智能体 | 职责 | 使用场景 |
|:-------|:-----|:---------|
| **Fundamentals Analyst** | 分析公司财务报表和基本面指标 | 股票分析 |
| **Technical Analyst** | 分析技术指标（MACD、RSI、布林带等） | 股票分析 |
| **News Analyst** | 收集和分析相关新闻 | 所有任务 |
| **Sentiment Analyst** | 分析市场情绪和社交媒体讨论 | 股票分析 |
| **Holdings Hunter** | 追踪机构和知名投资者持仓 | 持仓跟踪 |
| **Alpha Hound** | 基于复杂条件筛选股票 | 股票筛选 |
| **Daily Dashboard** | 每日市场扫描和值得关注的股票 | 决策仪表盘 |

### 通知渠道

| 渠道 | 环境变量 | 消息格式 |
|:-----|:---------|:---------|
| 企业微信 | `WECHAT_WEBHOOK_URL` | Markdown |
| 飞书 | `FEISHU_WEBHOOK_URL` | Markdown 卡片 |
| Telegram | `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` | Markdown |
| 邮件 | `EMAIL_SENDER` + `EMAIL_PASSWORD` | HTML |
| Pushover | `PUSHOVER_USER_KEY` + `PUSHOVER_API_TOKEN` | 纯文本 |
| 自定义 Webhook | `CUSTOM_WEBHOOK_URLS` | 自动适配 |

---

## 配置选项

详见 `clarity/core/config.py`：

```python
from clarity import AgentConfig

config = AgentConfig(
    llm_provider="openai",              # openai, anthropic, google
    deep_think_llm="gpt-5.2",
    online_tools=True,                  # 使用在线工具
    max_retries=3,
)
```

---

## 支持与贡献

本项目由 Cooragent 团队提供技术支持。Cooragent 是自演进的多智能体平台，致力于让每个人都能成为 Agent 的指挥官。

### 🌟 支持我们

如果这个项目对您有帮助，请：

- ⭐ **给项目点个 Star** - 这是对我们最大的鼓励！
- 🐛 **提交 Issue** - 报告 Bug 或提出功能建议
- 🔀 **提交 PR** - 欢迎贡献代码和文档改进
- 💬 **加入社区** - 与其他用户交流使用经验

### 📮 联系我们


- 🌐 飞书: [cooragent](https://applink.feishu.cn/client/chat/chatter/add_by_link?link_token=251mf86f-8106-4361-81aa-05fa856abc05)
- 📧 问题反馈：请通过 [GitHub Issues](https://github.com/cooragent/Clarity/issues) 提交



## Star History

<a href="https://star-history.com/#cooragent/Clarity&Date">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=cooragent/Clarity&type=Date&theme=dark" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=cooragent/Clarity&type=Date" />
   <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=cooragent/Clarity&type=Date" />
 </picture>
</a>
