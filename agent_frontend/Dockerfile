FROM python:3.14-slim
WORKDIR /app
COPY agent_frontend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY agent_frontend ./agent_frontend
COPY .agents/skills ./.agents/skills
EXPOSE 8000
ENV PYTHONPATH=/app
CMD ["uvicorn", "agent_frontend.app:app", "--host", "0.0.0.0", "--port", "8000"]
