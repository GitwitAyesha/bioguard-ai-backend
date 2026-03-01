FROM python:3.9-slim

# Install system dependencies needed for dlib/face_recognition
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install cmake && \
    pip install dlib==19.22.99 && \
    pip install -r requirements.txt

# Copy rest of the app
COPY . .

EXPOSE 8000

CMD ["python", "app.py"]