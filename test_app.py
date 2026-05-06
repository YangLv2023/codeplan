import pytest
import httpx
import asyncio
import json
from app import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_root():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["message"] == "Infini-AI Proxy API is running"


def test_list_models_openai():
    """测试OpenAI协议的模型列表接口"""
    response = client.get("/coding/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert "object" in data
    assert data["object"] == "list"
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0


def test_get_model_openai():
    """测试OpenAI协议的单个模型查询接口"""
    response = client.get("/coding/v1/models/glm-5.1")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["id"] == "glm-5.1"
    assert "object" in data
    assert data["object"] == "model"


def test_chat_completions_openai_non_stream():
    """测试OpenAI协议的非流式聊天接口"""
    payload = {
        "model": "glm-5.1",
        "messages": [
            {"role": "user", "content": "你好"}
        ],
        "stream": False,
        "max_tokens": 100,
        "temperature": 0.6
    }
    
    response = client.post("/coding/v1/chat/completions", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "choices" in data
    assert len(data["choices"]) > 0
    assert "message" in data["choices"][0]


def test_chat_completions_openai_stream():
    """测试OpenAI协议的流式聊天接口"""
    payload = {
        "model": "glm-5.1",
        "messages": [
            {"role": "user", "content": "你好"}
        ],
        "stream": True,
        "max_tokens": 100,
        "temperature": 0.6
    }
    
    response = client.post("/coding/v1/chat/completions", json=payload)
    assert response.status_code == 200
    
    content_received = False
    for line in response.iter_lines():
        if line:
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str != "[DONE]":
                    try:
                        data = json.loads(data_str)
                        if "choices" in data and len(data["choices"]) > 0:
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta and delta["content"]:
                                content_received = True
                                break
                    except json.JSONDecodeError:
                        continue
    
    assert content_received, "No content received in stream"


def test_messages_anthropic_non_stream():
    """测试Anthropic协议的非流式消息接口"""
    payload = {
        "model": "glm-5.1",
        "messages": [
            {"role": "user", "content": "你好"}
        ],
        "max_tokens": 100,
        "stream": False,
        "temperature": 0.6
    }
    
    response = client.post("/coding/v1/messages", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "type" in data
    assert data["type"] == "message"
    assert "content" in data
    assert isinstance(data["content"], list)
    assert len(data["content"]) > 0


def test_messages_anthropic_stream():
    """测试Anthropic协议的流式消息接口"""
    payload = {
        "model": "glm-5.1",
        "messages": [
            {"role": "user", "content": "你好"}
        ],
        "max_tokens": 100,
        "stream": True,
        "temperature": 0.6
    }
    
    response = client.post("/coding/v1/messages", json=payload)
    assert response.status_code == 200
    
    content_received = False
    lines_received = []
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8') if isinstance(line, bytes) else line
            lines_received.append(line_str)
            if line_str.startswith("event: "):
                event_type = line_str[7:]
                if event_type == "content_block_delta":
                    content_received = True
                    break
    
    if not content_received:
        print(f"Lines received: {lines_received}")
    
    assert content_received, f"No content received in stream. Lines: {lines_received}"


def test_invalid_model():
    """测试无效模型"""
    payload = {
        "model": "invalid-model",
        "messages": [
            {"role": "user", "content": "你好"}
        ],
        "stream": False,
        "max_tokens": 100
    }
    
    response = client.post("/coding/v1/chat/completions", json=payload)
    assert response.status_code in [400, 404, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
