"""
聊天路由 - 处理对话请求
支持人物档案关联、RAG记忆检索和Prompt工程优化
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, field_validator
from typing import List, Optional
import json

from services.character_service import CharacterService
from services.memory_service import MemoryService
from services.prompt_service import PromptService

logger = logging.getLogger(__name__)
router = APIRouter()

# 初始化服务
character_service = CharacterService()
memory_service = MemoryService()
prompt_service = PromptService()


class Message(BaseModel):
    """消息模型"""
    role: str  # "user" | "assistant" | "system"
    content: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        allowed = {"user", "assistant", "system"}
        if v not in allowed:
            raise ValueError(f"role必须是{allowed}之一")
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("content不能为空")
        if len(v) > 10000:
            raise ValueError("content长度不能超过10000字符")
        return v


class ChatRequest(BaseModel):
    """聊天请求模型"""
    messages: List[Message]
    provider: Optional[str] = None
    model: Optional[str] = None
    character_id: Optional[str] = None
    temperature: Optional[float] = 0.8
    max_tokens: Optional[int] = 2000
    stream: Optional[bool] = True

    @field_validator("messages")
    @classmethod
    def validate_messages(cls, v):
        if not v:
            raise ValueError("messages不能为空")
        if len(v) > 50:
            raise ValueError("messages数量不能超过50条")
        return v

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v):
        if v is not None and (v < 0 or v > 2):
            raise ValueError("temperature必须在0-2之间")
        return v

    @field_validator("max_tokens")
    @classmethod
    def validate_max_tokens(cls, v):
        if v is not None and (v < 1 or v > 8000):
            raise ValueError("max_tokens必须在1-8000之间")
        return v


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
    """如果指定了人物ID，注入优化后的系统提示词、RAG记忆和情感状态"""
    result = []

    if character_id:
        profile = character_service.load_character(character_id)

        if profile:
            user_messages = [m for m in messages if m.role == "user"]
            current_query = user_messages[-1].content if user_messages else ""

            emotion = prompt_service.analyze_emotion(current_query)
            time_context = prompt_service.get_time_context()

            context_memories = memory_service.get_context_memories(
                character_id=character_id,
                current_message=current_query,
                recent_messages=[],
                top_k=3,
            )

            system_prompt = prompt_service.generate_system_prompt(
                profile=profile,
                emotion_state=emotion,
            )

            if context_memories:
                system_prompt += f"\n\n# 相关记忆\n{context_memories}"

            if time_context:
                system_prompt += f"\n\n# 时间提示\n{time_context}"

            result.append({"role": "system", "content": system_prompt})
        else:
            # 人物不存在，降级为普通对话
            logger.warning(f"人物不存在: {character_id}")

    for msg in messages:
        result.append(msg.model_dump())

    return result


@router.post("/completions")
async def chat_completions(request: Request, chat_request: ChatRequest):
    """
    聊天补全接口
    支持流式和非流式响应，支持人物档案关联、RAG记忆和Prompt优化
    """
    llm_service = request.app.state.llm_service

    api_messages = _build_messages_with_character(
        chat_request.messages,
        chat_request.character_id,
    )

    try:
        if chat_request.stream:
            async def generate():
                try:
                    async for chunk in llm_service.chat_stream(
                        messages=api_messages,
                        provider=chat_request.provider,
                        model=chat_request.model,
                        temperature=chat_request.temperature,
                        max_tokens=chat_request.max_tokens,
                    ):
                        yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                    yield "data: [DONE]\n\n"
                except ValueError as e:
                    error_chunk = {"content": f"[配置错误: {str(e)}]", "error": True, "done": True}
                    yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    logger.error(f"流式聊天失败: {e}")
                    error_chunk = {"content": "[服务暂时不可用，请稍后重试]", "error": True, "done": True}
                    yield f"data: {json.dumps(error_chunk, ensure_ascii=False)}\n\n"
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
            result = await llm_service.chat(
                messages=api_messages,
                provider=chat_request.provider,
                model=chat_request.model,
                temperature=chat_request.temperature,
                max_tokens=chat_request.max_tokens,
            )
            return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"聊天请求失败: {e}")
        raise HTTPException(status_code=500, detail="服务暂时不可用，请稍后重试")


@router.get("/providers")
async def get_providers(request: Request):
    """获取可用的API服务商列表"""
    config_service = request.app.state.config_service
    return config_service.get_available_providers()


@router.get("/memory/{character_id}/stats")
async def get_memory_stats(character_id: str):
    """获取人物记忆统计"""
    return memory_service.get_memory_stats(character_id)


@router.get("/memory/{character_id}/search")
async def search_memory(character_id: str, query: str, top_k: int = 5):
    """搜索人物记忆"""
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="query不能为空")
    if top_k < 1 or top_k > 20:
        raise HTTPException(status_code=400, detail="top_k必须在1-20之间")
    return memory_service.search_memories(character_id, query, top_k)
