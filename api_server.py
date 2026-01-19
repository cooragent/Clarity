
#!/usr/bin/env python3
"""FastAPI server for the Financial Intelligence Agent.

Usage:
    # Start the server
    uvicorn api_server:app --reload --port 8000

    # Or run directly
    python api_server.py
"""

import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

from tradingagents.core import (
    AgentConfig,
    FinancialAgentOrchestrator,
    TaskType,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Global orchestrator instance
_orchestrator: FinancialAgentOrchestrator | None = None


def get_orchestrator() -> FinancialAgentOrchestrator:
    """Get or create the orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        config = AgentConfig()
        _orchestrator = FinancialAgentOrchestrator(config)
    return _orchestrator


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    logger.info("Starting Financial Intelligence Agent API...")
    get_orchestrator()  # Pre-initialize
    logger.info("API server ready!")
    yield
    # Shutdown
    logger.info("Shutting down API server...")


# Create FastAPI app
app = FastAPI(
    title="Financial Intelligence Agent API",
    description="""
    AI-powered financial analysis agent with multiple specialized sub-agents.
    
    ## Features
    - **Stock Analysis**: Deep analysis of specific stocks
    - **Holdings Tracking**: Track famous investors' portfolios
    - **Stock Screening**: Screen stocks based on complex criteria
    - **Natural Language**: Process queries in natural language
    
    ## Sub-Agents
    - Technical Analyst
    - Fundamentals Analyst
    - News Analyst
    - Sentiment Analyst
    - Holdings Hunter
    - Alpha Hound
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== Request/Response Models ==========

class AnalyzeRequest(BaseModel):
    """Request model for stock analysis."""

    ticker: str = Field(..., description="Stock ticker symbol (e.g., AAPL, NVDA)")
    trade_date: str | None = Field(
        None, description="Trade date in YYYY-MM-DD format. Defaults to today."
    )
    look_back_days: int = Field(7, description="Number of days to look back")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"ticker": "AAPL", "trade_date": "2025-01-18", "look_back_days": 7}
            ]
        }
    }


class TrackRequest(BaseModel):
    """Request model for holdings tracking."""

    investor_name: str = Field(
        ..., description="Investor name (e.g., Warren Buffett, Ray Dalio)"
    )
    trade_date: str | None = Field(
        None, description="Trade date in YYYY-MM-DD format. Defaults to today."
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{"investor_name": "Warren Buffett", "trade_date": "2025-01-18"}]
        }
    }


class ScreenRequest(BaseModel):
    """Request model for stock screening."""

    criteria: str = Field(
        ..., description="Screening criteria (e.g., 'high dividend yield low PE tech stocks')"
    )
    trade_date: str | None = Field(
        None, description="Trade date in YYYY-MM-DD format. Defaults to today."
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"criteria": "high dividend yield low PE tech stocks", "trade_date": "2025-01-18"}
            ]
        }
    }


class AskRequest(BaseModel):
    """Request model for natural language query."""

    query: str = Field(..., description="Natural language query")

    model_config = {
        "json_schema_extra": {
            "examples": [{"query": "分析一下苹果公司的股票"}]
        }
    }


class ExecutionSummary(BaseModel):
    """Execution summary model."""

    total_steps: int
    successful_steps: int
    failed_steps: int


class AgentResponse(BaseModel):
    """Response model for agent operations."""

    success: bool = Field(..., description="Whether the task completed successfully")
    task_type: str = Field(..., description="Type of task executed")
    target: str = Field(..., description="Target of the analysis")
    trade_date: str = Field(..., description="Trade date used for analysis")
    report: str = Field(..., description="Generated analysis report")
    execution_summary: ExecutionSummary | None = Field(
        None, description="Summary of execution steps"
    )
    error: str | None = Field(None, description="Error message if failed")
    files: dict[str, str] | None = Field(
        None, description="Paths to generated planning files"
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    available_agents: list[str]


# ========== API Endpoints ==========

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Financial Intelligence Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "analyze": "/api/v1/analyze",
            "track": "/api/v1/track",
            "screen": "/api/v1/screen",
            "ask": "/api/v1/ask",
        },
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    orchestrator = get_orchestrator()
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        available_agents=orchestrator.get_available_agents(),
    )


@app.post("/api/v1/analyze", response_model=AgentResponse, tags=["Analysis"])
async def analyze_stock(request: AnalyzeRequest):
    """
    Analyze a specific stock.
    
    Performs comprehensive analysis including:
    - Technical indicators (SMA, MACD, RSI, Bollinger Bands)
    - Fundamental analysis (financial statements, ratios)
    - News analysis
    - Sentiment analysis
    """
    orchestrator = get_orchestrator()
    trade_date = request.trade_date or datetime.now().strftime("%Y-%m-%d")

    logger.info(f"Analyzing stock: {request.ticker}")

    try:
        result = await orchestrator.run(
            task_type=TaskType.STOCK_ANALYSIS,
            target=request.ticker.upper(),
            trade_date=trade_date,
            look_back_days=request.look_back_days,
        )
        return _format_response(result)
    except Exception as e:
        logger.error(f"Error analyzing stock: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/track", response_model=AgentResponse, tags=["Holdings"])
async def track_holdings(request: TrackRequest):
    """
    Track an investor's holdings.
    
    Searches for:
    - SEC 13F filings
    - Portfolio holdings
    - Recent buys/sells
    - Related news
    """
    orchestrator = get_orchestrator()
    trade_date = request.trade_date or datetime.now().strftime("%Y-%m-%d")

    logger.info(f"Tracking holdings for: {request.investor_name}")

    try:
        result = await orchestrator.run(
            task_type=TaskType.HOLDINGS_TRACKING,
            target=request.investor_name,
            trade_date=trade_date,
        )
        return _format_response(result)
    except Exception as e:
        logger.error(f"Error tracking holdings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/screen", response_model=AgentResponse, tags=["Screening"])
async def screen_stocks(request: ScreenRequest):
    """
    Screen stocks based on criteria.
    
    Supports criteria like:
    - Valuation: "low PE", "undervalued"
    - Growth: "high revenue growth"
    - Dividend: "high dividend yield"
    - Technical: "above 50 SMA", "RSI oversold"
    - Sector: "tech stocks", "healthcare"
    """
    orchestrator = get_orchestrator()
    trade_date = request.trade_date or datetime.now().strftime("%Y-%m-%d")

    logger.info(f"Screening stocks with criteria: {request.criteria}")

    try:
        result = await orchestrator.run(
            task_type=TaskType.STOCK_SCREENING,
            target=request.criteria,
            trade_date=trade_date,
        )
        return _format_response(result)
    except Exception as e:
        logger.error(f"Error screening stocks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/ask", response_model=AgentResponse, tags=["Natural Language"])
async def ask_query(request: AskRequest):
    """
    Process a natural language query.
    
    The agent will:
    1. Analyze the query to determine task type
    2. Extract the target (stock/investor/criteria)
    3. Execute the appropriate analysis
    
    Supports queries in English and Chinese.
    """
    orchestrator = get_orchestrator()

    logger.info(f"Processing natural language query: {request.query}")

    try:
        result = await orchestrator.run_from_natural_language(request.query)
        return _format_response(result)
    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/files/{file_type}", tags=["Files"])
async def get_planning_file(file_type: str):
    """
    Get the content of a planning file.
    
    Available file types:
    - task_plan: Current task plan
    - findings: Research findings
    - progress: Execution progress log
    """
    orchestrator = get_orchestrator()
    files = orchestrator.get_planning_files()

    if file_type not in files:
        raise HTTPException(
            status_code=404,
            detail=f"File type '{file_type}' not found. Available: {list(files.keys())}",
        )

    file_path = files[file_type]
    if not file_path.exists():
        raise HTTPException(
            status_code=404, detail=f"File '{file_path}' does not exist yet."
        )

    return FileResponse(file_path, media_type="text/markdown")


@app.get("/api/v1/agents", tags=["Agents"])
async def list_agents():
    """List all available sub-agents."""
    orchestrator = get_orchestrator()
    agents = orchestrator.get_available_agents()

    agent_info = {
        "fundamentals_analyst": {
            "name": "Fundamentals Analyst",
            "description": "Analyzes company fundamentals and financial statements",
        },
        "sentiment_analyst": {
            "name": "Sentiment Analyst",
            "description": "Analyzes social media and public sentiment",
        },
        "news_analyst": {
            "name": "News Analyst",
            "description": "Gathers and analyzes relevant news",
        },
        "technical_analyst": {
            "name": "Technical Analyst",
            "description": "Analyzes technical indicators and price trends",
        },
        "holdings_hunter": {
            "name": "Holdings Hunter",
            "description": "Tracks institutional and guru holdings",
        },
        "alpha_hound": {
            "name": "Alpha Hound",
            "description": "Screens stocks based on complex criteria",
        },
    }

    return {
        "available_agents": agents,
        "agent_details": {k: v for k, v in agent_info.items() if k in agents},
    }


# ========== Helper Functions ==========

def _format_response(result: dict[str, Any]) -> AgentResponse:
    """Format the orchestrator result into API response."""
    execution_summary = None
    if "execution_summary" in result:
        summary = result["execution_summary"]
        execution_summary = ExecutionSummary(
            total_steps=summary.get("total_steps", 0),
            successful_steps=summary.get("successful_steps", 0),
            failed_steps=summary.get("failed_steps", 0),
        )

    return AgentResponse(
        success=result.get("success", False),
        task_type=result.get("task_type", ""),
        target=result.get("target", ""),
        trade_date=result.get("trade_date", ""),
        report=result.get("report", ""),
        execution_summary=execution_summary,
        error=result.get("error"),
        files=result.get("files"),
    )


# ========== Main ==========

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
