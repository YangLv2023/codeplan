FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

COPY . .

ENV INFINI_AI_BASE_URL=https://cloud.infini-ai.com
ENV INFINI_AI_COOKIES=["cookie1"]
ENV DEFAULT_MODEL=glm-5.1
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV API_KEY=infini-ai-proxy-2024-secure-key-x7k9m2p4
ENV DEBUG=false

EXPOSE 8000

CMD ["python", "app.py"]
