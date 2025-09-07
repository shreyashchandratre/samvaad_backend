from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import pipeline
import logging
import os
import random
import re
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize the emotion classification model
try:
    logger.info("Loading emotion classification model...")
    emotion_classifier = pipeline(
        "text-classification",
        model="bhadresh-savani/distilbert-base-uncased-emotion",
        return_all_scores=True
    )
    logger.info("✅ Emotion classification model loaded successfully!")
except Exception as e:
    logger.error(f"❌ Error loading emotion classification model: {e}")
    emotion_classifier = None

# In-memory conversation storage (in production, use a database)
conversations = {}

# Conversation context and response templates
CONVERSATION_CONTEXTS = {
    'greeting': {
        'keywords': ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening'],
        'responses': [
            "Hello! I'm here to support you on your mental health journey. How are you feeling today?",
            "Hi there! I'm glad you reached out. What's on your mind?",
            "Hello! I'm here to listen and support you. How can I help you today?",
            "Hey! Thanks for connecting with me. What would you like to talk about?"
        ]
    },
    'farewell': {
        'keywords': ['bye', 'goodbye', 'see you', 'talk to you later', 'good night'],
        'responses': [
            "Take care! Remember, I'm here whenever you need someone to talk to. You're not alone.",
            "Goodbye! I hope our conversation helped. Don't hesitate to reach out again.",
            "See you later! Keep taking care of yourself. You're doing great.",
            "Take care of yourself! I'm always here to support you."
        ]
    },
    'gratitude': {
        'keywords': ['thank you', 'thanks', 'appreciate', 'grateful'],
        'responses': [
            "You're very welcome! I'm here to support you, and I'm glad I could help.",
            "It's my pleasure! Supporting you is what I'm here for. How else can I help?",
            "You're welcome! I'm grateful that you trust me enough to share with me.",
            "Anytime! I'm here for you. Is there anything else you'd like to discuss?"
        ]
    },
    'self_care': {
        'keywords': ['tired', 'exhausted', 'stressed', 'overwhelmed', 'burnout'],
        'responses': [
            "It sounds like you're going through a lot right now. Have you considered taking some time for self-care? Even small things like taking a walk or deep breathing can help.",
            "I can hear how overwhelmed you're feeling. What would help you feel a bit better right now? Sometimes just talking about it can be a form of self-care.",
            "You're dealing with a lot, and that's completely valid. What's one small thing you could do today to take care of yourself?",
            "It's okay to feel this way. Self-care isn't selfish - it's necessary. What activities usually help you feel more grounded?"
        ]
    },
    'relationships': {
        'keywords': ['friend', 'family', 'partner', 'relationship', 'love', 'breakup'],
        'responses': [
            "Relationships can be really complex and emotional. Would you like to tell me more about what's happening?",
            "It sounds like this relationship situation is really affecting you. How are you feeling about it?",
            "Relationships can bring up so many different emotions. What's the most challenging part for you right now?",
            "I can hear how important this relationship is to you. What would you like to explore about it?"
        ]
    },
    'work_stress': {
        'keywords': ['work', 'job', 'career', 'boss', 'colleague', 'deadline', 'meeting'],
        'responses': [
            "Work stress can be really challenging. What's been the most difficult part of your work situation?",
            "I can hear how work is affecting you. What would help you feel more supported in your work environment?",
            "Work stress can really impact our mental health. What's one thing that would make your work situation better?",
            "It sounds like work is taking a toll on you. How are you coping with the stress?"
        ]
    },
    'anxiety': {
        'keywords': ['anxious', 'worry', 'panic', 'nervous', 'scared', 'afraid'],
        'responses': [
            "Anxiety can be really overwhelming. What's making you feel most anxious right now?",
            "I can hear how anxious you're feeling. Have you tried any techniques that help you feel more grounded?",
            "Anxiety affects so many people, and it's completely valid to feel this way. What would help you feel a bit calmer?",
            "It sounds like your anxiety is really intense right now. What's one thing that usually helps you feel more at ease?"
        ]
    },
    'depression': {
        'keywords': ['sad', 'depressed', 'hopeless', 'worthless', 'empty', 'numb'],
        'responses': [
            "I can hear how much you're struggling right now. Your feelings are valid, and you don't have to go through this alone. What's been the hardest part?",
            "Depression can make everything feel so heavy. I'm here to listen and support you. What would help you feel even a little bit better?",
            "I can sense how difficult this is for you. Remember that it's okay to not be okay. What's one small thing that might help today?",
            "You're dealing with so much, and I want you to know that your feelings matter. What would you like to talk about?"
        ]
    }
}

# Follow-up questions based on emotion
EMOTION_FOLLOW_UPS = {
    'joy': [
        "What's been the highlight of your day so far?",
        "I love hearing about your happiness! What else is going well for you?",
        "It's wonderful to see you in such a positive space. What's contributing to this joy?",
        "Your positive energy is contagious! What would you like to celebrate?"
    ],
    'sadness': [
        "I can hear how much you're hurting. Would you like to tell me more about what's causing this sadness?",
        "It's okay to feel this way. What's been the hardest part of what you're going through?",
        "I'm here to listen. What would help you feel even a little bit supported right now?",
        "Your feelings are completely valid. What's one thing that might help you feel better?"
    ],
    'anger': [
        "I can feel how frustrated you are. What's been the most challenging part of this situation?",
        "It sounds like you have every right to be angry. What would help you feel heard?",
        "Anger can be really intense. What's underneath this anger for you?",
        "I understand why you're feeling this way. What would help you feel more at peace?"
    ],
    'fear': [
        "Fear can be really overwhelming. What's making you feel most afraid right now?",
        "I can hear how scared you are. What would help you feel safer?",
        "It's natural to feel afraid when things are uncertain. What's one thing that might help you feel more grounded?",
        "I'm here to support you through this fear. What would help you feel more secure?"
    ],
    'surprise': [
        "Wow, that sounds unexpected! How are you feeling about this surprise?",
        "That's quite a surprise! What's your reaction to this news?",
        "I can hear how shocking this is for you. How are you processing this?",
        "That's definitely unexpected! What would help you make sense of this?"
    ],
    'love': [
        "It's beautiful to hear about your feelings of love. What's making you feel this way?",
        "Love is such a powerful emotion. What would you like to share about it?",
        "I can feel the warmth in your words. What's bringing you this feeling of love?",
        "Your love is radiating through your message. What would you like to explore about it?"
    ],
    'neutral': [
        "How are you feeling about everything right now?",
        "What's on your mind today?",
        "I'm here to listen. What would you like to talk about?",
        "How can I support you today?"
    ]
}

def get_conversation_context(user_id):
    """Get or create conversation context for a user"""
    if user_id not in conversations:
        conversations[user_id] = {
            'messages': [],
            'emotion_history': [],
            'topics_discussed': set(),
            'last_interaction': datetime.now(),
            'conversation_start': datetime.now()
        }
    return conversations[user_id]

def detect_conversation_context(message):
    """Detect the conversation context based on keywords"""
    message_lower = message.lower()
    
    for context, data in CONVERSATION_CONTEXTS.items():
        for keyword in data['keywords']:
            if keyword in message_lower:
                return context, random.choice(data['responses'])
    
    return None, None

def generate_contextual_response(user_message, detected_emotion, conversation_context):
    """Generate a contextual response based on conversation history and emotion"""
    
    # Check for specific conversation contexts first
    context, context_response = detect_conversation_context(user_message)
    if context_response:
        return context_response
    
    # Get emotion-based follow-up questions
    emotion_follow_ups = EMOTION_FOLLOW_UPS.get(detected_emotion, EMOTION_FOLLOW_UPS['neutral'])
    
    # Analyze conversation history for better responses
    recent_emotions = conversation_context['emotion_history'][-3:]  # Last 3 emotions
    message_count = len(conversation_context['messages'])
    
    # If this is early in the conversation, be more supportive
    if message_count <= 2:
        if detected_emotion in ['sadness', 'anger', 'fear']:
            return f"I can sense that you're feeling {detected_emotion}, and I want you to know that it's okay to feel this way. Your feelings are valid. {random.choice(emotion_follow_ups)}"
        else:
            return random.choice(emotion_follow_ups)
    
    # If user has been consistently sad/depressed, offer more specific support
    if len(recent_emotions) >= 2 and all(emotion in ['sadness', 'fear'] for emotion in recent_emotions[-2:]):
        return "I've noticed you've been feeling down lately. I want you to know that you don't have to go through this alone. Have you considered talking to a mental health professional? They can provide the support you deserve."
    
    # If user has been consistently angry, help them process
    if len(recent_emotions) >= 2 and all(emotion == 'anger' for emotion in recent_emotions[-2:]):
        return "I can see that you've been feeling angry about this situation. Sometimes anger can be a sign that something important to us has been hurt or threatened. What do you think is at the heart of what's making you angry?"
    
    # If user has been consistently joyful, celebrate with them
    if len(recent_emotions) >= 2 and all(emotion == 'joy' for emotion in recent_emotions[-2:]):
        return "It's wonderful to see you in such a positive space! Your joy is contagious. What's been the most meaningful part of this positive experience for you?"
    
    # Default to emotion-based response
    return random.choice(emotion_follow_ups)

def classify_emotion(text):
    """Classify the emotion in the given text"""
    if not emotion_classifier:
        return 'neutral'
    
    try:
        # Get emotion predictions
        results = emotion_classifier(text)
        
        # Find the emotion with the highest score
        if results and len(results) > 0:
            emotions = results[0]
            # Sort by score in descending order
            emotions.sort(key=lambda x: x['score'], reverse=True)
            return emotions[0]['label']
        else:
            return 'neutral'
    except Exception as e:
        logger.error(f"Error classifying emotion: {e}")
        return 'neutral'

def clean_conversations():
    """Clean old conversations (older than 24 hours)"""
    current_time = datetime.now()
    expired_users = []
    
    for user_id, context in conversations.items():
        if current_time - context['last_interaction'] > timedelta(hours=24):
            expired_users.append(user_id)
    
    for user_id in expired_users:
        del conversations[user_id]
        logger.info(f"Cleaned conversation for user {user_id}")

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages and return contextual, conversational responses"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        user_id = data.get('user_id', 'default_user')  # In production, use actual user authentication
        
        if not user_message:
            return jsonify({
                'response': "I'm here to listen. Please share what's on your mind.",
                'emotion': 'neutral',
                'confidence': 0.0
            }), 400
        
        # Clean old conversations
        clean_conversations()
        
        # Get conversation context
        conversation_context = get_conversation_context(user_id)
        
        # Classify the emotion in the user's message
        detected_emotion = classify_emotion(user_message)
        
        # Get confidence score
        if emotion_classifier:
            results = emotion_classifier(user_message)
            if results and len(results) > 0:
                emotions = results[0]
                # Find the confidence for the detected emotion
                confidence = next((e['score'] for e in emotions if e['label'] == detected_emotion), 0.0)
            else:
                confidence = 0.0
        else:
            confidence = 0.0
        
        # Generate contextual response
        bot_response = generate_contextual_response(user_message, detected_emotion, conversation_context)
        
        # Update conversation context
        conversation_context['messages'].append({
            'user_message': user_message,
            'bot_response': bot_response,
            'emotion': detected_emotion,
            'timestamp': datetime.now().isoformat()
        })
        conversation_context['emotion_history'].append(detected_emotion)
        conversation_context['last_interaction'] = datetime.now()
        
        # Keep only last 20 messages to prevent memory issues
        if len(conversation_context['messages']) > 20:
            conversation_context['messages'] = conversation_context['messages'][-20:]
            conversation_context['emotion_history'] = conversation_context['emotion_history'][-20:]
        
        logger.info(f"User {user_id}: '{user_message}' | Emotion: {detected_emotion} | Confidence: {confidence:.3f}")
        
        return jsonify({
            'response': bot_response,
            'emotion': detected_emotion,
            'confidence': confidence,
            'timestamp': request.json.get('timestamp', ''),
            'conversation_length': len(conversation_context['messages'])
        })
        
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        return jsonify({
            'response': "I'm having trouble processing your message right now. Please try again in a moment.",
            'emotion': 'neutral',
            'confidence': 0.0
        }), 500

@app.route('/api/chat/reset', methods=['POST'])
def reset_conversation():
    """Reset conversation for a user"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        
        if user_id in conversations:
            del conversations[user_id]
        
        return jsonify({
            'message': 'Conversation reset successfully',
            'status': 'success'
        })
    except Exception as e:
        logger.error(f"Error resetting conversation: {e}")
        return jsonify({
            'message': 'Error resetting conversation',
            'status': 'error'
        }), 500

@app.route('/api/chat/history', methods=['GET'])
def get_conversation_history():
    """Get conversation history for a user"""
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        if user_id in conversations:
            return jsonify({
                'messages': conversations[user_id]['messages'],
                'emotion_history': conversations[user_id]['emotion_history'],
                'conversation_start': conversations[user_id]['conversation_start'].isoformat()
            })
        else:
            return jsonify({
                'messages': [],
                'emotion_history': [],
                'conversation_start': None
            })
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return jsonify({
            'message': 'Error retrieving conversation history',
            'status': 'error'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': emotion_classifier is not None,
        'message': 'Chatbot backend is running',
        'active_conversations': len(conversations)
    })

@app.route('/', methods=['GET'])
def home():
    """Root endpoint"""
    return jsonify({
        'message': 'Samvaad Chatbot Backend',
        'version': '2.0.0',
        'features': [
            'Emotion-aware responses',
            'Conversation memory',
            'Contextual responses',
            'Mental health support'
        ],
        'endpoints': {
            'chat': '/api/chat (POST)',
            'chat_reset': '/api/chat/reset (POST)',
            'chat_history': '/api/chat/history (GET)',
            'health': '/api/health (GET)'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 