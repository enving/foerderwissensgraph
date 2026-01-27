# Use the official Apify Python image
FROM apify/actor-python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy requirements and install
COPY apify_actor/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m spacy download de_core_news_sm

# Copy the actor wrapper
COPY apify_actor/main.py ./apify_actor/
COPY apify_actor/actor.json ./
COPY apify_actor/input_schema.json ./

# Copy the core application and data
# We include data/ in the image for the "Brain" to be portable
COPY src/ ./src/
COPY config/ ./config/
COPY data/ ./data/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run the actor
CMD ["python3", "apify_actor/main.py"]
