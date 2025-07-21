# Multi-stage build for Python Streamlit app with OCR capabilities
# Stage 1: Build dependencies and compile packages
FROM python:3.11-slim as builder

# Set build arguments for better caching
ARG DEBIAN_FRONTEND=noninteractive

# Install system dependencies needed for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    pkg-config \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies in virtual environment
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime image
FROM python:3.11-slim as runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Set build arguments
ARG DEBIAN_FRONTEND=noninteractive

# Install runtime system dependencies including curl for health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-fra \
    tesseract-ocr-deu \
    tesseract-ocr-spa \
    libtesseract-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgcc-s1 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create application directory
WORKDIR /app

# Create necessary directories with proper permissions
RUN mkdir -p /app/data /app/uploads /app/logs \
    && chown -R appuser:appuser /app

# Copy application code and startup script
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser requirements.txt ./
COPY --chown=appuser:appuser start.sh ./

# Make startup script executable
RUN chmod +x start.sh

# Create .streamlit directory and config
RUN mkdir -p /app/.streamlit && \
    echo '[server]' > /app/.streamlit/config.toml && \
    echo 'address = "0.0.0.0"' >> /app/.streamlit/config.toml && \
    echo 'headless = true' >> /app/.streamlit/config.toml && \
    echo 'enableCORS = false' >> /app/.streamlit/config.toml && \
    echo 'enableXsrfProtection = false' >> /app/.streamlit/config.toml && \
    echo '' >> /app/.streamlit/config.toml && \
    echo '[browser]' >> /app/.streamlit/config.toml && \
    echo 'gatherUsageStats = false' >> /app/.streamlit/config.toml && \
    echo '' >> /app/.streamlit/config.toml && \
    echo '[theme]' >> /app/.streamlit/config.toml && \
    echo 'base = "light"' >> /app/.streamlit/config.toml && \
    chown -R appuser:appuser /app/.streamlit

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8501}/_stcore/health || exit 1

# Use the startup script as default command
CMD ["./start.sh"]
