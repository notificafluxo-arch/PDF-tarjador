# Use imagem oficial Python
FROM python:3.11-slim

# Configura diretório de trabalho
WORKDIR /app

# Copia arquivos necessários
COPY app.py requirements.txt ./

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expõe porta do Flask
EXPOSE 8080

# Comando de inicialização para Railway
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
