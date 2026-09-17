"""MCP服务层 - 通过MCP SDK连接amap-mcp-server,将工具适配为LangChain工具"""

import asyncio
import json
from typing import List, Dict, Any, Optional, Type
from pydantic import BaseModel, Field, create_model

from langchain_core.tools import BaseTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from ..config import get_settings


class AmapMCPTool(BaseTool):
    """高德地图MCP工具适配器 - 将单个MCP工具封装为LangChain BaseTool"""

    name: str
    description: str
    args_schema: Optional[Type[BaseModel]] = None
    _server_params: StdioServerParameters = None

    def __init__(self, name: str, description: str, input_schema: Dict[str, Any], server_params: StdioServerParameters):
        """初始化工具

        Args:
            name: 工具名称
            description: 工具描述
            input_schema: 工具的输入参数JSON Schema
            server_params: MCP服务器参数
        """
        super().__init__(
            name=name,
            description=description,
        )
        self._server_params = server_params
        self.args_schema = self._build_args_schema(name, input_schema)

    def _build_args_schema(self, name: str, input_schema: Dict[str, Any]) -> Type[BaseModel]:
        """根据MCP工具的inputSchema构建Pydantic模型"""
        properties = input_schema.get("properties", {})
        required = set(input_schema.get("required", []))

        fields = {}
        for param_name, param_info in properties.items():
            param_type = param_info.get("type", "string")
            param_desc = param_info.get("description", "")
            is_required = param_name in required

            if param_type == "string":
                field_type = str
            elif param_type == "integer":
                field_type = int
            elif param_type == "number":
                field_type = float
            elif param_type == "boolean":
                field_type = bool
            elif param_type == "array":
                field_type = List[str]
            else:
                field_type = str

            if is_required:
                fields[param_name] = (field_type, Field(description=param_desc))
            else:
                fields[param_name] = (Optional[field_type], Field(default=None, description=param_desc))

        return create_model(f"{name}_Args", **fields)

    def _run(self, **kwargs) -> str:
        """同步调用MCP工具"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果在运行中的事件循环内(如Jupyter/FastAPI),使用nest_asyncio或创建新线程
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._arun(**kwargs))
                    return future.result()
            else:
                return loop.run_until_complete(self._arun(**kwargs))
        except RuntimeError:
            # 没有事件循环
            return asyncio.run(self._arun(**kwargs))

    async def _arun(self, **kwargs) -> str:
        """异步调用MCP工具"""
        async with stdio_client(self._server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(self.name, arguments=kwargs)

                # 解析结果
                texts = []
                for content in result.content:
                    if hasattr(content, "text"):
                        texts.append(content.text)
                    else:
                        texts.append(str(content))
                return "\n".join(texts)


class MCPService:
    """MCP服务管理器 - 管理amap-mcp-server连接和工具列表"""

    def __init__(self):
        self.settings = get_settings()
        self._server_params = StdioServerParameters(
            command="uvx",
            args=["amap-mcp-server"],
            env={"AMAP_MAPS_API_KEY": self.settings.amap_api_key}
        )
        self._tools: Optional[List[BaseTool]] = None

    async def _fetch_tools(self) -> List[Dict[str, Any]]:
        """从MCP服务器获取工具列表"""
        async with stdio_client(self._server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools_response = await session.list_tools()
                return [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                    }
                    for tool in tools_response.tools
                ]

    def get_tools(self) -> List[BaseTool]:
        """获取适配后的LangChain工具列表(同步入口)"""
        if self._tools is not None:
            return self._tools

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._fetch_tools())
                    raw_tools = future.result()
            else:
                raw_tools = loop.run_until_complete(self._fetch_tools())
        except RuntimeError:
            raw_tools = asyncio.run(self._fetch_tools())

        self._tools = []
        for tool_info in raw_tools:
            adapted = AmapMCPTool(
                name=tool_info["name"],
                description=tool_info["description"],
                input_schema=tool_info["input_schema"],
                server_params=self._server_params,
            )
            self._tools.append(adapted)

        print(f"✅ MCP工具加载成功: {len(self._tools)} 个工具")
        return self._tools

    def get_tool_by_name(self, name: str) -> Optional[BaseTool]:
        """根据名称获取特定工具"""
        tools = self.get_tools()
        for tool in tools:
            if tool.name == name:
                return tool
        return None


# 全局MCP服务实例
_mcp_service: Optional[MCPService] = None


def get_mcp_service() -> MCPService:
    """获取MCP服务实例(单例)"""
    global _mcp_service
    if _mcp_service is None:
        _mcp_service = MCPService()
    return _mcp_service


def get_mcp_tools() -> List[BaseTool]:
    """便捷函数:直接获取MCP工具列表"""
    return get_mcp_service().get_tools()
