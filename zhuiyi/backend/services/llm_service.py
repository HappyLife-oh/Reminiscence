"""
LLM服务 - 统一调用不同API服务商
支持 OpenAI 兼容接口
"""

import logging
import asyncio
from openai import AsyncOpenAI
from typing import List, Dict, Optional, AsyncGenerator
from .config_service import ConfigService, PROVIDERS

logger = logging.getLogger(__name__)


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
        if not provider_info:
            raise ValueError(f"不支持的API服务商: {provider_name}")

        base_url = config.get("base_url", provider_info.get("base_url", ""))
        api_key = config.get("api_key", "")
        model = config.get("model", provider_info.get("default_model", ""))

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
        max_tokens: int = 2000,
    ) -> Dict:
        """非流式聊天"""
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
        max_tokens: int = 2000,
    ) -> AsyncGenerator[Dict, None]:
        """流式聊天，带重试和降级机制"""
        client, default_model, provider_name = self._get_client(provider)
        model = model or default_model

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
                return

            except ValueError:
                raise
            except Exception as e:
                last_error = e
                logger.warning(f"流式聊天尝试{attempt + 1}失败: {e}")
                if attempt < 2:
                    await asyncio.sleep(1 * (attempt + 1))
                    continue
                break

        # 流式失败，降级为非流式
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
            logger.error(f"聊天降级也失败: {e}")
            yield {
                "content": "[服务暂时不可用，请稍后重试]",
                "provider": provider_name,
                "model": model,
                "done": True,
                "error": True,
            }
