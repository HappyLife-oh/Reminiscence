"""
聊天路由 - 处理对话请求
支持人物档案关联、RAG记忆检索和Prompt工程优化
"""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import json

from services.character_service import CharacterService
from services.memory_service import MemoryService
from services.prompt_service import PromptService

router = APIRouter()

# 初始化服务
character_service = CharacterService()
memory_service = MemoryService()
prompt_service = PromptService()


class Message(BaseModel):
    """消息模型"""
    role: str  # "user" | "assistant" | "system"
    content: str


class ChatRequest(BaseModel):
    """聊天请求模型"""
    messages: List[Message]
    provider: Optional[str] = None
    model: Optional[str] = None
    character_id: Optional[str] = None
    temperature: Optional[float] = 0.8
    max_tokens: Optional[int] = 2000
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
    """如果指定了人物ID，注入优化后的系统提示词、RAG记忆和情感状态"""
    result = []

    if character_id:
        # 加载人物档案
        profile = character_service.load_character(character_id)

        if profile:
            # 获取当前用户消息
            user_messages = [m for m in messages if m.role == "user"]
            current_query = user_messages[-1].content if user_messages else ""

            # 分析用户情感
            emotion = prompt_service.analyze_emotion(current_query)

            # 获取时间上下文
            time_context = prompt_service.get_time_context()

            # 检索相关记忆
            context_memories = memory_service.get_context_memories(
                character_id=character_id,
                current_message=current_query,
                recent_messages=[],
                top_k=3,
            )

            # 使用PromptService生成优化的系统提示词
            system_prompt = prompt_service.generate_system_prompt(
                profile=profile,
                emotion_state=emotion,
            )

            # 注入RAG记忆
            if context_memories:
                system_prompt += f"\n\n# 相关记忆\n{context_memories}"

            # 注入时间上下文
            if time_context:
                system_prompt += f"\n\n# 时间提示\n{time_context}"

            result.append({"role": "system", "content": system_prompt})
        else:
            # 降级：使用旧的系统提示词
            system_prompt = character_service.load_system_prompt(character_id)
            if system_prompt:
                # 仍然注入RAG记忆
                user_messages = [m for m in messages if m.role == "user"]
                current_query = user_messages[-1].content if user_messages else ""
                context_memories = memory_service.get_context_memories(
                    character_id=character_id,
                    current_message=current_query,
                    recent_messages=[],
                    top_k=3,
                )
                if context_memories:
                    system_prompt += f"\n\n# 相关记忆\n{context_memories}"
                result.append({"role": "system", "content": system_prompt})

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

    # 构建消息列表（注入优化的系统提示词）
    api_messages = _build_messages_with_character(
        chat_request.messages,
        chat_request.character_id,
    )

    if chat_request.stream:
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


@router.get("/memory/{character_id}/stats")
async def get_memory_stats(character_id: str):
    """获取人物记忆统计"""
    return memory_service.get_memory_stats(character_id)


@router.get("/memory/{character_id}/search")
async def search_memory(character_id: str, query: str, top_k: int = 5):
    """搜索人物记忆"""
    return memory_service.search_memories(character_id, query, top_k)
