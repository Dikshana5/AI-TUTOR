# Use a slim Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app/backend

# Copy requirements and install dependencies
COPY requirements.txt .
# 1. Install PyTorch CPU-only version explicitly by URL (for Python 3.11)
# This uses the stable CPU-only link for torch 2.8.0, which resolves the CUDA dependency issue.
# We no longer rely on the -f flag which failed to exclude the CUDA dependencies.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --default-timeout=3000 "torch==2.8.0" --index-url https://download.pytorch.org/whl/cpu

# 2. Install the rest of the dependencies from requirements.txt (Use cache mount)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --default-timeout=600 -r requirements.txt
# ...
# 3. Copy the rest of the application (Step 6/7)
COPY . .

# 3. Build the vector index (Step 7/7)
RUN python -c "from detector import load_and_build_index; load_and_build_index(index_dir='vector_index')"

# Expose the port (FastAPI default)
EXPOSE 8000

# Command to run the application (accessible on 0.0.0.0 inside the container)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]