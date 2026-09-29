FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements-lock.txt ./
RUN pip install --no-cache-dir -r requirements-lock.txt
COPY . .
# The container defaults to a clearly labeled software fixture, not private data.
RUN python scripts/create_test_dataset.py && useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 5000
CMD ["python", "-m", "flask", "--app", "health_friend.web", "run", "--host", "0.0.0.0", "--port", "5000"]
