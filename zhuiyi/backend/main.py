"""
追忆 - AI数字人后端服务
FastAPI 应用入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routers import chat, config as config_router, data_import, tts
from services.llm_service import LLMService
from services.config_service import ConfigService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    config_service = ConfigService()
    llm_service = LLMService(config_service)
    app.state.config_service = config_service
    app.state.llm_service = llm_service
    print("[OK] 追忆后端服务启动")
    yield
    # 关闭时清理
    print("[OK] 追忆后端服务关闭")


app = FastAPI(
    title="追忆 - AI数字人后端",
    description="此情可待成追忆，只是当时已惘然",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat.router, prefix="/api/chat", tags=["聊天"])
app.include_router(config_router.router, prefix="/api/config", tags=["配置"])
app.include_router(data_import.router, prefix="/api/data", tags=["数据导入"])
app.include_router(tts.router, prefix="/api/tts", tags=["语音合成"])


@app.get("/")
async def root():
    return {
        "name": "追忆",
        "version": "1.0.0",
        "description": "此情可待成追忆，只是当时已惘然",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
