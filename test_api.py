import requests
import json

url = "https://cloud.infini-ai.com/maas/glm-5.1/nvidia/chat/completions"

headers = {
    "accept": "text/event-stream",
    "accept-language": "zh-CN,zh;q=0.9",
    "content-type": "application/json",
    "origin": "https://cloud.infini-ai.com",
    "referer": "https://cloud.infini-ai.com/genstudio/experience",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "cookie": "UM_distinctid=19d3c45599ac67-0dba07b081f1338-26011051-384000-19d3c45599b10c3; _c_WBKFRo=fQrfFUacYaruuYH42jVx4qX7tIPezw1Rdqhvomef; CZ_UUID1281348319=ac-dcqxr542fasno4bj; _clck=prnb56%5E2%5Eg5n%5E0%5E2280; acw_tc=0893731c17780299740793675e1674df5e0318fb2057423459ba99db4fba9b; INFINI_USERINFO_V1=c4a67df3-658c-40c3-a55d-02a6690e1e07822600265; CNZZDATA1281348319=47746149-1774832671-https%253A%252F%252Fwww.baidu.com%252F%7C1778031353"
}

data = {
    "model": "glm-5.1",
    "messages": [
        {"role": "user", "content": "你好"}
    ],
    "stream": True,
    "max_tokens": 100,
    "temperature": 0.6,
    "top_k": 50,
    "top_p": 0.7,
    "frequency_penalty": 0,
    "presence_penalty": 0
}

try:
    response = requests.post(url, headers=headers, json=data, timeout=60, stream=True)
    print(f"状态码: {response.status_code}")
    print(f"响应头: {response.headers}")
    print("响应内容:")
    for line in response.iter_lines():
        if line:
            print(line.decode('utf-8'))
except Exception as e:
    print(f"请求失败: {e}")
