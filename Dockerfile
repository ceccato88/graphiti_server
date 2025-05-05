# ---------- Stage 1: Builder ----------
FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y gcc git

# Clonar repositório e extrair apenas o requirements.txt
RUN git clone --depth=1 --filter=blob:none --sparse https://github.com/ceccato88/graphiti_server.git && \
    cd graphiti_server && \
    git sparse-checkout set requirements.txt && \
    mv requirements.txt ../ && \
    cd .. && rm -rf graphiti_server

# Instalar dependências
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# ---------- Stage 2: Final ----------
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl git && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

# Clonar apenas os arquivos da pasta graph_service
RUN git clone --depth=1 --filter=blob:none --sparse https://github.com/ceccato88/graphiti_server.git && \
    cd graphiti_server && \
    git sparse-checkout set graph_service && \
    mv graph_service/* ../app && \
    cd .. && rm -rf graphiti_server

# Criar usuário sem privilégios
RUN adduser --disabled-password --gecos '' apiuser \
    && chown -R apiuser /app
USER apiuser

EXPOSE 8081

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=5 \
  CMD curl -f http://localhost:8081/healthcheck || exit 1

CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8081", "-w", "5"]
