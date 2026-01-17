# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY src/ ./src/
COPY config/ ./config/
COPY data/knowledge_graph.json ./data/
COPY data/d3_graph_documents.json ./data/
COPY data/chroma_db/ ./data/chroma_db/

# Expose the port the app runs on
EXPOSE 5001

# Define environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Command to run the application
CMD ["uvicorn", "src.api.search_api:app", "--host", "0.0.0.0", "--port", "5001"]
