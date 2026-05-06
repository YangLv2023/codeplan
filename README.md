# Infini-AI Proxy API

这是一个逆向代理服务，将无问芯穹（Infini-AI）的API转换为标准的OpenAI和Anthropic协议接口。

## 功能特性

- ✅ 支持OpenAI兼容协议
  - `/coding/v1/chat/completions` - 聊天补全接口
  - `/coding/v1/models` - 模型列表接口
  
- ✅ 支持Anthropic协议
  - `/coding/v1/messages` - 消息接口
  - `/coding/v1/models` - 模型列表接口

- ✅ 支持流式和非流式响应
- ✅ 支持Docker容器化部署
- ✅ 支持API Key认证保护

## 快速开始

### 本地运行

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 配置环境变量：
复制 `.env.example` 为 `.env`，并修改其中的配置：
```bash
cp .env.example .env
```

3. 启动服务：
```bash
python app.py
```

服务将在 `http://localhost:8000` 启动。

### Docker部署

1. 构建镜像：
```bash
docker build -t infini-ai-proxy .
```

2. 运行容器：
```bash
docker run -d -p 8000:8000 --name infini-ai-proxy infini-ai-proxy
```

或者使用环境变量覆盖：
```bash
docker run -d -p 8000:8000 \
  -e INFINI_AI_COOKIE="your_cookie_here" \
  --name infini-ai-proxy \
  infini-ai-proxy
```

## API使用示例

**重要：所有API请求都需要在请求头中包含API Key进行认证。**

默认API Key: `infini-ai-proxy-2024-secure-key-x7k9m2p4`

认证方式（任选其一）：
1. 在请求头中添加: `Authorization: Bearer YOUR_API_KEY`
2. 在URL参数中添加: `?api_key=YOUR_API_KEY`

### OpenAI协议示例

#### 非流式请求
```bash
curl -X POST http://localhost:8000/coding/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer infini-ai-proxy-2024-secure-key-x7k9m2p4" \
  -d '{
    "model": "glm-5.1",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": false
  }'
```

#### 流式请求
```bash
curl -X POST http://localhost:8000/coding/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer infini-ai-proxy-2024-secure-key-x7k9m2p4" \
  -d '{
    "model": "glm-5.1",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": true
  }'
```

### Anthropic协议示例

#### 非流式请求
```bash
curl -X POST http://localhost:8000/coding/v1/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer infini-ai-proxy-2024-secure-key-x7k9m2p4" \
  -d '{
    "model": "glm-5.1",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 1024,
    "stream": false
  }'
```

#### 流式请求
```bash
curl -X POST http://localhost:8000/coding/v1/messages \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer infini-ai-proxy-2024-secure-key-x7k9m2p4" \
  -d '{
    "model": "glm-5.1",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 1024,
    "stream": true
  }'
```

## 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| INFINI_AI_BASE_URL | Infini-AI API基础URL | https://cloud.infini-ai.com |
| INFINI_AI_COOKIE | 认证Cookie | - |
| DEFAULT_MODEL | 默认模型 | glm-5.1 |
| API_HOST | API服务监听地址 | 0.0.0.0 |
| API_PORT | API服务监听端口 | 8000 |
| API_KEY | API认证密钥 | infini-ai-proxy-2024-secure-key-x7k9m2p4 |

## 测试

运行测试用例：
```bash
python -m pytest test_app.py -v
```

## 注意事项

1. Cookie认证信息可能会过期，需要定期更新
2. 建议在生产环境中使用HTTPS
3. 建议添加API密钥认证层以保护服务

## 许可证

MIT License
