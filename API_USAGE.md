# Financial Intelligence Agent API 使用文档

## 目录
- [简介](#简介)
- [安装与启动](#安装与启动)
- [API 端点](#api-端点)
- [使用示例](#使用示例)
- [测试](#测试)
- [配置](#配置)

## 简介

Financial Intelligence Agent API 提供了基于 FastAPI 的 RESTful 接口，用于访问金融智能分析功能。

**主要功能：**
- 股票分析 (Stock Analysis)
- 持仓追踪 (Holdings Tracking)
- 股票筛选 (Stock Screening)
- 自然语言查询 (Natural Language Query)
- 每日决策仪表盘 (Daily Dashboard)
- 消息通知推送 (Notification Service)

**技术栈：**
- FastAPI
- Pydantic (数据验证)
- Uvicorn (ASGI 服务器)
- Async/Await (异步处理)

## 安装与启动

### 1. 安装依赖

```bash
# 安装 FastAPI 和相关依赖
pip install fastapi uvicorn[standard] python-multipart

# 安装测试依赖（可选）
pip install pytest pytest-asyncio httpx
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
# LLM 配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
OPENAI_DEEP_MODEL=gpt-4

# 或使用通义千问
QWEN_API_KEY=your_qwen_api_key
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-plus
QWEN_DEEP_MODEL=qwen-max

# 通知渠道配置（可选）
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# API 服务配置
API_HOST=0.0.0.0
API_PORT=8000
```

### 3. 启动服务

```bash
# 方式 1: 直接运行
python api.py

# 方式 2: 使用 uvicorn (推荐用于生产环境)
uvicorn api:app --host 0.0.0.0 --port 8000 --reload

# 方式 3: 后台运行
nohup uvicorn api:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
```

服务启动后，访问：
- API 文档 (Swagger UI): http://localhost:8000/docs
- API 文档 (ReDoc): http://localhost:8000/redoc
- OpenAPI Schema: http://localhost:8000/openapi.json

## API 端点

### 基础端点

#### 1. 健康检查
```
GET /health
```

**响应示例：**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-21T10:30:00",
  "version": "1.0.0"
}
```

### 分析端点

#### 2. 股票分析
```
POST /api/v1/analyze
```

**请求体：**
```json
{
  "ticker": "AAPL",
  "trade_date": "2025-01-15",  // 可选
  "model": "openai"            // 可选: "openai" 或 "qwen"
}
```

**响应示例：**
```json
{
  "success": true,
  "task_type": "STOCK_ANALYSIS",
  "target": "AAPL",
  "trade_date": "2025-01-15",
  "report": "详细的股票分析报告...",
  "execution_summary": {
    "total_steps": 5,
    "successful_steps": 5,
    "failed_steps": 0
  },
  "files": {
    "task_plan": "runtime/sessions/xxx/task_plan.md",
    "findings": "runtime/sessions/xxx/findings.md"
  }
}
```

#### 3. 持仓追踪
```
POST /api/v1/track
```

**请求体：**
```json
{
  "investor_name": "Warren Buffett",
  "trade_date": "2025-01-15",  // 可选
  "model": "openai"            // 可选
}
```

**响应示例：**
```json
{
  "success": true,
  "task_type": "HOLDINGS_TRACKING",
  "target": "Warren Buffett",
  "trade_date": "2025-01-15",
  "report": "持仓追踪报告...",
  "execution_summary": {...},
  "files": {...}
}
```

#### 4. 股票筛选
```
POST /api/v1/screen
```

**请求体：**
```json
{
  "criteria": "high dividend yield tech stocks",
  "trade_date": "2025-01-15",  // 可选
  "model": "openai"            // 可选
}
```

**响应示例：**
```json
{
  "success": true,
  "task_type": "STOCK_SCREENING",
  "target": "high dividend yield tech stocks",
  "trade_date": "2025-01-15",
  "report": "筛选结果报告...",
  "execution_summary": {...},
  "files": {...}
}
```

#### 5. 自然语言查询
```
POST /api/v1/ask
```

**请求体：**
```json
{
  "query": "分析一下苹果公司的股票",
  "model": "openai"  // 可选
}
```

**响应示例：**
```json
{
  "success": true,
  "task_type": "NATURAL_LANGUAGE",
  "target": "分析一下苹果公司的股票",
  "trade_date": "2025-01-21",
  "report": "根据您的查询生成的分析报告...",
  "execution_summary": {...},
  "files": {...}
}
```

#### 6. 每日决策仪表盘
```
POST /api/v1/dashboard
```

**请求体：**
```json
{
  "markets": ["A股", "美股"],        // 可选，默认 ["A股", "美股"]
  "top_n": 10,                     // 可选，默认 10
  "push": false,                   // 可选，是否推送通知
  "push_channels": ["wechat"]      // 可选，指定推送渠道
}
```

**响应示例：**
```json
{
  "success": true,
  "date": "2025-01-21",
  "market_overviews": [
    {
      "market_type": "A股",
      "index_name": "上证指数",
      "index_value": 3250.5,
      "index_change_pct": 1.2,
      "up_count": 2500,
      "down_count": 1500,
      "total_amount": 850000
    }
  ],
  "recommendations": [
    {
      "code": "000001",
      "name": "平安银行",
      "market": "A股",
      "current_price": 12.5,
      "change_pct": 2.5,
      "score": 85,
      "signal": "极具潜力",
      "reasons": ["技术面强势突破", "基本面稳健"],
      "entry_price": 12.3,
      "stop_loss": 11.8,
      "target_price": 13.5
    }
  ],
  "summary": "市场总结...",
  "markdown": "# 📊 每日决策仪表盘...",
  "notification_sent": true
}
```

#### 7. 获取通知渠道
```
GET /api/v1/notification/channels
```

**响应示例：**
```json
{
  "available": true,
  "channels": ["wechat", "feishu", "telegram"]
}
```

## 使用示例

### Python 示例

#### 使用 requests 库

```python
import requests

API_BASE = "http://localhost:8000"

# 1. 健康检查
response = requests.get(f"{API_BASE}/health")
print(response.json())

# 2. 分析股票
response = requests.post(f"{API_BASE}/api/v1/analyze", json={
    "ticker": "AAPL",
    "model": "openai"
})
result = response.json()
print(f"分析成功: {result['success']}")
print(f"报告:\n{result['report']}")

# 3. 追踪投资者持仓
response = requests.post(f"{API_BASE}/api/v1/track", json={
    "investor_name": "Warren Buffett",
    "trade_date": "2025-01-15"
})
print(response.json())

# 4. 筛选股票
response = requests.post(f"{API_BASE}/api/v1/screen", json={
    "criteria": "高股息率科技股"
})
print(response.json())

# 5. 自然语言查询
response = requests.post(f"{API_BASE}/api/v1/ask", json={
    "query": "分析一下特斯拉最近的走势"
})
print(response.json())

# 6. 每日仪表盘
response = requests.post(f"{API_BASE}/api/v1/dashboard", json={
    "markets": ["A股"],
    "top_n": 5,
    "push": True,
    "push_channels": ["wechat"]
})
dashboard = response.json()
print(f"推荐股票数量: {len(dashboard['recommendations'])}")
print(f"Markdown 报告:\n{dashboard['markdown']}")
```

#### 使用 httpx 库（异步）

```python
import asyncio
import httpx

async def analyze_stocks():
    async with httpx.AsyncClient() as client:
        # 并发分析多只股票
        tickers = ["AAPL", "TSLA", "GOOGL"]
        tasks = [
            client.post("http://localhost:8000/api/v1/analyze",
                       json={"ticker": ticker})
            for ticker in tickers
        ]

        responses = await asyncio.gather(*tasks)

        for ticker, response in zip(tickers, responses):
            result = response.json()
            print(f"{ticker}: {result['success']}")

asyncio.run(analyze_stocks())
```

### cURL 示例

```bash
# 健康检查
curl http://localhost:8000/health

# 分析股票
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "model": "openai"}'

# 追踪投资者
curl -X POST http://localhost:8000/api/v1/track \
  -H "Content-Type: application/json" \
  -d '{"investor_name": "Warren Buffett"}'

# 筛选股票
curl -X POST http://localhost:8000/api/v1/screen \
  -H "Content-Type: application/json" \
  -d '{"criteria": "high dividend yield tech stocks"}'

# 自然语言查询
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "分析一下苹果公司的股票"}'

# 每日仪表盘
curl -X POST http://localhost:8000/api/v1/dashboard \
  -H "Content-Type: application/json" \
  -d '{
    "markets": ["A股", "美股"],
    "top_n": 10,
    "push": false
  }'

# 获取通知渠道
curl http://localhost:8000/api/v1/notification/channels
```

### JavaScript/TypeScript 示例

```typescript
// 使用 fetch API
const API_BASE = 'http://localhost:8000';

// 分析股票
async function analyzeStock(ticker: string) {
  const response = await fetch(`${API_BASE}/api/v1/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      ticker: ticker,
      model: 'openai'
    })
  });

  const result = await response.json();
  console.log(`分析 ${ticker}:`, result.success);
  console.log('报告:', result.report);
  return result;
}

// 每日仪表盘
async function getDashboard() {
  const response = await fetch(`${API_BASE}/api/v1/dashboard`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      markets: ['A股', '美股'],
      top_n: 10,
      push: false
    })
  });

  const dashboard = await response.json();
  console.log('推荐股票:', dashboard.recommendations);
  return dashboard;
}

// 使用示例
analyzeStock('AAPL');
getDashboard();
```

## 测试

### 运行测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio httpx pytest-cov

# 运行所有测试
pytest test_api.py -v

# 运行特定测试
pytest test_api.py::test_health_check -v

# 排除集成测试（不需要 API keys）
pytest test_api.py -v -m "not integration and not slow"

# 运行集成测试（需要配置 API keys）
pytest test_api.py -v -m integration

# 生成测试覆盖率报告
pytest test_api.py --cov=api --cov-report=html
# 查看报告: open htmlcov/index.html
```

### 测试覆盖的功能

- ✅ 基础端点 (健康检查, 根路径)
- ✅ 股票分析端点 (正常请求, 缺失参数, 无效数据)
- ✅ 持仓追踪端点
- ✅ 股票筛选端点
- ✅ 自然语言查询端点 (中英文)
- ✅ 仪表盘端点 (默认参数, 自定义市场, 推送通知)
- ✅ 通知渠道端点
- ✅ CORS 配置
- ✅ API 文档可访问性
- ✅ 错误处理 (404, 405, 422)
- ✅ 并发请求处理

## 配置

### 环境变量

| 变量名 | 说明 | 默认值 | 必填 |
|-------|------|--------|------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | - | 是* |
| `OPENAI_BASE_URL` | OpenAI API 地址 | https://api.openai.com/v1 | 否 |
| `OPENAI_MODEL` | OpenAI 快速模型 | - | 否 |
| `OPENAI_DEEP_MODEL` | OpenAI 深度模型 | - | 否 |
| `QWEN_API_KEY` | 通义千问 API 密钥 | - | 是* |
| `QWEN_BASE_URL` | 通义千问 API 地址 | https://dashscope.aliyuncs.com/compatible-mode/v1 | 否 |
| `QWEN_MODEL` | 通义千问快速模型 | qwen-latest | 否 |
| `QWEN_DEEP_MODEL` | 通义千问深度模型 | - | 否 |
| `API_HOST` | API 服务监听地址 | 0.0.0.0 | 否 |
| `API_PORT` | API 服务端口 | 8000 | 否 |
| `WECHAT_WEBHOOK_URL` | 企业微信 Webhook | - | 否 |
| `FEISHU_WEBHOOK_URL` | 飞书 Webhook | - | 否 |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | - | 否 |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID | - | 否 |

\* OpenAI 或 Qwen 至少配置一个

### 生产环境部署

#### 使用 Gunicorn + Uvicorn

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动服务（4 个 worker）
gunicorn api:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 300 \
  --access-logfile - \
  --error-logfile -
```

#### 使用 Docker

创建 `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

构建和运行：

```bash
# 构建镜像
docker build -t financial-agent-api .

# 运行容器
docker run -d \
  --name financial-api \
  -p 8000:8000 \
  --env-file .env \
  financial-agent-api

# 查看日志
docker logs -f financial-api
```

#### 使用 Docker Compose

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./runtime:/app/runtime
    restart: unless-stopped
```

启动：

```bash
docker-compose up -d
```

## 性能优化

### 1. 异步处理

API 使用 FastAPI 的异步特性，支持高并发请求。

### 2. 后台任务

仪表盘推送通知使用后台任务，不阻塞响应：

```python
background_tasks.add_task(send_notification)
```

### 3. 连接池

可配置数据库连接池大小（如果使用数据库）。

### 4. 缓存

可添加 Redis 缓存层缓存分析结果：

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
```

## 故障排除

### 1. 端口被占用

```bash
# 查找占用端口的进程
lsof -i :8000

# 杀死进程
kill -9 <PID>
```

### 2. API Keys 未配置

错误信息：`HTTP 500: API key not configured`

解决方案：检查 `.env` 文件中的 API key 配置。

### 3. 导入错误

错误信息：`ModuleNotFoundError: No module named 'clarity'`

解决方案：确保在项目根目录运行，或添加项目路径到 PYTHONPATH：

```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/Clarity"
```

### 4. 连接超时

增加超时配置：

```python
uvicorn api:app --timeout-keep-alive 300
```

## 安全建议

1. **生产环境使用 HTTPS**
2. **添加 API 认证（JWT、API Key 等）**
3. **限流保护**
4. **输入验证**
5. **日志脱敏**

示例：添加 API Key 认证

```python
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

API_KEY = "your-secret-api-key"
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
    return api_key

@app.post("/api/v1/analyze", dependencies=[Depends(verify_api_key)])
async def analyze_stock(request: AnalyzeRequest):
    ...
```

## 更多资源

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Uvicorn 文档](https://www.uvicorn.org/)
- [Pydantic 文档](https://docs.pydantic.dev/)
- [pytest 文档](https://docs.pytest.org/)

## 许可证

本项目遵循项目根目录的 LICENSE 文件。
