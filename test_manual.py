import requests
import json

BASE_URL = "http://localhost:8000"
API_KEY = "infini-ai-proxy-2024-secure-key-x7k9m2p4"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

def test_openai_chat():
    print("测试OpenAI协议聊天接口...")
    url = f"{BASE_URL}/coding/v1/chat/completions"
    payload = {
        "model": "glm-5.1",
        "messages": [{"role": "user", "content": "你好，请用一句话介绍自己"}],
        "stream": False
    }
    
    response = requests.post(url, json=payload, headers=HEADERS)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
    else:
        print(f"错误: {response.text}")
    print()

def test_openai_stream():
    print("测试OpenAI协议流式接口...")
    url = f"{BASE_URL}/coding/v1/chat/completions"
    payload = {
        "model": "glm-5.1",
        "messages": [{"role": "user", "content": "你好"}],
        "stream": True
    }
    
    response = requests.post(url, json=payload, stream=True, headers=HEADERS)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        print("流式响应:")
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith("data: "):
                    data_str = line_str[6:]
                    if data_str != "[DONE]":
                        try:
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    print(content, end="", flush=True)
                        except json.JSONDecodeError:
                            pass
        print("\n")
    else:
        print(f"错误: {response.text}")
    print()

def test_anthropic_chat():
    print("测试Anthropic协议消息接口...")
    url = f"{BASE_URL}/coding/v1/messages"
    payload = {
        "model": "glm-5.1",
        "messages": [{"role": "user", "content": "你好，请用一句话介绍自己"}],
        "max_tokens": 1024,
        "stream": False
    }
    
    response = requests.post(url, json=payload, headers=HEADERS)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
    else:
        print(f"错误: {response.text}")
    print()

def test_models():
    print("测试模型列表接口...")
    url = f"{BASE_URL}/coding/v1/models"
    
    response = requests.get(url, headers=HEADERS)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")
    else:
        print(f"错误: {response.text}")
    print()

if __name__ == "__main__":
    print("=" * 60)
    print("Infini-AI Proxy API 测试")
    print("=" * 60)
    print()
    
    test_models()
    test_openai_chat()
    test_openai_stream()
    test_anthropic_chat()
    
    print("=" * 60)
    print("测试完成")
    print("=" * 60)
