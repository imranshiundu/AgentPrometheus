FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install crewAI and other orchestration dependencies
RUN pip install --no-cache-dir crewai langchain-openai litellm python-dotenv

# Copy the manager script
COPY . /app

# The workspace will be mounted as a volume
VOLUME ["/app/workspace"]

CMD ["python", "prometheus_manager.py"]
