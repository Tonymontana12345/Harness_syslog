FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY mcp_servers/requirements.txt /tmp/mcp-requirements.txt
COPY rag/requirements.txt /tmp/rag-requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /tmp/mcp-requirements.txt -r /tmp/rag-requirements.txt

COPY mcp_servers/ ./mcp_servers/
COPY rag/ ./rag/
COPY data/DB/ ./data/DB/
COPY data/Log/ ./data/Log/

RUN mkdir -p data/Manual data/Store/chroma output Token

CMD ["python", "mcp_servers/log_db_server.py"]
