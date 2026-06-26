# Sử dụng Python 3.10 vì đây là phiên bản ổn định nhất cho selfcord.py
FROM python:3.10-slim

# Cài đặt các thư viện hệ thống cần thiết để biên dịch code C
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Nâng cấp pip và cài đặt setuptools trước để tránh lỗi metadata
RUN pip install --upgrade pip setuptools wheel

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "main.py"]
