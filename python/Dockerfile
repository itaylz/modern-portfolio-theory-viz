# Use a slim Python image
FROM python:3.10-slim

# Install system dependencies for cvxpy (needed for math compilation)
RUN apt-get update && apt-get install -y build-essential

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the code
COPY . .

# Run the app
CMD ["uvicorn", "python-service:app", "--host", "0.0.0.0", "--port", "8000"]