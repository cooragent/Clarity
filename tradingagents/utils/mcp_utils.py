# SPDX-FileCopyrightText: 2025 MiromindAI
#
# SPDX-License-Identifier: Apache-2.0

"""
TradingAgents MCP 工具加载工具，参考 youtu-agent 的 MCP 加载方式。

主要功能：
- create_tradingagents_mcp_server_parameters: 生成 TradingAgents MCP 服务器参数配置
- load_sub_agents_as_tools: 将子智能体作为工具加载
"""

import sys
import importlib
from pathlib import Path
from typing import List, Tuple
from mcp import StdioServerParameters
from omegaconf import DictConfig, OmegaConf


def create_tradingagents_mcp_server_parameters(
    agent_cfg: DictConfig,
    logs_dir: str | None = None
) -> Tuple[List[dict], set]:
    """
    生成 TradingAgents MCP 服务器参数配置
    
    参考: youtu-agent/MiroFlow/src/utils/tool_utils.py::create_mcp_server_parameters
    
    Args:
        agent_cfg: Agent 配置
        logs_dir: 日志目录（可选）
    
    Returns:
        (configs, blacklist) - MCP 服务器配置列表和黑名单
    """
    configs = []
    
    if agent_cfg.get("tool_config", None) is not None:
        for tool in agent_cfg["tool_config"]:
            try:
                config_path = (
                    Path(__file__).parent.parent.parent
                    / "config"
                    / "tool"
                    / f"{tool}.yaml"
                )
                tool_cfg = OmegaConf.load(config_path)
                configs.append(
                    {
                        "name": tool_cfg.get("name", tool),
                        "params": StdioServerParameters(
                            command=sys.executable
                            if tool_cfg["tool_command"] == "python"
                            else tool_cfg["tool_command"],
                            args=tool_cfg.get("args", []),
                            env=tool_cfg.get("env", {}),
                        ),
                    }
                )
            except Exception as e:
                print(f"[ERROR] Error creating MCP server parameters for tool {tool}: {e}")
                continue
    
    blacklist = set()
    for black_list_item in agent_cfg.get("tool_blacklist", []):
        blacklist.add((black_list_item[0], black_list_item[1]))
    
    return configs, blacklist


def _load_agent_prompt_class(prompt_class_name: str):
    """
    动态导入 Agent Prompt 类
    
    参考: youtu-agent/MiroFlow/src/utils/tool_utils.py::_load_agent_prompt_class
    """
    if not isinstance(prompt_class_name, str) or not prompt_class_name.isidentifier():
        raise ValueError(f"Invalid prompt class name: {prompt_class_name}")
    
    try:
        # 动态导入 config.agent_prompts 模块的类
        from tradingagents.config.agent_prompts.base_agent_prompt import BaseAgentPrompt
        from tradingagents.config import agent_prompts
        
        agent_prompts_module = importlib.import_module("tradingagents.config.agent_prompts")
        PromptClass = getattr(agent_prompts_module, prompt_class_name)
    except (ModuleNotFoundError, AttributeError) as e:
        raise ImportError(
            f"Could not import class '{prompt_class_name}' from 'tradingagents.config.agent_prompts': {e}"
        )
    return PromptClass()


def load_sub_agents_as_tools(sub_agents_cfg: DictConfig) -> List[dict]:
    """
    将子智能体作为工具加载
    
    参考: youtu-agent/MiroFlow/src/utils/tool_utils.py::expose_sub_agents_as_tools
    
    Args:
        sub_agents_cfg: 子智能体配置
    
    Returns:
        sub_agents_server_params - 子智能体工具定义列表
    """
    sub_agents_server_params = []
    
    for sub_agent in sub_agents_cfg.keys():
        if not sub_agent.startswith("agent-"):
            raise ValueError(
                f"Sub-agent name must start with 'agent-': {sub_agent}. Please check the sub-agent name in the agent's config file."
            )
        try:
            sub_agent_prompt_instance = _load_agent_prompt_class(
                sub_agents_cfg[sub_agent].prompt_class
            )
            sub_agent_tool_definition = sub_agent_prompt_instance.expose_agent_as_tool(
                subagent_name=sub_agent
            )
            sub_agents_server_params.append(sub_agent_tool_definition)
        except Exception as e:
            raise ValueError(f"Failed to expose sub-agent {sub_agent} as a tool: {e}")
    
    return sub_agents_server_params


def create_agent_prompt_template(skill_name: str, role_description: str, task_type: str) -> str:
    """
    创建 Agent Prompt 模板
    
    Args:
        skill_name: 技能名称
        role_description: 角色描述
        task_type: 任务类型（筛选/持仓/分析）
    
    Returns:
        prompt_template - Prompt 模板类代码
    """
    class_template = f"""
from config.agent_prompts.base_agent_prompt import BaseAgentPrompt
from typing import Dict, List
from omegaconf import DictConfig


class {skill_name}AgentPrompt(BaseAgentPrompt):
    \"\"\"
    {role_description}
    \"\"\"

    def __init__(self, cfg: DictConfig):
        super().__init__(cfg)
        self.skill_name = "{skill_name}"
        self.task_type = "{task_type}"
    
    def get_system_prompt(self) -> str:
        \"\"\"\"
        返回系统提示词
        \"\"\"
        base = super().get_system_prompt()
        
        task_guidance = ""
        if self.task_type == "screening":
            task_guidance = """
        你擅长基于复杂条件筛选股票。
        - 使用 FinnHub API 获取财务数据
        - 使用 SERPER API 和 JINA API 进行网络搜索和内容提取
        - 能够理解用户的自然语言筛选条件，并转换为可执行的查询
        - 输出结构化的候选列表和筛选理由
        """
        elif self.task_type == "holdings":
            task_guidance = """
        你擅长跟踪金融大佬的最新持仓。
        - 优先使用权威披露来源
        - 使用网络搜索补充最新信息
        - 能够整理持仓变化并识别增持/减持趋势
        - 输出结构化的持仓报告
        """
        elif self.task_type == "analysis":
            task_guidance = """
        你擅长深度分析特定股票。
        - 综合基本面、情绪、新闻、技术指标
        - 能够识别关键驱动因素和风险点
        - 输出结构化的分析报告和投资建议
        """
        
        return base + task_guidance
    
    def expose_agent_as_tool(self, subagent_name: str) -> dict:
        \"\"\"
        将此 Agent 暴露为工具定义
        \"\"\"
        return {{
            "name": subagent_name,
            "description": f"{{self.get_system_prompt()}}",
            "params": {{
                "type": "object",
                "properties": {{
                    "ticker": {{
                        "type": "string",
                        "description": "股票代码"
                    }},
                    "time_range": {{
                        "type": "string",
                        "description": "时间范围（可选）"
                    }},
                    "focus_areas": {{
                        "type": "array",
                        "items": {{"type": "string"}},
                        "description": "关注领域（可选）"
                    }}
                }},
                "required": ["ticker"]
            }}
        }}
"""
    
    return class_template
"""
    
    return class_template
