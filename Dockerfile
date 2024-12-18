FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install watchdog[watchmedo]

# Copy the application code
COPY . .

# Create script to generate .env file
RUN echo '#!/bin/sh\n\
echo "TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN" > .env\n\
echo "CHROMA_SERVER_HOST=chromadb" >> .env\n\
echo "CHROMA_SERVER_PORT=8000" >> .env\n\
echo "OLLAMA_BASE_URL=http://ollama:11434" >> .env\n\
exec "$@"' > /app/docker-entrypoint.sh \
&& chmod +x /app/docker-entrypoint.sh

# Set the entrypoint to our script
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Command to run the application with watchdog
CMD ["watchmedo", "auto-restart", "--directory=./", "--pattern=*.py", "--recursive", "--", "python", "telegram_bot.py"]
