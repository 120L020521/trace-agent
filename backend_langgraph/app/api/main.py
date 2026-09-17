"""FastAPI 主应用与 Agent Runtime 就绪探针。"""

import os
import shutil

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ..config import get_settings, validate_config, print_config
from .routes import flywheel, trip, poi, knowledge, map as map_routes

# 获取配置
settings = get_settings()

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于LangGraph+MCP架构的智能旅行规划助手API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(trip.router, prefix="/api")
app.include_router(poi.router, prefix="/api")
app.include_router(map_routes.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api")
app.include_router(flywheel.router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    print("\n" + "="*60)
    print(f"🚀 {settings.app_name} v{settings.app_version}")
    print("="*60)
    
    # 打印配置信息
    print_config()
    
    # 验证配置
    try:
        validate_config()
        print("\n✅ 配置验证通过")
    except ValueError as e:
        print(f"\n❌ 配置验证失败:\n{e}")
        print("\n请检查.env文件并确保所有必要的配置项都已设置")
        raise
    
    print("\n" + "="*60)
    print("📚 API文档: http://localhost:8000/docs")
    print("📖 ReDoc文档: http://localhost:8000/redoc")
    print("="*60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    print("\n" + "="*60)
    print("👋 应用正在关闭...")
    print("="*60 + "\n")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health():
    """返回进程健康和关键运行依赖，不触发真实模型或外部工具调用。"""
    checks = {
        "llm": {
            "ready": bool(os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or settings.openai_api_key),
            "detail": "LLM API 凭证已配置",
        },
        "amap": {
            "ready": bool(settings.amap_api_key),
            "detail": "高德 Web 服务 Key 已配置",
        },
        "mcp_runtime": {
            "ready": shutil.which("uvx") is not None,
            "detail": "uvx 可用于启动高德 MCP Server",
        },
    }
    for check in checks.values():
        if not check["ready"]:
            check["detail"] = check["detail"].replace("已配置", "未配置").replace("可用于", "不可用于")
    ready = all(check["ready"] for check in checks.values())
    return {
        "status": "ready" if ready else "degraded",
        "process_healthy": True,
        "agent_ready": ready,
        "service": settings.app_name,
        "version": settings.app_version,
        "checks": checks,
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
