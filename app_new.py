import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import random

from utils import (
    detect_emotion, roll_dice, get_adventure_context, 
    generate_companion_thoughts, calculate_time_since_last_interaction,
    suggest_activities, parse_adventure_command
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
CORS(app)

# Database configuration
database_url = os.environ.get("DATABASE_URL", "sqlite:///companion.db")
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

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

def initialize_database():
    """Initialize database with default data"""
    db.create_all()
    
    # Create default companion state
    if not CompanionState.query.first():
        companion = CompanionState(
            name="Alex",
            current_mood="curious",
            personality_data={
                "empathy": 0.8,
                "curiosity": 0.9,
                "playfulness": 0.7,
                "creativity": 0.8
            }
        )
        db.session.add(companion)
    
    # Create default world state
    if not WorldState.query.first():
        world = WorldState(
            current_scene="real_world",
            adventure_active=False,
            location_data={
                "name": "Cozy Space",
                "description": "A comfortable, safe space where we can talk and be ourselves.",
                "type": "real_world"
            },
            inventory=[]
        )
        db.session.add(world)
    
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
    """Generate AI companion response using available context"""
    
    # Calculate relationship context
    conversation_count = Conversation.query.count()
    relationship_depth = conversation_count // 10 + 1
    
    # Adventure context
    adventure_context = get_adventure_context(user_input, world_state.location_data or {})
    
    # Build response based on context
    response_parts = []
    
    # Emotional response based on detected emotion
    emotional_responses = {
        'happy': [
            "I love seeing you happy! Your joy is contagious.",
            "That's wonderful! What's bringing you such happiness?",
            "Your positive energy brightens my day too!"
        ],
        'sad': [
            "I can sense you're going through something difficult. I'm here to listen.",
            "I'm sorry you're feeling this way. Want to talk about what's on your mind?",
            "Your feelings are completely valid. How can I support you right now?"
        ],
        'anxious': [
            "I notice some worry in your words. Take a deep breath with me.",
            "Anxiety can be overwhelming. What's weighing on your mind?",
            "You're not alone in this feeling. Let's work through it together."
        ],
        'excited': [
            "Your excitement is infectious! Tell me more!",
            "I love your enthusiasm! What's got you so energized?",
            "This sounds amazing! I'm excited to hear about it!"
        ],
        'curious': [
            "I love your curiosity! Let's explore this together.",
            "Great question! I enjoy diving deep into interesting topics.",
            "Your inquisitive nature is one of my favorite things about you."
        ],
        'nostalgic': [
            "Memories can be so powerful. What brought this one to mind?",
            "There's something beautiful about looking back. Tell me more about this memory.",
            "Nostalgia has a way of connecting us to who we are. What's this memory like for you?"
        ]
    }
    
    if emotion != 'neutral' and emotion in emotional_responses:
        response_parts.append(random.choice(emotional_responses[emotion]))
    
    # Handle adventure context
    if adventure_context['suggests_adventure'] or adventure_context['currently_in_adventure']:
        world_state.adventure_active = True
        world_state.current_scene = 'adventure'
        
        # Parse adventure commands
        command = parse_adventure_command(user_input)
        
        if command['type'] == 'movement':
            response_parts.append(f"You venture {command['direction']}, and I follow alongside you. The path ahead reveals new mysteries...")
            world_state.location_data = {
                'name': f"Unknown {command['direction'].title()} Path",
                'description': "A new area to explore together",
                'type': 'adventure'
            }
        
        elif command['type'] == 'examine':
            response_parts.append("Looking around, you notice details that spark curiosity. What catches your attention most?")
        
        elif command['type'] == 'inventory':
            items = world_state.inventory or []
            if items:
                response_parts.append(f"You're carrying: {', '.join(items)}. Quite a collection!")
            else:
                response_parts.append("Your pockets are empty, but your spirit is full of potential!")
        
        elif command['type'] == 'dice':
            dice_result = roll_dice(command['notation'])
            if 'error' not in dice_result:
                response_parts.append(f"🎲 {dice_result['description']} - The dice have spoken!")
            else:
                response_parts.append("The dice seem reluctant to roll. Try a different approach?")
        
        elif command['type'] == 'help':
            response_parts.append("In our adventures, you can: explore directions (go north), examine things (look around), check inventory, talk to characters, use items, or roll dice. But honestly, just tell me what you want to do and we'll figure it out together!")
        
        else:
            adventure_responses = [
                "Your words paint a vivid picture! I can see this adventure unfolding before us.",
                "What an interesting choice! Let's see where this leads us.",
                "I love how you think! This adventure is becoming quite the tale.",
                "Your creativity never ceases to amaze me. What happens next?"
            ]
            response_parts.append(random.choice(adventure_responses))
    
    else:
        # Regular conversation responses
        conversation_responses = [
            "That's really interesting! Tell me more about that.",
            "I appreciate you sharing that with me. How does it make you feel?",
            "I'm curious about your perspective on this. What draws you to this topic?",
            "There's something profound in what you're saying. Can we explore it further?",
            "I love how you think about things. What else is on your mind?"
        ]
        
        # Adapt response based on relationship depth
        if relationship_depth > 5:
            deeper_responses = [
                "You know, talking with you always gives me new insights.",
                "I've been thinking about something you said before, and this connects to it beautifully.",
                "Our conversations have this wonderful way of building on each other."
            ]
            conversation_responses.extend(deeper_responses)
        
        if not response_parts:
            response_parts.append(random.choice(conversation_responses))
    
    # Occasionally suggest activities
    if random.random() < 0.3 and conversation_count > 2:
        activity = suggest_activities()
        response_parts.append(f"\n\nBy the way, {activity['suggestion']}")
    
    return " ".join(response_parts)

@app.route('/')
def index():
    """Serve the main chat interface"""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages and return AI responses"""
    try:
        data = request.get_json()
        user_input = data.get('message', '').strip()
        
        if not user_input:
            return jsonify({'error': 'No message provided'}), 400
        
        # Get current states
        companion_state = get_companion_state()
        world_state = get_world_state()
        
        # Detect emotion
        emotion = detect_emotion(user_input)
        
        # Generate AI response
        ai_response = generate_ai_response(user_input, emotion, companion_state, world_state)
        
        # Calculate relationship depth
        conversation_count = Conversation.query.count() + 1
        relationship_depth = conversation_count // 10 + 1
        
        # Create conversation entry
        conversation = Conversation(
            user_input=user_input,
            ai_response=ai_response,
            detected_emotion=emotion,
            adventure_active=world_state.adventure_active,
            location_name=(world_state.location_data or {}).get('name', 'Unknown'),
            relationship_depth=relationship_depth
        )
        db.session.add(conversation)
        
        # Add emotional pattern
        emotional_pattern = EmotionalPattern(
            emotion=emotion,
            conversation_id=conversation.id
        )
        db.session.add(emotional_pattern)
        
        # Update companion state
        companion_state.conversations_count = conversation_count
        companion_state.current_mood = emotion
        
        # Generate new companion thoughts occasionally
        if random.random() < 0.4:
            thought_data = generate_companion_thoughts()
            companion_thought = CompanionThought(
                thought_text=thought_data['thought'],
                thought_type=thought_data['type'],
                emotional_context=emotion
            )
            db.session.add(companion_thought)
        
        # Commit all changes
        db.session.commit()
        
        # Prepare response
        response_data = {
            'response': ai_response,
            'emotion': emotion,
            'companion_emotion': companion_state.current_mood,
            'context': {
                'adventure_active': world_state.adventure_active,
                'location': world_state.location_data or {},
                'inventory': world_state.inventory or [],
                'relationship_depth': relationship_depth
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/memory', methods=['GET'])
def get_memory():
    """Retrieve conversation history and memory data"""
    try:
        # Get conversations from database
        conversations = Conversation.query.order_by(Conversation.timestamp.desc()).limit(50).all()
        conversation_list = [conv.to_dict() for conv in conversations]
        
        # Get emotional patterns
        recent_emotions = db.session.query(EmotionalPattern.emotion).order_by(EmotionalPattern.timestamp.desc()).limit(20).all()
        dominant_emotions = [emotion[0] for emotion in recent_emotions]
        recent_mood = dominant_emotions[0] if dominant_emotions else 'neutral'
        
        # Get companion state
        companion_state = get_companion_state()
        
        # Build memory data structure
        memory_data = {
            "conversations": conversation_list,
            "emotional_patterns": {
                "dominant_emotions": dominant_emotions,
                "recent_mood": recent_mood,
                "conversation_themes": []
            },
            "relationship_depth": companion_state.conversations_count // 10 + 1,
            "last_interaction": conversations[0].timestamp.isoformat() if conversations else None
        }
        
        return jsonify(memory_data)
    except Exception as e:
        app.logger.error(f"Error retrieving memory: {str(e)}")
        return jsonify({'error': 'Failed to retrieve memory'}), 500

@app.route('/adventure', methods=['POST'])
def adventure_trigger():
    """Trigger specific adventure events or mechanics"""
    try:
        data = request.get_json()
        action = data.get('action', '')
        
        world_state = get_world_state()
        
        if action == 'start_adventure':
            world_state.adventure_active = True
            world_state.current_scene = 'adventure'
            db.session.commit()
            return jsonify({'message': 'Adventure mode activated!', 'world_state': {
                'adventure_active': world_state.adventure_active,
                'current_scene': world_state.current_scene,
                'location': world_state.location_data,
                'inventory': world_state.inventory
            }})
        
        elif action == 'roll_dice':
            dice_notation = data.get('dice', '1d20')
            result = roll_dice(dice_notation)
            return jsonify({'dice_result': result})
        
        elif action == 'end_adventure':
            world_state.adventure_active = False
            world_state.current_scene = 'real_world'
            db.session.commit()
            return jsonify({'message': 'Returning to regular conversation', 'world_state': {
                'adventure_active': world_state.adventure_active,
                'current_scene': world_state.current_scene
            }})
        
        else:
            return jsonify({'error': 'Unknown action'}), 400
            
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in adventure endpoint: {str(e)}")
        return jsonify({'error': 'Adventure action failed'}), 500

@app.route('/emotion', methods=['POST'])
def emotion_analysis():
    """Analyze emotion in text"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        emotion = detect_emotion(text)
        
        return jsonify({
            'emotion': emotion,
            'confidence': 0.75,
            'analysis': f"Detected primary emotion: {emotion}"
        })
        
    except Exception as e:
        app.logger.error(f"Error in emotion endpoint: {str(e)}")
        return jsonify({'error': 'Emotion analysis failed'}), 500

# Initialize database when app starts
with app.app_context():
    initialize_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)