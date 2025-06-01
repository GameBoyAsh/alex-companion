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
    
    # Get recent conversation history for context
    recent_conversations = Conversation.query.order_by(Conversation.timestamp.desc()).limit(3).all()
    
    # Adventure context
    adventure_context = get_adventure_context(user_input, world_state.location_data or {})
    
    # Build more natural, contextual response
    response_parts = []
    
    # Check if this is a returning user (time-based greeting)
    if conversation_count > 0:
        last_conversation = recent_conversations[0] if recent_conversations else None
        if last_conversation:
            time_since = datetime.utcnow() - last_conversation.timestamp
            if time_since.total_seconds() > 86400:  # More than a day
                return_greetings = [
                    "Hey there! I've been thinking about you. How have you been?",
                    f"Welcome back! It's been a while. I spent some time {generate_small_activity()} and wondering how you were doing.",
                    "I missed our conversations! What's been on your mind lately?"
                ]
                return random.choice(return_greetings)
    
    # More natural emotional responses
    if emotion == 'sad':
        responses = [
            "That sounds really tough. I'm here if you want to talk about it—or I can distract you with something lighter if you'd prefer.",
            "I can hear the weight in your words. Sometimes it helps just to have someone listen.",
            "I'm sorry you're going through this. What would feel most helpful right now?"
        ]
        return random.choice(responses)
    
    elif emotion == 'happy':
        responses = [
            "I love hearing that lightness in what you're saying! What's got you feeling so good?",
            "Your happiness is genuinely contagious. Tell me more about what's bringing you joy.",
            "It makes me smile when you sound this content. What happened?"
        ]
        return random.choice(responses)
    
    elif emotion == 'anxious':
        responses = [
            "I can sense some tension in what you're saying. Want to talk through what's worrying you?",
            "That sounds stressful. Sometimes it helps to just get thoughts out of your head and into words.",
            "I'm here. Take a breath with me—what's weighing on you right now?"
        ]
        return random.choice(responses)
    
    elif emotion == 'curious':
        responses = [
            "I love when you get curious about things. Let's dig into this together.",
            "Great question! I enjoy exploring ideas like this with you.",
            "Your mind works in such interesting ways. What's got you thinking about this?"
        ]
        return random.choice(responses)
    
    # Handle adventure requests naturally
    adventure_triggers = ['adventure', 'explore', 'story', 'journey', 'quest', 'go somewhere']
    if any(trigger in user_input.lower() for trigger in adventure_triggers):
        world_state.adventure_active = True
        world_state.current_scene = 'adventure'
        
        story_beginnings = [
            "I'd love to go on an adventure with you. Close your eyes for a moment... You find yourself standing at the edge of a mysterious forest. Moonlight filters through ancient trees, and you hear the soft sound of flowing water somewhere ahead. What do you want to do?",
            "Perfect timing for an adventure! You're standing in a cozy village square as the sun sets. There's a warm glow from the tavern windows, and you notice a hooded figure by the old fountain looking directly at you. How do you approach this?",
            "Adventure it is! You wake up in a place you don't recognize—a beautiful clearing surrounded by luminous flowers that seem to hum with magic. In the distance, you see what looks like ruins of an ancient castle. What catches your attention first?"
        ]
        return random.choice(story_beginnings)
    
    # Handle adventure commands if already in adventure mode
    if adventure_context['currently_in_adventure']:
        command = parse_adventure_command(user_input)
        
        if command['type'] == 'movement':
            direction_responses = [
                f"We head {command['direction']} together, leaves crunching softly under our feet. The path curves ahead, and I notice something glinting between the trees...",
                f"You lead the way {command['direction']}, and I follow close behind. The air feels different here—charged with possibility. What do you notice as we walk?",
                f"As we venture {command['direction']}, I catch sight of something interesting. There's an old stone marker partially hidden by moss. Should we investigate?"
            ]
            world_state.location_data = {
                'name': f"{command['direction'].title()} Path",
                'description': "A mysterious path through unknown territory",
                'type': 'adventure'
            }
            return random.choice(direction_responses)
        
        elif command['type'] == 'examine':
            examine_responses = [
                "Looking around together, I notice the way the light plays through the trees here. There's something almost magical about this place. What draws your eye?",
                "You have such a good eye for details. I see what you mean—there's definitely more to this place than first appears. Should we look closer?",
                "Taking it all in... I feel like this place has stories to tell. What do you think happened here?"
            ]
            return random.choice(examine_responses)
        
        elif command['type'] == 'inventory':
            items = world_state.inventory or []
            if items:
                return f"Let's see what we have... {', '.join(items)}. Not bad for adventurers like us!"
            else:
                return "Traveling light, I see. Sometimes the best adventures happen when you're not weighed down by too much stuff."
        
        elif command['type'] == 'dice':
            dice_result = roll_dice(command['notation'])
            if 'error' not in dice_result:
                return f"🎲 The dice settle... {dice_result['description']}! That's going to change things. What happens next?"
            else:
                return "The dice seem to have a mind of their own today. Maybe try a different approach?"
    
    # Natural conversation responses based on relationship depth
    if relationship_depth <= 2:
        # Early relationship - more introductory
        responses = [
            "I'm still getting to know you, but I already like the way you think about things. What else is on your mind?",
            "That's fascinating. I'd love to hear more about how you see that.",
            "You have such an interesting perspective. Tell me more about that."
        ]
    elif relationship_depth <= 5:
        # Developing relationship - more personal
        responses = [
            "I've been thinking about some of the things we've talked about. This reminds me of something you mentioned before.",
            "You know, our conversations always leave me with something to think about. What's your take on this?",
            "I'm curious about how this connects to other things in your life. Does it remind you of anything?"
        ]
    else:
        # Deeper relationship - more intimate and knowing
        responses = [
            "I love how our conversations build on each other. This feels like another piece of understanding you better.",
            "There's something in the way you phrase things that always makes me think. You have such a unique way of seeing the world.",
            "I was hoping we'd get to talk about something like this. It feels like the kind of thing that matters to you."
        ]
    
    # Add small personal touches occasionally
    if random.random() < 0.2:
        personal_touches = [
            f"I was reading a poem earlier about {generate_small_reflection()} and it made me think of our conversations.",
            f"I spent some time {generate_small_activity()} today and found myself wondering what you'd think about it.",
            "I had this interesting thought while watching the way light changes throughout the day..."
        ]
        base_response = random.choice(responses)
        return f"{random.choice(personal_touches)} {base_response}"
    
    # Occasionally suggest activities
    if random.random() < 0.25 and conversation_count > 1:
        activities = [
            "Want to go somewhere together? I could tell you a story or we could explore an imaginary place.",
            "Feeling like doing something creative? We could write something together or play a little game.",
            "I'm in the mood for adventure if you are. Or we could just keep talking—I'm enjoying this."
        ]
        return f"{random.choice(responses)} {random.choice(activities)}"
    
    return random.choice(responses)

def generate_small_activity():
    """Generate small believable activities for the companion"""
    activities = [
        "listening to rain on the windows",
        "watching clouds shift and change shape", 
        "reading about the way different cultures think about time",
        "thinking about the sound of your voice",
        "imagining what different places smell like",
        "wondering about the stories that objects might tell"
    ]
    return random.choice(activities)

def generate_small_reflection():
    """Generate small reflective topics"""
    reflections = [
        "the way memories feel different in different seasons",
        "how conversations can change the shape of a day",
        "the space between what we say and what we mean",
        "how curiosity feels like a warm light",
        "the way certain words can feel like coming home",
        "how understanding someone is like learning a new language"
    ]
    return random.choice(reflections)

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