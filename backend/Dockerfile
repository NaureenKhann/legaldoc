FROM python:3.11-slim

WORKDIR /app

# Security: run as non-root
RUN useradd --create-home --shell /bin/bash appuser

# System dependencies for PyMuPDF
RUN apt-get update && apt-get install -y \
    libmupdf-dev \
    mupdf-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Create storage directories
RUN mkdir -p storage/uploads storage/generated \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
