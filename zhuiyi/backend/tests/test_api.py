"""
API自动化测试
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestHealthEndpoints:
    """健康检查测试"""

    def test_health(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_root(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "name" in response.json()


class TestChatEndpoints:
    """聊天接口测试"""

    def test_empty_messages(self):
        response = client.post("/api/chat/completions", json={
            "messages": [],
            "provider": "mimo",
            "stream": False,
        })
        assert response.status_code == 422

    def test_invalid_provider(self):
        response = client.post("/api/chat/completions", json={
            "messages": [{"role": "user", "content": "test"}],
            "provider": "invalid",
            "stream": False,
        })
        assert response.status_code == 400

    def test_invalid_role(self):
        response = client.post("/api/chat/completions", json={
            "messages": [{"role": "invalid", "content": "test"}],
            "provider": "mimo",
            "stream": False,
        })
        assert response.status_code == 422

    def test_providers(self):
        response = client.get("/api/chat/providers")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestDataImportEndpoints:
    """数据导入测试"""

    def test_empty_content(self):
        response = client.post("/api/data/import/text", data={
            "content": "",
            "character_name": "test",
            "file_type": "txt",
        })
        assert response.status_code == 422

    def test_characters_list(self):
        response = client.get("/api/data/characters")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_delete_nonexistent(self):
        response = client.delete("/api/data/characters/non_existent")
        assert response.status_code == 404

    def test_get_nonexistent(self):
        response = client.get("/api/data/characters/non_existent")
        assert response.status_code == 404


class TestConfigEndpoints:
    """配置接口测试"""

    def test_providers(self):
        response = client.get("/api/config/providers")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_app_config(self):
        response = client.get("/api/config/app")
        assert response.status_code == 200
        assert "default_provider" in response.json()


class TestAvatarEndpoints:
    """数字人接口测试"""

    def test_expressions(self):
        response = client.get("/api/avatar/expressions")
        assert response.status_code == 200
        assert "expressions" in response.json()


class TestTTSEndpoints:
    """TTS接口测试"""

    def test_models(self):
        response = client.get("/api/tts/models")
        assert response.status_code == 200
        assert "models" in response.json()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
