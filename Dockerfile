# Use the official slim Python base image
FROM python:3.10-slim

# 1) Install system dependencies, including poppler for PDF→PNG
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
       git \
       build-essential \
       poppler-utils \
  && rm -rf /var/lib/apt/lists/*

# 2) Set our working directory
WORKDIR /app

# 3) Copy & install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4) Copy in our application code
COPY . .

# 5) Create folders used at runtime
RUN mkdir -p portfolio_uploads static/portfolio_pages

# 6) Expose the port Uvicorn will listen on
EXPOSE 8000

# 7) Default command: launch the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
