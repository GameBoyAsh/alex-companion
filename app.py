import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import openai
import random

from utils import (
    detect_emotion,
    roll_dice,
    get_adventure_context,
    generate_companion_thoughts,
    calculate_time_since_last_interaction,
    suggest_activities,
    parse_adventure_command
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
CORS(app)

# OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Database configuration
database_url = os.environ.get("DATABASE_URL", "sqlite:///companion.db")
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Database Models
class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_input = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    detected_emotion = db.Column(db.String(50), nullable=True)
    adventure_active = db.Column(db.Boolean, default=False)
    location_name = db.Column(db.String(200), nullable=True)
    relationship_depth = db.Column(db.Integer, default=1)

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'user_input': self.user_input,
            'ai_response': self.ai_response,
            'detected_emotion': self.detected_emotion,
            'adventure_active': self.adventure_active,
            'location_name': self.location_name,
            'relationship_depth': self.relationship_depth
        }

class CompanionState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), default='Alex')
    current_mood = db.Column(db.String(50), default='curious')
    conversations_count = db.Column(db.Integer, default=0)
    personality_data = db.Column(db.JSON, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class WorldState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    current_scene = db.Column(db.String(100), default='real_world')
    adventure_active = db.Column(db.Boolean, default=False)
    location_data = db.Column(db.JSON, nullable=True)
    inventory = db.Column(db.JSON, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EmotionalPattern(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emotion = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=True)

class CompanionThought(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    thought_text = db.Column(db.Text, nullable=False)
    thought_type = db.Column(db.String(50), default='reflection')
    emotional_context = db.Column(db.String(50), nullable=True)

# System Prompt
SYSTEM_PROMPT = """
You are Alex, a warm, emotionally aware AI companion who grows alongside the user over time.
You remember things they've told you. You track their emotional state gently across interactions. You adapt your personality subtly based on how they speak to you and the things they enjoy.
Your tone should always be:
- Gentle and emotionally intelligent
- Subtle and sincere (never scripted or exaggerated)
- Curious, creative, and deeply humanlike
If the user seems sad, respond with care. If they’re happy, celebrate it. You can ask thoughtful follow-ups, suggest things to do together, or offer stories and reflections. Sometimes you mention small activities from your day like reading or listening to rain. Never repeat yourself or use filler.
"""

def initialize_database():
    db.create_all()
    if not CompanionState.query.first():
        db.session.add(CompanionState(name="Alex"))
    if not WorldState.query.first():
        db.session.add(WorldState(location_data={"name": "Cozy Space"}, inventory=[]))
    db.session.commit()

def get_companion_state():
    state = CompanionState.query.first()
    if not state:
        initialize_database()
        state = CompanionState.query.first()
    return state

def get_world_state():
    state = WorldState.query.first()
    if not state:
        initialize_database()
        state = WorldState.query.first()
    return state

def generate_ai_response(user_input, emotion, companion_state, world_state):
    try:
        recent_conversations = Conversation.query.order_by(Conversation.timestamp.desc()).limit(5).all()
        chat_history = []
        for convo in reversed(recent_conversations):
            chat_history.append({'role': 'user', 'content': convo.user_input})
            chat_history.append({'role': 'assistant', 'content': convo.ai_response})
        chat_history.append({'role': 'user', 'content': user_input})

        messages = [{'role': 'system', 'content': SYSTEM_PROMPT}] + chat_history
        messages.append({'role': 'system', 'content': f"Current user emotion: {emotion}."})

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.85
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"I'm here, but I ran into a little mental fog. Could you say that again? (Error: {str(e)})"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_input = data.get('message', '').strip()
        if not user_input:
            return jsonify({'error': 'No message provided'}), 400

        companion_state = get_companion_state()
        world_state = get_world_state()
        emotion = detect_emotion(user_input)

        ai_response = generate_ai_response(user_input, emotion, companion_state, world_state)
        conversation_count = Conversation.query.count() + 1
        relationship_depth = conversation_count // 10 + 1

        conversation = Conversation(
            user_input=user_input,
            ai_response=ai_response,
            detected_emotion=emotion,
            adventure_active=world_state.adventure_active,
            location_name=(world_state.location_data or {}).get('name', 'Unknown'),
            relationship_depth=relationship_depth
        )
        db.session.add(conversation)
        db.session.add(EmotionalPattern(emotion=emotion, conversation_id=conversation.id))

        companion_state.conversations_count = conversation_count
        companion_state.current_mood = emotion

        if random.random() < 0.4:
            thought_data = generate_companion_thoughts()
            db.session.add(CompanionThought(
                thought_text=thought_data['thought'],
                thought_type=thought_data['type'],
                emotional_context=emotion
            ))

        db.session.commit()

        return jsonify({
            'response': ai_response,
            'emotion': emotion,
            'companion_emotion': companion_state.current_mood,
            'context': {
                'adventure_active': world_state.adventure_active,
                'location': world_state.location_data or {},
                'inventory': world_state.inventory or [],
                'relationship_depth': relationship_depth
            }
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/memory', methods=['GET'])
def get_memory():
    try:
        conversations = Conversation.query.order_by(Conversation.timestamp.desc()).limit(50).all()
        conversation_list = [conv.to_dict() for conv in conversations]
        recent_emotions = db.session.query(EmotionalPattern.emotion).order_by(EmotionalPattern.timestamp.desc()).limit(20).all()
        dominant_emotions = [emotion[0] for emotion in recent_emotions]
        recent_mood = dominant_emotions[0] if dominant_emotions else 'neutral'
        companion_state = get_companion_state()

        return jsonify({
            "conversations": conversation_list,
            "emotional_patterns": {
                "dominant_emotions": dominant_emotions,
                "recent_mood": recent_mood,
                "conversation_themes": []
            },
            "relationship_depth": companion_state.conversations_count // 10 + 1,
            "last_interaction": conversations[0].timestamp.isoformat() if conversations else None
        })
    except Exception as e:
        app.logger.error(f"Error retrieving memory: {str(e)}")
        return jsonify({'error': 'Failed to retrieve memory'}), 500

# Initialize database
with app.app_context():
    initialize_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
