# ---------- Stage 1: Builder ----------
FROM python:3.11-slim AS builder

WORKDIR /app

# Boas práticas Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instalar dependências necessárias para build
RUN apt-get update && apt-get install -y gcc

# Copiar e instalar dependências na pasta /install
COPY app/requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt


# ---------- Stage 2: Final ----------
FROM python:3.11-slim

WORKDIR /app

# Reaplicando boas práticas
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instalar curl para o healthcheck
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Instalar dependências do build anterior
COPY --from=builder /install /usr/local

# Copiar código
COPY app .

# Criar usuário sem privilégios
RUN adduser --disabled-password --gecos '' apiuser \
    && chown -R apiuser /app
USER apiuser

# Expor porta usada
EXPOSE 8000

# Healthcheck configurado
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=5 \
  CMD curl -f http://localhost:8000/healthcheck || exit 1

# Comando de execução com Gunicorn + UvicornWorker
CMD ["gunicorn", "graph_service.main:app", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "-w", "5"]
