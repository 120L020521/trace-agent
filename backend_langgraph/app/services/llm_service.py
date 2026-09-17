"""LLM服务模块 - LangChain ChatOpenAI封装"""

import os
from langchain_openai import ChatOpenAI
from ..config import get_settings

# 全局LLM实例
_llm_instance = None


def get_llm() -> ChatOpenAI:
    """
    获取LLM实例(单例模式)

    Returns:
        ChatOpenAI实例
    """
    global _llm_instance

    if _llm_instance is None:
        settings = get_settings()

        # 优先使用LLM_API_KEY(兼容原配置),否则使用OPENAI_API_KEY
        api_key = os.getenv("LLM_API_KEY") or settings.openai_api_key
        base_url = os.getenv("LLM_BASE_URL") or settings.openai_base_url
        model = os.getenv("LLM_MODEL_ID") or settings.openai_model

        _llm_instance = ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=0.7,
            max_tokens=4096,
        )

        print(f"✅ LLM服务初始化成功")
        print(f"   模型: {model}")
        print(f"   Base URL: {base_url}")

    return _llm_instance


def reset_llm():
    """重置LLM实例(用于测试或重新配置)"""
    global _llm_instance
    _llm_instance = None
