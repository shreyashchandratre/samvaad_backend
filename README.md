# Samvaad Chatbot Backend 💬

A lightweight API for an emotion-aware chatbot that uses Hugging Face's `distilbert-base-uncased-emotion` model to classify emotions and respond accordingly. The application is containerized using Docker for easy deployment.

## Features

* Emotion-aware responses** using Hugging Face's emotion classification model.
* REST API endpoints** for chat interaction, conversation history, and health check.
* Lightweight and easy deployment** via Docker.

## API Endpoints

* POST `/api/chat`: Sends a message and gets an emotion-aware response.
* GET `/api/chat/history`: Retrieves the conversation history.
* POST `/api/chat/reset`: Resets the conversation.
* GET `/api/health`: Health check for the backend service.

## Deployment with Docker

1. Build Docker image:

   ```bash
   docker build -t samvaad-chatbot-backend .
   ```
2. Run Docker container:

   ```bash
   docker run -p 5000:7860 samvaad-chatbot-backend
   ```

   The app will be available at `http://localhost:5000`.

## Requirements

* Flask==2.3.3
* Flask-CORS==4.0.0
* Transformers==4.35.0
* Torch>=2.0.0
* Numpy==1.24.3

Install dependencies:

```bash
pip install -r requirements.txt
```

## License

MIT License. See the [LICENSE] file for details.
