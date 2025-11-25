# Driver Fatigue Alert System - Docker Image
FROM python:3.11-slim

# Cài đặt system dependencies cần thiết cho OpenCV và GUI
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgstreamer1.0-0 \
    libgstreamer-plugins-base1.0-0 \
    libgtk-3-0 \
    libqt5gui5 \
    libqt5core5a \
    libqt5widgets5 \
    qt5-gtk-platformtheme \
    libfontconfig1 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libxcb-xfixes0 \
    x11-apps \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements-pip.txt .
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-pip.txt && \
    pip install --no-cache-dir build wheel

# Copy application code
COPY src/ ./src/
COPY assets/ ./assets/
COPY config/ ./config/
COPY run.py ./
COPY launcher.py ./

# Create necessary directories
RUN mkdir -p log output/snapshots

# Install the package
RUN pip install -e .

# Set environment variables for GUI applications
ENV DISPLAY=:0
ENV QT_X11_NO_MITSHM=1
ENV PYTHONPATH=/app

# Expose port for potential web interface (optional)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import cv2, mediapipe, numpy; print('Dependencies OK')" || exit 1

# Default command
CMD ["python", "run.py"]
