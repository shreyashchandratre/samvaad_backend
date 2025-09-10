---
title: Samvaad Chatbot Backend
emoji: 💬
colorFrom: pink
colorTo: purple
sdk: docker
app_port: 5000
---

# Samvaad Chatbot Backend

This is a backend API for an emotion-aware chatbot deployed on Hugging Face Spaces using a custom Docker container.

## Features
* **Emotion-aware responses:** The chatbot uses a Hugging Face model to classify user emotions and respond accordingly.
* **API Endpoints:** Provides a REST API for chat interactions, conversation history, and a health check.
* **Lightweight Deployment:** Designed to run efficiently on free-tier cloud services.

## API Endpoints
* `/api/chat` (POST)
* `/api/chat/history` (GET)
* `/api/chat/reset` (POST)
* `/api/health` (GET)

## How It Works
The chatbot is a Flask API that loads a `distilbert-base-uncased-emotion` model using the Hugging Face `transformers` library. The entire application runs inside a Docker container, making it easy to deploy on any platform.
