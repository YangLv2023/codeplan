import os
import json
import time
import uuid
from typing import List, Optional, Dict, Any, Iterator
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
import requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Infini-AI Proxy API", version="1.0.0")

INFINI_AI_BASE_URL = os.getenv("INFINI_AI_BASE_URL", "https://cloud.infini-ai.com")
INFINI_AI_COOKIE = os.getenv("INFINI_AI_COOKIE", "")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "glm-5.1")


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = DEFAULT_MODEL
    messages: List[Message]
    stream: bool = False
    max_tokens: Optional[int] = 65536
    temperature: Optional[float] = 0.6
    top_k: Optional[int] = 50
    top_p: Optional[float] = 0.7
    frequency_penalty: Optional[float] = 0
    presence_penalty: Optional[float] = 0


class AnthropicMessage(BaseModel):
    role: str
    content: str


class AnthropicRequest(BaseModel):
    model: str = DEFAULT_MODEL
    messages: List[AnthropicMessage]
    max_tokens: int = 1024
    stream: bool = False
    temperature: Optional[float] = 0.6
    top_k: Optional[int] = 50
    top_p: Optional[float] = 0.7


class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int = Field(default_factory=lambda: int(time.time()))
    owned_by: str = "infini-ai"


def get_headers():
    return {
        "accept": "text/event-stream",
        "accept-language": "zh-CN,zh;q=0.9",
        "content-type": "application/json",
        "origin": INFINI_AI_BASE_URL,
        "referer": f"{INFINI_AI_BASE_URL}/genstudio/experience",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
        "cookie": INFINI_AI_COOKIE
    }


def stream_response(response: requests.Response) -> Iterator[str]:
    for line in response.iter_lines():
        if line:
            yield f"{line.decode('utf-8')}\n"


@app.get("/")
async def root():
    return {"message": "Infini-AI Proxy API is running", "version": "1.0.0"}


@app.get("/coding/v1/models")
@app.get("/coding/v1/models/")
async def list_models_openai():
    models = [
        ModelInfo(id="glm-5.1"),
        ModelInfo(id="glm-4"),
        ModelInfo(id="deepseek-chat"),
        ModelInfo(id="deepseek-coder"),
    ]
    return {"object": "list", "data": [model.dict() for model in models]}


@app.get("/coding/v1/models/{model_id}")
async def get_model_openai(model_id: str):
    model = ModelInfo(id=model_id)
    return model.dict()


@app.post("/coding/v1/chat/completions")
@app.post("/coding/v1/chat/completions/")
async def chat_completions_openai(request: ChatCompletionRequest):
    url = f"{INFINI_AI_BASE_URL}/maas/{request.model}/nvidia/chat/completions"
    
    payload = {
        "model": request.model,
        "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
        "stream": request.stream,
        "max_tokens": request.max_tokens,
        "temperature": request.temperature,
        "top_k": request.top_k,
        "top_p": request.top_p,
        "frequency_penalty": request.frequency_penalty,
        "presence_penalty": request.presence_penalty
    }
    
    try:
        if request.stream:
            response = requests.post(url, headers=get_headers(), json=payload, stream=True, timeout=120.0)
            response.raise_for_status()
            return StreamingResponse(
                stream_response(response),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            response = requests.post(url, headers=get_headers(), json=payload, timeout=120.0)
            response.raise_for_status()
            return JSONResponse(content=response.json())
    except requests.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Upstream API error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.get("/coding/v1/models")
async def list_models_anthropic():
    models = [
        ModelInfo(id="glm-5.1"),
        ModelInfo(id="glm-4"),
        ModelInfo(id="deepseek-chat"),
        ModelInfo(id="deepseek-coder"),
    ]
    return {"object": "list", "data": [model.dict() for model in models]}


@app.post("/coding/v1/messages")
async def messages_anthropic(request: AnthropicRequest):
    url = f"{INFINI_AI_BASE_URL}/maas/{request.model}/nvidia/chat/completions"
    
    payload = {
        "model": request.model,
        "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
        "stream": request.stream,
        "max_tokens": request.max_tokens,
        "temperature": request.temperature,
        "top_k": request.top_k,
        "top_p": request.top_p
    }
    
    try:
        if request.stream:
            response = requests.post(url, headers=get_headers(), json=payload, stream=True, timeout=120.0)
            response.raise_for_status()
            
            def anthropic_stream():
                for line in response.iter_lines():
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        data_str = line_str[6:]
                        if data_str == "[DONE]":
                            yield f"event: message_stop\ndata: {{}}\n\n"
                            break
                        try:
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    anthropic_event = {
                                        "type": "content_block_delta",
                                        "index": 0,
                                        "delta": {"type": "text_delta", "text": content}
                                    }
                                    yield f"event: content_block_delta\ndata: {json.dumps(anthropic_event)}\n\n"
                        except json.JSONDecodeError:
                            continue
            
            return StreamingResponse(
                anthropic_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        else:
            response = requests.post(url, headers=get_headers(), json=payload, timeout=120.0)
            response.raise_for_status()
            
            openai_response = response.json()
            
            if "choices" in openai_response and len(openai_response["choices"]) > 0:
                message = openai_response["choices"][0].get("message", {})
                anthropic_response = {
                    "id": f"msg_{uuid.uuid4().hex[:24]}",
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": message.get("content", "")
                        }
                    ],
                    "model": request.model,
                    "stop_reason": "end_turn",
                    "usage": openai_response.get("usage", {})
                }
                return JSONResponse(content=anthropic_response)
            else:
                raise HTTPException(status_code=500, detail="Invalid response from upstream API")
                
    except requests.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Upstream API error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("API_HOST", "0.0.0.0"), port=int(os.getenv("API_PORT", "8000")))
