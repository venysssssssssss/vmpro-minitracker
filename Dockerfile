# Multi-stage build para otimizar tamanho da imagem
FROM python:3.12-slim as builder

# Definir diretório de trabalho
WORKDIR /app

# Instalar Poetry
RUN pip install poetry

# Copiar arquivos de dependências
COPY pyproject.toml poetry.lock ./

# Configurar Poetry para não criar ambiente virtual
RUN poetry config virtualenvs.create false

# Instalar dependências
RUN poetry install --no-dev --no-interaction --no-ansi

# Estágio final
FROM python:3.12-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root
RUN useradd --create-home --shell /bin/bash app

# Definir diretório de trabalho
WORKDIR /app

# Copiar dependências Python do estágio anterior
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar código da aplicação
COPY . .

# Mudar proprietário dos arquivos para o usuário app
RUN chown -R app:app /app

# Mudar para usuário não-root
USER app

# Expor porta
EXPOSE 8000

# Comando padrão
CMD ["python", "-m", "uvicorn", "modern_fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"]
