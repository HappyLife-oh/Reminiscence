"""
聊天路由 - 处理对话请求
"""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import json

from services.character_service import CharacterService

router = APIRouter()

# 初始化人物服务
character_service = CharacterService()


class Message(BaseModel):
    """消息模型"""
    role: str  # "user" | "assistant" | "system"
    content: str


class ChatRequest(BaseModel):
    """聊天请求模型"""
    messages: List[Message]
    provider: Optional[str] = None  # API服务商
    model: Optional[str] = None  # 模型名称
    character_id: Optional[str] = None  # 人物ID
    temperature: Optional[float] = 0.8
    max_tokens: Optional[int] = 500
    stream: Optional[bool] = True


class ChatResponse(BaseModel):
    """聊天响应模型"""
    content: str
    provider: str
    model: str
    usage: Optional[dict] = None


def _build_messages_with_character(
    messages: List[Message],
    character_id: Optional[str],
) -> List[dict]:
    """如果指定了人物ID，注入系统提示词"""
    result = []

    if character_id:
        system_prompt = character_service.load_system_prompt(character_id)
        if system_prompt:
            result.append({"role": "system", "content": system_prompt})

    for msg in messages:
        result.append(msg.model_dump())

    return result


@router.post("/completions")
async def chat_completions(request: Request, chat_request: ChatRequest):
    """
    聊天补全接口
    支持流式和非流式响应，支持人物档案关联
    """
    llm_service = request.app.state.llm_service

    # 构建消息列表（注入人物系统提示词）
    api_messages = _build_messages_with_character(
        chat_request.messages,
        chat_request.character_id,
    )

    if chat_request.stream:
        # 流式响应
        async def generate():
            async for chunk in llm_service.chat_stream(
                messages=api_messages,
                provider=chat_request.provider,
                model=chat_request.model,
                temperature=chat_request.temperature,
                max_tokens=chat_request.max_tokens,
            ):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        # 非流式响应
        result = await llm_service.chat(
            messages=api_messages,
            provider=chat_request.provider,
            model=chat_request.model,
            temperature=chat_request.temperature,
            max_tokens=chat_request.max_tokens,
        )
        return result


@router.get("/providers")
async def get_providers(request: Request):
    """获取可用的API服务商列表"""
    config_service = request.app.state.config_service
    return config_service.get_available_providers()
