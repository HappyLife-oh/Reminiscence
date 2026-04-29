"""
配置服务 - 管理API密钥和应用配置
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 配置文件路径
CONFIG_DIR = Path.home() / ".zhuiyi"
CONFIG_FILE = CONFIG_DIR / "config.json"

# 支持的API服务商
PROVIDERS = {
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-v4-pro",
        "env_key": "DEEPSEEK_API_KEY",
        "description": "便宜且中文效果好，推荐日常使用",
    },
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
        "description": "效果最好，价格较高",
    },
    "qwen": {
        "name": "通义千问",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-turbo",
        "env_key": "QWEN_API_KEY",
        "description": "阿里云服务，稳定可靠",
    },
    "zhipu": {
        "name": "智谱GLM",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "default_model": "glm-4-flash",
        "env_key": "ZHIPU_API_KEY",
        "description": "中文优化，国产大模型",
    },
    "kimi": {
        "name": "Kimi",
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-8k",
        "env_key": "KIMI_API_KEY",
        "description": "长文本支持，适合长对话",
    },
    "mimo": {
        "name": "MiMo",
        "base_url": "https://token-plan-cn.xiaomimimo.com/v1",
        "default_model": "mimo-v2.5-pro",
        "env_key": "MIMO_API_KEY",
        "description": "小米MiMo AI服务，支持对话、TTS、声音克隆",
    },
}


class ConfigService:
    """配置服务"""

    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """加载配置"""
        # 确保配置目录存在
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # 从文件加载
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._config = {}

        # 从环境变量补充
        for provider_key, provider_info in PROVIDERS.items():
            env_key = provider_info["env_key"]
            env_value = os.getenv(env_key)
            if env_value and provider_key not in self._config.get("providers", {}):
                if "providers" not in self._config:
                    self._config["providers"] = {}
                self._config["providers"][provider_key] = {
                    "api_key": env_value,
                    "base_url": provider_info["base_url"],
                    "model": provider_info["default_model"],
                }

        # 设置默认值
        if "default_provider" not in self._config:
            self._config["default_provider"] = os.getenv("DEFAULT_PROVIDER", "deepseek")
        if "default_model" not in self._config:
            self._config["default_model"] = os.getenv("DEFAULT_MODEL", "deepseek-chat")

    def _save_config(self):
        """保存配置到文件"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)

    def get_provider_config(self, provider_name: Optional[str] = None) -> Optional[Dict]:
        """获取指定服务商的配置"""
        if provider_name is None:
            provider_name = self._config.get("default_provider", "deepseek")

        providers = self._config.get("providers", {})
        return providers.get(provider_name)

    def get_available_providers(self) -> list:
        """获取已配置API密钥的服务商列表"""
        providers = self._config.get("providers", {})
        available = []
        for key, info in PROVIDERS.items():
            if key in providers and providers[key].get("api_key"):
                available.append({
                    "key": key,
                    "name": info["name"],
                    "model": providers[key].get("model", info["default_model"]),
                    "description": info["description"],
                })
        return available

    def get_all_providers(self) -> list:
        """获取所有服务商信息（包括未配置的）"""
        providers = self._config.get("providers", {})
        result = []
        for key, info in PROVIDERS.items():
            config = providers.get(key, {})
            result.append({
                "key": key,
                "name": info["name"],
                "base_url": info["base_url"],
                "default_model": info["default_model"],
                "description": info["description"],
                "configured": bool(config.get("api_key")),
                "model": config.get("model", info["default_model"]),
            })
        return result

    def update_provider(self, provider_name: str, config: Dict):
        """更新服务商配置"""
        if "providers" not in self._config:
            self._config["providers"] = {}
        self._config["providers"][provider_name] = config
        self._save_config()

    def get_app_config(self) -> Dict:
        """获取应用配置"""
        return {
            "default_provider": self._config.get("default_provider", "deepseek"),
            "default_model": self._config.get("default_model", "deepseek-chat"),
        }

    def update_app_config(self, config: Dict):
        """更新应用配置"""
        self._config.update(config)
        self._save_config()
