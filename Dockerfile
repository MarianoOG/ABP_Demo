# Set up
FROM python:3.10-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip --no-cache-dir && \
    pip install -r requirements.txt --no-cache-dir

# Update code
COPY main.py /app/main.py

# Entrypoint
EXPOSE 8080
ENTRYPOINT ["streamlit", "run", "main.py", "--server.port", "8080"]
