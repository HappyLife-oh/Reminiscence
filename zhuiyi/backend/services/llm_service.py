"""
LLM服务 - 统一调用不同API服务商
支持 OpenAI 兼容接口
"""

import asyncio
from openai import AsyncOpenAI
from typing import List, Dict, Optional, AsyncGenerator
from .config_service import ConfigService, PROVIDERS


class LLMService:
    """LLM服务 - 统一API调用"""

    def __init__(self, config_service: ConfigService):
        self.config_service = config_service

    def _get_client(self, provider_name: Optional[str] = None) -> tuple[AsyncOpenAI, str, str]:
        """获取API客户端"""
        if provider_name is None:
            provider_name = self.config_service._config.get("default_provider", "deepseek")

        config = self.config_service.get_provider_config(provider_name)
        if not config or not config.get("api_key"):
            raise ValueError(f"未配置 {provider_name} 的API密钥，请在设置中配置")

        provider_info = PROVIDERS.get(provider_name, {})
        base_url = config.get("base_url", provider_info.get("base_url", ""))
        api_key = config.get("api_key", "")
        model = config.get("model", provider_info.get("default_model", ""))

        # 创建httpx客户端，禁用系统代理以避免连接问题
        import httpx
        http_client = httpx.AsyncClient(
            proxy=None,
            timeout=60.0,
            trust_env=False,
        )
        
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=60.0,
            max_retries=2,
            http_client=http_client,
        )

        return client, model, provider_name

    async def chat(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.8,
        max_tokens: int = 500,
    ) -> Dict:
        """
        非流式聊天
        """
        client, default_model, provider_name = self._get_client(provider)
        model = model or default_model

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )

        # 处理推理模型（如MiMo）的reasoning_content
        content = response.choices[0].message.content or ""
        reasoning = getattr(response.choices[0].message, 'reasoning_content', None)
        
        # 如果content为空但有reasoning_content，说明token全部用于推理
        # 将推理内容作为回复返回
        if not content and reasoning:
            content = reasoning

        return {
            "content": content,
            "provider": provider_name,
            "model": model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
        }

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.8,
        max_tokens: int = 500,
    ) -> AsyncGenerator[Dict, None]:
        """
        流式聊天，带重试和降级机制
        """
        client, default_model, provider_name = self._get_client(provider)
        model = model or default_model

        # 尝试流式请求，最多重试2次
        last_error = None
        for attempt in range(3):
            try:
                stream = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                )

                async for chunk in stream:
                    if chunk.choices:
                        delta = chunk.choices[0].delta
                        # 优先使用content，如果没有则使用reasoning_content
                        content = delta.content or getattr(delta, 'reasoning_content', None) or ""
                        if content:
                            yield {
                                "content": content,
                                "provider": provider_name,
                                "model": model,
                                "done": False,
                            }

                yield {
                    "content": "",
                    "provider": provider_name,
                    "model": model,
                    "done": True,
                }
                return  # 成功，退出

            except Exception as e:
                last_error = e
                if attempt < 2:
                    # 等待后重试
                    await asyncio.sleep(1 * (attempt + 1))
                    continue
                break

        # 流式失败，降级为非流式请求
        try:
            result = await self.chat(
                messages=messages,
                provider=provider,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            yield {
                "content": result["content"],
                "provider": provider_name,
                "model": model,
                "done": False,
            }
            yield {
                "content": "",
                "provider": provider_name,
                "model": model,
                "done": True,
            }
        except Exception as e:
            yield {
                "content": f"[连接错误: {str(last_error or e)}]",
                "provider": provider_name,
                "model": model,
                "done": True,
                "error": True,
            }
