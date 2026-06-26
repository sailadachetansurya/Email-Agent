FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm

COPY . .

ENV LLM_ENDPOINT=http://host.docker.internal:8080/chat/completions

ENTRYPOINT ["python", "tui.py"]
