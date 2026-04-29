"""
配置路由 - 管理API配置
"""

from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class ProviderConfig(BaseModel):
    """API服务商配置"""
    name: str
    api_key: str
    base_url: str
    model: Optional[str] = None


class AppConfig(BaseModel):
    """应用配置"""
    default_provider: Optional[str] = None
    default_model: Optional[str] = None


@router.get("/providers")
async def list_providers(request: Request):
    """列出所有API服务商及其状态"""
    config_service = request.app.state.config_service
    return config_service.get_all_providers()


@router.post("/providers/{provider_name}")
async def update_provider(
    request: Request,
    provider_name: str,
    config: ProviderConfig,
):
    """更新API服务商配置"""
    config_service = request.app.state.config_service
    config_service.update_provider(provider_name, config.model_dump())
    return {"status": "ok", "message": f"已更新 {provider_name} 配置"}


@router.get("/app")
async def get_app_config(request: Request):
    """获取应用配置"""
    config_service = request.app.state.config_service
    return config_service.get_app_config()


@router.post("/app")
async def update_app_config(request: Request, config: AppConfig):
    """更新应用配置"""
    config_service = request.app.state.config_service
    config_service.update_app_config(config.model_dump(exclude_none=True))
    return {"status": "ok", "message": "已更新应用配置"}
