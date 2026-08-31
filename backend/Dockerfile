FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

# docker run -p 8000:8000 personal-ai-backend
# docker ps //Shows running containers
# docker logs <container-id> //shows app log
# docker stop <container-id> //stop the container