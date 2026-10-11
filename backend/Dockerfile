FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir 'torch==2.14.1+cpu' \
        --index-url https://download.pytorch.org/whl/cpu \
        --extra-index-url https://pypi.org/simple \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home atlas && chown -R atlas:atlas /app

RUN mkdir -p /app/storage /home/atlas/.cache/huggingface \
    && chown -R atlas:atlas /app/storage /home/atlas

USER atlas

EXPOSE 8000

CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--no-access-log"]
