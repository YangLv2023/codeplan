import os
import json
import time
import uuid
import sys
import traceback
from datetime import datetime
from typing import List, Optional, Dict, Any, Iterator, Union
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import requests
from dotenv import load_dotenv

load_dotenv()

DEBUG = os.getenv("DEBUG", "false").lower() == "true"

def safe_print(message: str, file=None):
    try:
        if file is None:
            file = sys.stdout
        if hasattr(file, 'buffer'):
            file.buffer.write((message + "\n").encode('utf-8'))
            file.buffer.flush()
        else:
            print(message, file=file)
    except Exception:
        pass

def log(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    formatted_message = f"[{timestamp}] [{level}] {message}"
    safe_print(formatted_message, file=sys.stderr if level == "ERROR" else sys.stdout)

def log_error(message: str, exception: Exception = None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    error_msg = f"[{timestamp}] [ERROR] {message}"
    safe_print(error_msg, file=sys.stderr)
    if exception:
        try:
            traceback.print_exc()
        except Exception:
            pass

def log_debug(message: str):
    if DEBUG:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted_message = f"[{timestamp}] [DEBUG] {message}"
        safe_print(formatted_message)

app = FastAPI(title="Infini-AI Proxy API", version="1.0.0")

INFINI_AI_BASE_URL = os.getenv("INFINI_AI_BASE_URL", "https://cloud.infini-ai.com")
INFINI_AI_COOKIE = os.getenv("INFINI_AI_COOKIE", "")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "glm-5.1")
API_KEY = os.getenv("API_KEY", "infini-ai-proxy-2024-secure-key-x7k9m2p4")

log(f"Starting Infini-AI Proxy API v1.0.0")
log(f"DEBUG mode: {DEBUG}")
log(f"API Key configured: {'Yes' if API_KEY else 'No'}")

security = HTTPBearer(auto_error=False)


async def verify_api_key(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        api_key = None
        
        if credentials:
            api_key = credentials.credentials
        elif "api_key" in request.query_params:
            api_key = request.query_params["api_key"]
        elif "apikey" in request.query_params:
            api_key = request.query_params["apikey"]
        elif "authorization" in request.headers:
            auth_header = request.headers["authorization"]
            if auth_header.startswith("Bearer "):
                api_key = auth_header[7:]
        
        if not api_key or api_key != API_KEY:
            log(f"API key validation failed - IP: {request.client.host if request.client else 'unknown'}")
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key. Please provide a valid API key in the Authorization header or as a query parameter."
            )
        
        log_debug(f"API key validated successfully")
        return api_key
    except HTTPException:
        raise
    except Exception as e:
        log_error("Error in API key verification", e)
        raise HTTPException(status_code=500, detail="Internal server error during authentication")


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = DEFAULT_MODEL
    messages: List[Message]
    stream: bool = False
    max_tokens: Optional[int] = 8192
    temperature: Optional[float] = 0.4
    top_p: Optional[float] = 0.9
    top_k: Optional[int] = 0
    frequency_penalty: Optional[float] = 0
    presence_penalty: Optional[float] = 0


class AnthropicMessage(BaseModel):
    role: str
    content: Union[str, List[Dict[str, Any]]]


class AnthropicRequest(BaseModel):
    model: str = DEFAULT_MODEL
    messages: List[AnthropicMessage]
    max_tokens: int = 4096
    stream: bool = False
    temperature: Optional[float] = 0.4
    top_p: Optional[float] = 0.9
    top_k: Optional[int] = 0
    tools: Optional[List[Dict[str, Any]]] = None
    system: Optional[Union[str, List[Dict[str, Any]]]] = None


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


@app.post("/debug/inspect/v1/messages")
async def debug_inspect(request: Request, api_key: str = Depends(verify_api_key)):
    body = await request.json()
    
    import sys
    import io
    
    output = io.StringIO()
    output.write("=" * 80 + "\n")
    output.write("DEBUG: Received request\n")
    output.write("=" * 80 + "\n")
    output.write(f"Method: {request.method}\n")
    output.write(f"URL: {request.url}\n")
    output.write(f"Query Params: {dict(request.query_params)}\n")
    output.write(f"Body: {json.dumps(body, ensure_ascii=False, indent=2)}\n")
    output.write("=" * 80 + "\n")
    
    print(output.getvalue(), file=sys.stderr)
    
    return {
        "method": request.method,
        "url": str(request.url),
        "query_params": dict(request.query_params),
        "body": body
    }


@app.get("/coding/v1/models")
@app.get("/coding/v1/models/")
async def list_models_openai(api_key: str = Depends(verify_api_key)):
    models = [
        ModelInfo(id="glm-5.1"),
        ModelInfo(id="glm-4"),
        ModelInfo(id="deepseek-chat"),
        ModelInfo(id="deepseek-coder"),
    ]
    return {"object": "list", "data": [model.dict() for model in models]}


@app.get("/coding/v1/models/{model_id}")
async def get_model_openai(model_id: str, api_key: str = Depends(verify_api_key)):
    model = ModelInfo(id=model_id)
    return model.dict()


@app.post("/coding/v1/chat/completions")
@app.post("/coding/v1/chat/completions/")
async def chat_completions_openai(request: ChatCompletionRequest, api_key: str = Depends(verify_api_key)):
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


@app.post("/coding/v1/messages")
async def messages_anthropic(request: AnthropicRequest, api_key: str = Depends(verify_api_key)):
    request_id = str(uuid.uuid4())[:8]
    log(f"[{request_id}] Received Anthropic request - Model: {request.model}, Stream: {request.stream}")
    
    log_debug(f"[{request_id}] Request details: {json.dumps(request.dict(), ensure_ascii=False, indent=2)}")
    
    try:
        url = f"{INFINI_AI_BASE_URL}/maas/{request.model}/nvidia/chat/completions"
        
        messages = []
        for msg in request.messages:
            if isinstance(msg.content, str):
                messages.append({"role": msg.role, "content": msg.content})
            elif isinstance(msg.content, list):
                text_parts = []
                tool_uses = []
                tool_results = []
                
                for item in msg.content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            text_parts.append(item.get("text", ""))
                        elif item.get("type") == "tool_use":
                            tool_uses.append({
                                "id": item.get("id", ""),
                                "type": "function",
                                "function": {
                                    "name": item.get("name", ""),
                                    "arguments": json.dumps(item.get("input", {}))
                                }
                            })
                        elif item.get("type") == "tool_result":
                            tool_results.append({
                                "tool_call_id": item.get("tool_use_id", ""),
                                "role": "tool",
                                "content": item.get("content", "")
                            })
                
                if tool_uses and msg.role == "assistant":
                    message_obj = {"role": msg.role}
                    if text_parts:
                        message_obj["content"] = "\n".join(text_parts)
                    message_obj["tool_calls"] = tool_uses
                    messages.append(message_obj)
                elif tool_results:
                    messages.extend(tool_results)
                    if text_parts:
                        messages.append({"role": msg.role, "content": "\n".join(text_parts)})
                else:
                    content = "\n".join(text_parts)
                    if content:
                        messages.append({"role": msg.role, "content": content})
            else:
                messages.append({"role": msg.role, "content": str(msg.content)})
        
        payload = {
            "model": request.model,
            "messages": messages,
            "stream": request.stream,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_k": request.top_k,
            "top_p": request.top_p
        }
        
        if request.tools:
            openai_tools = []
            for tool in request.tools:
                if tool.get("type") == "function" or "function" in tool:
                    openai_tools.append(tool)
                else:
                    openai_tools.append({
                        "type": "function",
                        "function": {
                            "name": tool.get("name", ""),
                            "description": tool.get("description", ""),
                            "parameters": tool.get("input_schema", {})
                        }
                    })
            payload["tools"] = openai_tools
            log_debug(f"[{request_id}] Tools configured: {len(openai_tools)} tools")
        
        if request.system:
            system_content = ""
            if isinstance(request.system, str):
                system_content = request.system
            elif isinstance(request.system, list):
                text_parts = []
                for item in request.system:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                system_content = "\n".join(text_parts)
            
            if system_content:
                if messages and messages[0].get("role") == "system":
                    messages[0]["content"] = system_content
                else:
                    messages.insert(0, {"role": "system", "content": system_content})
        
        log_debug(f"[{request_id}] Forwarding to upstream API: {url}")
        log_debug(f"[{request_id}] Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        if request.stream:
            log(f"[{request_id}] Processing streaming request")
            response = requests.post(url, headers=get_headers(), json=payload, stream=True, timeout=120.0)
            response.raise_for_status()
            
            def anthropic_stream():
                try:
                    for line in response.iter_lines():
                        line_str = line.decode('utf-8')
                        if line_str.startswith("data: "):
                            data_str = line_str[6:]
                            if data_str == "[DONE]":
                                log_debug(f"[{request_id}] Stream completed")
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
                except Exception as e:
                    log_error(f"[{request_id}] Error in streaming response", e)
                    raise
            
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
            log(f"[{request_id}] Processing non-streaming request")
            response = requests.post(url, headers=get_headers(), json=payload, timeout=120.0)
            response.raise_for_status()
            
            openai_response = response.json()
            log_debug(f"[{request_id}] Upstream response: {json.dumps(openai_response, ensure_ascii=False, indent=2)}")
            
            if "choices" in openai_response and len(openai_response["choices"]) > 0:
                message = openai_response["choices"][0].get("message", {})
                
                content_blocks = []
                
                if message.get("content"):
                    content_blocks.append({
                        "type": "text",
                        "text": message.get("content", "")
                    })
                
                tool_calls = message.get("tool_calls", [])
                if tool_calls:
                    log_debug(f"[{request_id}] Found {len(tool_calls)} tool calls")
                    for tool_call in tool_calls:
                        if tool_call.get("type") == "function":
                            function = tool_call.get("function", {})
                            try:
                                arguments = json.loads(function.get("arguments", "{}"))
                            except json.JSONDecodeError:
                                arguments = {}
                            
                            content_blocks.append({
                                "type": "tool_use",
                                "id": tool_call.get("id", f"toolu_{uuid.uuid4().hex[:24]}"),
                                "name": function.get("name", ""),
                                "input": arguments
                            })
                
                stop_reason = "tool_use" if tool_calls else "end_turn"
                
                anthropic_response = {
                    "id": f"msg_{uuid.uuid4().hex[:24]}",
                    "type": "message",
                    "role": "assistant",
                    "content": content_blocks,
                    "model": request.model,
                    "stop_reason": stop_reason,
                    "usage": openai_response.get("usage", {})
                }
                log(f"[{request_id}] Request completed successfully - Stop reason: {stop_reason}")
                log_debug(f"[{request_id}] Response: {json.dumps(anthropic_response, ensure_ascii=False, indent=2)}")
                return JSONResponse(content=anthropic_response)
            else:
                log_error(f"[{request_id}] Invalid response from upstream API")
                raise HTTPException(status_code=500, detail="Invalid response from upstream API")
                
    except requests.HTTPError as e:
        log_error(f"[{request_id}] HTTP error from upstream API", e)
        raise HTTPException(status_code=e.response.status_code, detail=f"Upstream API error: {e.response.text}")
    except Exception as e:
        log_error(f"[{request_id}] Unexpected error", e)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("API_HOST", "0.0.0.0"), port=int(os.getenv("API_PORT", "8000")))
