FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py ./
COPY messages/ ./messages/

# The Vercel daemon invokes this command; no HTTP app or port is required.
CMD ["python", "-u", "main.py"]
