FROM python:3.8.10-slim
WORKDIR /app

COPY . /app
RUN pip install -r /app/requirement.txt
CMD ["uvicorn", "main:app", "--reload", "--port", "8000", "--host", "0.0.0.0"]