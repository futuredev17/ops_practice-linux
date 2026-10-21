# 1. Base environment: Use the official lightweight Python 3.11 image
FROM python:3.11-slim

# 2. Set working directory: Create a folder inside the container and switch to it
WORKDIR /app

# 3. Copy all files from the host's current directory to the container's /app directory
COPY . /app

# 4. Default command executed when the container starts
ENTRYPOINT ["python3", "local_port_check.py"]