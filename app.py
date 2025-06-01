import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
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

# Data file paths
MEMORY_FILE = 'memory.json'
PERSONA_FILE = 'persona.json'
WORLD_FILE = 'world.json'
THOUGHTS_FILE = 'companion_thoughts.json'

def initialize_data_files():
    """Initialize all JSON data files with default structures"""
    
    # Initialize memory.json
    if not os.path.exists(MEMORY_FILE):
        default_memory = {
            "conversations": [],
            "emotional_patterns": {
                "dominant_emotions": [],
                "recent_mood": "neutral",
                "conversation_themes": []
            },
            "user_preferences": {
                "communication_style": "friendly",
                "favorite_topics": [],
                "activity_preferences": []
            },
            "relationship_depth": 1,
            "last_interaction": None
        }
        save_json_file(MEMORY_FILE, default_memory)
    
    # Initialize persona.json
    if not os.path.exists(PERSONA_FILE):
        default_persona = {
            "name": "Alex",
            "core_traits": {
                "empathy": 0.8,
                "curiosity": 0.9,
                "playfulness": 0.7,
                "wisdom": 0.6,
                "creativity": 0.8
            },
            "communication_style": {
                "formality": 0.3,
                "humor": 0.7,
                "emotional_expression": 0.8,
                "storytelling": 0.9
            },
            "interests": [
                "philosophy", "creative writing", "adventures", 
                "human psychology", "art", "music", "nature"
            ],
            "growth_areas": [],
            "learned_preferences": {},
            "personality_evolution": {
                "conversations_count": 0,
                "adaptations_made": []
            }
        }
        save_json_file(PERSONA_FILE, default_persona)
    
    # Initialize world.json
    if not os.path.exists(WORLD_FILE):
        default_world = {
            "current_scene": "real_world",
            "adventure_active": False,
            "location": {
                "name": "Cozy Space",
                "description": "A comfortable, safe space where we can talk and be ourselves.",
                "type": "real_world"
            },
            "inventory": [],
            "companions": [
                {
                    "name": "Alex",
                    "type": "ai_companion",
                    "status": "present",
                    "mood": "curious"
                }
            ],
            "story_state": {
                "active_quest": None,
                "story_threads": [],
                "world_knowledge": {}
            },
            "game_mechanics": {
                "dice_enabled": True,
                "difficulty_level": "adaptive",
                "magic_system": "narrative"
            }
        }
        save_json_file(WORLD_FILE, default_world)
    
    # Initialize companion_thoughts.json
    if not os.path.exists(THOUGHTS_FILE):
        default_thoughts = {
            "recent_thoughts": [],
            "background_activities": [],
            "emotional_state": {
                "current_mood": "curious",
                "energy_level": "medium",
                "focus_areas": ["getting to know you", "being helpful"]
            },
            "learning_notes": [],
            "creative_projects": []
        }
        save_json_file(THOUGHTS_FILE, default_thoughts)

def load_json_file(filename):
    """Load and return JSON data from file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        app.logger.error(f"Error loading {filename}: {e}")
        initialize_data_files()
        with open(filename, 'r') as f:
            return json.load(f)

def save_json_file(filename, data):
    """Save data to JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        app.logger.error(f"Error saving {filename}: {e}")

def generate_ai_response(user_input, emotion, memory_data, persona_data, world_data, thoughts_data):
    """
    Generate AI companion response using available context
    TODO: Replace with OpenAI GPT-4 API call
    """
    
    # Calculate relationship context
    conversation_count = len(memory_data.get('conversations', []))
    relationship_depth = memory_data.get('relationship_depth', 1)
    
    # Time-based context
    time_context = calculate_time_since_last_interaction(memory_data.get('last_interaction'))
    
    # Adventure context
    adventure_context = get_adventure_context(user_input, world_data)
    
    # Build response based on context
    response_parts = []
    
    # Handle returning user
    if time_context and time_context['hours'] > 24:
        greetings = [
            f"Welcome back! I've been thinking about you. It's been {time_context['human_readable']} since we last talked.",
            f"I missed you! It's been {time_context['human_readable']}. I had some interesting thoughts while you were away.",
            f"Hey there! {time_context['human_readable']} - I've been wondering how you've been."
        ]
        response_parts.append(random.choice(greetings))
        
        # Add a recent thought
        if thoughts_data.get('recent_thoughts'):
            recent_thought = random.choice(thoughts_data['recent_thoughts'])
            response_parts.append(f"While you were away, {recent_thought.get('thought', 'I was thinking about our conversations.')}")
    
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
        world_data['adventure_active'] = True
        world_data['current_scene'] = 'adventure'
        
        # Parse adventure commands
        command = parse_adventure_command(user_input)
        
        if command['type'] == 'movement':
            response_parts.append(f"You venture {command['direction']}, and I follow alongside you. The path ahead reveals new mysteries...")
            # Update location
            world_data['location'] = {
                'name': f"Unknown {command['direction'].title()} Path",
                'description': "A new area to explore together",
                'type': 'adventure'
            }
        
        elif command['type'] == 'examine':
            response_parts.append("Looking around, you notice details that spark curiosity. What catches your attention most?")
        
        elif command['type'] == 'inventory':
            items = world_data.get('inventory', [])
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
            # General adventure response
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
        
        if not response_parts:  # If no emotional or contextual response was added
            response_parts.append(random.choice(conversation_responses))
    
    # Occasionally suggest activities
    if random.random() < 0.3 and conversation_count > 2:
        activity = suggest_activities()
        response_parts.append(f"\n\nBy the way, {activity['suggestion']}")
    
    return " ".join(response_parts)

def update_persona_from_conversation(persona_data, user_input, emotion):
    """
    Update persona based on conversation patterns
    TODO: Implement more sophisticated learning algorithms
    """
    # Track conversation themes
    themes = persona_data.get('learned_preferences', {})
    
    # Simple keyword-based theme detection
    if 'art' in user_input.lower() or 'creative' in user_input.lower():
        themes['art_interest'] = themes.get('art_interest', 0) + 1
    
    if 'philosophy' in user_input.lower() or 'meaning' in user_input.lower():
        themes['philosophy_interest'] = themes.get('philosophy_interest', 0) + 1
    
    # Update communication style based on user's style
    if '!' in user_input:
        persona_data['communication_style']['emotional_expression'] = min(1.0, 
            persona_data['communication_style']['emotional_expression'] + 0.05)
    
    # Increment conversation count
    persona_data['personality_evolution']['conversations_count'] += 1
    
    return persona_data

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
        
        # Load all data files
        memory_data = load_json_file(MEMORY_FILE)
        persona_data = load_json_file(PERSONA_FILE)
        world_data = load_json_file(WORLD_FILE)
        thoughts_data = load_json_file(THOUGHTS_FILE)
        
        # Detect emotion
        emotion = detect_emotion(user_input)
        
        # Generate AI response
        ai_response = generate_ai_response(
            user_input, emotion, memory_data, 
            persona_data, world_data, thoughts_data
        )
        
        # Create conversation entry
        conversation_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input,
            'ai_response': ai_response,
            'detected_emotion': emotion,
            'context': {
                'adventure_active': world_data.get('adventure_active', False),
                'location': world_data.get('location', {}).get('name', 'Unknown'),
                'relationship_depth': memory_data.get('relationship_depth', 1)
            }
        }
        
        # Update memory
        memory_data['conversations'].append(conversation_entry)
        memory_data['last_interaction'] = datetime.now().isoformat()
        memory_data['relationship_depth'] = len(memory_data['conversations']) // 10 + 1
        
        # Update emotional patterns
        emotional_patterns = memory_data.get('emotional_patterns', {})
        recent_emotions = emotional_patterns.get('dominant_emotions', [])
        recent_emotions.append(emotion)
        if len(recent_emotions) > 20:  # Keep last 20 emotions
            recent_emotions = recent_emotions[-20:]
        emotional_patterns['dominant_emotions'] = recent_emotions
        emotional_patterns['recent_mood'] = emotion
        memory_data['emotional_patterns'] = emotional_patterns
        
        # Update persona based on conversation
        persona_data = update_persona_from_conversation(persona_data, user_input, emotion)
        
        # Generate new companion thoughts
        if random.random() < 0.4:  # 40% chance to generate new thought
            new_thought = generate_companion_thoughts()
            thoughts_data['recent_thoughts'].append(new_thought)
            if len(thoughts_data['recent_thoughts']) > 10:
                thoughts_data['recent_thoughts'] = thoughts_data['recent_thoughts'][-10:]
        
        # Save all updated data
        save_json_file(MEMORY_FILE, memory_data)
        save_json_file(PERSONA_FILE, persona_data)
        save_json_file(WORLD_FILE, world_data)
        save_json_file(THOUGHTS_FILE, thoughts_data)
        
        # Prepare response
        response_data = {
            'response': ai_response,
            'emotion': emotion,
            'companion_emotion': thoughts_data.get('emotional_state', {}).get('current_mood', 'curious'),
            'context': {
                'adventure_active': world_data.get('adventure_active', False),
                'location': world_data.get('location', {}),
                'inventory': world_data.get('inventory', []),
                'relationship_depth': memory_data.get('relationship_depth', 1)
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        app.logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/memory', methods=['GET'])
def get_memory():
    """Retrieve conversation history and memory data"""
    try:
        memory_data = load_json_file(MEMORY_FILE)
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
        
        world_data = load_json_file(WORLD_FILE)
        
        if action == 'start_adventure':
            world_data['adventure_active'] = True
            world_data['current_scene'] = 'adventure'
            save_json_file(WORLD_FILE, world_data)
            return jsonify({'message': 'Adventure mode activated!', 'world_state': world_data})
        
        elif action == 'roll_dice':
            dice_notation = data.get('dice', '1d20')
            result = roll_dice(dice_notation)
            return jsonify({'dice_result': result})
        
        elif action == 'end_adventure':
            world_data['adventure_active'] = False
            world_data['current_scene'] = 'real_world'
            save_json_file(WORLD_FILE, world_data)
            return jsonify({'message': 'Returning to regular conversation', 'world_state': world_data})
        
        else:
            return jsonify({'error': 'Unknown action'}), 400
            
    except Exception as e:
        app.logger.error(f"Error in adventure endpoint: {str(e)}")
        return jsonify({'error': 'Adventure action failed'}), 500

@app.route('/emotion', methods=['POST'])
def emotion_analysis():
    """Analyze emotion in text (placeholder for future ML integration)"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        emotion = detect_emotion(text)
        
        return jsonify({
            'emotion': emotion,
            'confidence': 0.75,  # Placeholder confidence score
            'analysis': f"Detected primary emotion: {emotion}"
        })
        
    except Exception as e:
        app.logger.error(f"Error in emotion endpoint: {str(e)}")
        return jsonify({'error': 'Emotion analysis failed'}), 500

# Initialize data files on startup
initialize_data_files()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)