FROM python:3.13-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev && rm -rf /var/lib/apt/lists/*

# Copy repo source
COPY . .

# Install Hermes from repo source so the Railway crash-loop fix (gateway/run.py early startup) is included
RUN pip install --no-cache-dir .

# Expose the Hermes API server port
EXPOSE 3006

# Start Hermes gateway
CMD ["python", "-m", "hermes_cli.main", "gateway", "run", "--replace"]