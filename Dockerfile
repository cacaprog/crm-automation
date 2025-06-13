# Use uma imagem Python oficial e leve como base.
# Usar uma tag específica (ex: 3.9) garante builds consistentes.
FROM python:3.9-slim-buster

# Define o diretório de trabalho dentro do contêiner.
WORKDIR /app

# Define variáveis de ambiente para Python.
# PYTHONDONTWRITEBYTECODE: Impede o Python de criar arquivos .pyc.
# PYTHONUNBUFFERED: Garante que os logs sejam enviados diretamente para o terminal.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copia o arquivo de dependências para o contêiner.
COPY requirements.txt .

# Instala as dependências do projeto.
# --no-cache-dir: Desativa o cache do pip para manter a imagem menor.
# --upgrade pip: Garante que estamos usando a versão mais recente do pip.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia todo o código da aplicação para o diretório de trabalho.
COPY . .

# Comando para executar a aplicação usando Gunicorn, um servidor WSGI de produção.
# O Cloud Run define a variável de ambiente $PORT automaticamente.
# --workers: Número de processos de trabalho.
# --threads: Número de threads por worker.
# --timeout 0: Desativa o timeout do worker, ideal para tarefas longas como a sua.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
