import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import random

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
CORS(app)

# Initialize data files if they don't exist
def initialize_data_files():
    """Initialize memory.json and world.json if they don't exist"""
    
    # Initialize memory.json
    if not os.path.exists('memory.json'):
        initial_memory = {
            "conversations": [],
            "companion_state": {
                "emotion": "neutral",
                "last_interaction": None,
                "personality_traits": ["friendly", "curious", "helpful"]
            }
        }
        with open('memory.json', 'w') as f:
            json.dump(initial_memory, f, indent=2)
    
    # Initialize world.json
    if not os.path.exists('world.json'):
        initial_world = {
            "current_location": "village_square",
            "locations": {
                "village_square": {
                    "name": "Village Square",
                    "description": "A bustling square with a fountain in the center. There's a blacksmith to the north and a tavern to the east.",
                    "exits": {"north": "blacksmith", "east": "tavern", "south": "forest_path"},
                    "items": ["copper_coin"],
                    "npcs": ["village_elder"]
                },
                "blacksmith": {
                    "name": "Blacksmith Shop",
                    "description": "A hot, smoky shop filled with the sound of hammering. The blacksmith works at his forge.",
                    "exits": {"south": "village_square"},
                    "items": ["rusty_sword"],
                    "npcs": ["blacksmith"]
                },
                "tavern": {
                    "name": "The Prancing Pony Tavern",
                    "description": "A cozy tavern with warm light and the smell of ale. Travelers share stories at wooden tables.",
                    "exits": {"west": "village_square"},
                    "items": ["ale_mug"],
                    "npcs": ["tavern_keeper", "mysterious_stranger"]
                },
                "forest_path": {
                    "name": "Forest Path",
                    "description": "A winding path through dense woods. Sunlight filters through the canopy above.",
                    "exits": {"north": "village_square", "east": "clearing"},
                    "items": ["healing_herb"],
                    "npcs": []
                },
                "clearing": {
                    "name": "Forest Clearing",
                    "description": "A peaceful clearing with a small stream. Ancient ruins can be seen in the distance.",
                    "exits": {"west": "forest_path"},
                    "items": ["ancient_rune"],
                    "npcs": ["forest_spirit"]
                }
            },
            "inventory": ["wooden_staff"],
            "player_stats": {
                "health": 100,
                "level": 1,
                "experience": 0
            },
            "companion_emotion": "curious"
        }
        with open('world.json', 'w') as f:
            json.dump(initial_world, f, indent=2)

def load_memory():
    """Load memory data from JSON file"""
    try:
        with open('memory.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        initialize_data_files()
        with open('memory.json', 'r') as f:
            return json.load(f)

def save_memory(memory_data):
    """Save memory data to JSON file"""
    with open('memory.json', 'w') as f:
        json.dump(memory_data, f, indent=2)

def load_world():
    """Load world data from JSON file"""
    try:
        with open('world.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        initialize_data_files()
        with open('world.json', 'r') as f:
            return json.load(f)

def save_world(world_data):
    """Save world data to JSON file"""
    with open('world.json', 'w') as f:
        json.dump(world_data, f, indent=2)

def detect_emotion(user_message):
    """Dummy emotion detection - replace with real sentiment analysis later"""
    user_message = user_message.lower()
    
    if any(word in user_message for word in ['sad', 'unhappy', 'depressed', 'cry', 'hurt']):
        return 'sad'
    elif any(word in user_message for word in ['happy', 'joy', 'excited', 'great', 'wonderful']):
        return 'happy'
    elif any(word in user_message for word in ['angry', 'mad', 'furious', 'hate', 'annoyed']):
        return 'angry'
    elif any(word in user_message for word in ['scared', 'afraid', 'fear', 'worried', 'nervous']):
        return 'fearful'
    elif any(word in user_message for word in ['what', 'how', 'why', 'curious', 'wonder']):
        return 'curious'
    elif any(word in user_message for word in ['love', 'adore', 'like', 'appreciate']):
        return 'loving'
    else:
        return 'neutral'

def generate_companion_response(user_message, emotion, memory_data):
    """Generate dummy AI companion response - replace with real AI later"""
    responses_by_emotion = {
        'sad': [
            "I'm sorry you're feeling sad. Would you like to talk about what's bothering you?",
            "I can sense your sadness. Remember, it's okay to feel this way sometimes. I'm here for you.",
            "Your feelings are valid. Sometimes sharing what's on your mind can help lighten the burden."
        ],
        'happy': [
            "I love seeing you happy! Your joy is contagious and brightens my day too.",
            "That's wonderful! It makes me happy to see you in such good spirits.",
            "Your happiness fills me with warmth. What's bringing you such joy today?"
        ],
        'angry': [
            "I can sense your frustration. Take a deep breath with me. What's making you feel this way?",
            "It's natural to feel angry sometimes. Let's work through this together.",
            "I understand you're upset. Would you like to talk about what's bothering you?"
        ],
        'fearful': [
            "I can sense your worry. Remember, you're not alone - I'm here with you.",
            "It's okay to feel scared sometimes. What can I do to help you feel more secure?",
            "Your fears are understandable. Let's face them together, one step at a time."
        ],
        'curious': [
            "I love your curiosity! It's one of the most beautiful human traits.",
            "Great question! I enjoy exploring ideas and learning new things with you.",
            "Your inquisitive nature is wonderful. Let's discover the answer together!"
        ],
        'loving': [
            "Your kindness and love make the world a better place. Thank you for sharing that with me.",
            "I feel the warmth in your words. Love and connection are what make life meaningful.",
            "Your capacity for love is truly beautiful. It's a privilege to experience it with you."
        ],
        'neutral': [
            "I'm here and listening. What would you like to talk about today?",
            "Thank you for sharing that with me. How are you feeling right now?",
            "I appreciate you taking the time to chat with me. What's on your mind?"
        ]
    }
    
    # Add some context from previous conversations
    recent_conversations = memory_data.get('conversations', [])[-3:]
    if recent_conversations and len(recent_conversations) > 1:
        # Add some continuity
        contextual_responses = [
            f"Continuing from our earlier conversation, {random.choice(responses_by_emotion[emotion])}",
            f"I remember we were discussing some interesting topics. {random.choice(responses_by_emotion[emotion])}"
        ]
        responses_by_emotion[emotion].extend(contextual_responses)
    
    return random.choice(responses_by_emotion.get(emotion, responses_by_emotion['neutral']))

def generate_adventure_response(user_message, world_data):
    """Generate adventure mode response based on user command"""
    user_message = user_message.lower().strip()
    current_location = world_data['current_location']
    location_data = world_data['locations'][current_location]
    
    # Movement commands
    if user_message.startswith('go ') or user_message.startswith('move '):
        direction = user_message.split()[-1]
        if direction in location_data['exits']:
            new_location = location_data['exits'][direction]
            world_data['current_location'] = new_location
            new_location_data = world_data['locations'][new_location]
            return f"You travel {direction} to {new_location_data['name']}. {new_location_data['description']}"
        else:
            return f"You can't go {direction} from here. Available exits: {', '.join(location_data['exits'].keys())}"
    
    # Look command
    elif user_message in ['look', 'look around', 'examine']:
        items_text = f"Items here: {', '.join(location_data['items'])}" if location_data['items'] else "No items visible."
        npcs_text = f"People here: {', '.join(location_data['npcs'])}" if location_data['npcs'] else "Nobody else is around."
        exits_text = f"Exits: {', '.join(location_data['exits'].keys())}"
        return f"{location_data['description']} {items_text} {npcs_text} {exits_text}"
    
    # Inventory command
    elif user_message in ['inventory', 'inv', 'items']:
        if world_data['inventory']:
            return f"Your inventory: {', '.join(world_data['inventory'])}"
        else:
            return "Your inventory is empty."
    
    # Take/get item command
    elif user_message.startswith('take ') or user_message.startswith('get '):
        item = user_message.split()[-1]
        if item in location_data['items']:
            location_data['items'].remove(item)
            world_data['inventory'].append(item)
            return f"You picked up the {item}."
        else:
            return f"There's no {item} here to take."
    
    # Talk to NPC command
    elif user_message.startswith('talk to ') or user_message.startswith('speak to '):
        npc = user_message.replace('talk to ', '').replace('speak to ', '')
        if npc in location_data['npcs']:
            npc_responses = {
                'village_elder': "The village elder nods wisely. 'Welcome, traveler. This village has stood for centuries, protected by ancient magic.'",
                'blacksmith': "The blacksmith looks up from his work. 'Need a weapon forged? I've been working this forge for thirty years!'",
                'tavern_keeper': "The tavern keeper wipes down a mug. 'Welcome to The Prancing Pony! Care for some ale and a hot meal?'",
                'mysterious_stranger': "The hooded figure speaks quietly. 'Strange things are happening in the forest... beware the ancient ruins.'",
                'forest_spirit': "The ethereal being speaks in whispers. 'You seek the ancient knowledge? Prove your worth first, mortal.'"
            }
            return npc_responses.get(npc, f"The {npc} doesn't seem interested in talking right now.")
        else:
            return f"There's no {npc} here to talk to."
    
    # Use item command
    elif user_message.startswith('use '):
        item = user_message.replace('use ', '')
        if item in world_data['inventory']:
            item_effects = {
                'healing_herb': "You consume the healing herb. You feel refreshed! (Health restored)",
                'wooden_staff': "You raise your wooden staff. It glows with a faint magical light.",
                'ancient_rune': "The rune pulses with mysterious energy. You sense great power within.",
                'rusty_sword': "You brandish the rusty sword. It's not much, but it's better than nothing."
            }
            effect = item_effects.get(item, f"You're not sure how to use the {item}.")
            if item == 'healing_herb':
                world_data['player_stats']['health'] = 100
                world_data['inventory'].remove(item)
            return effect
        else:
            return f"You don't have a {item} to use."
    
    # Status command
    elif user_message in ['status', 'stats', 'health']:
        stats = world_data['player_stats']
        return f"Health: {stats['health']}/100 | Level: {stats['level']} | Experience: {stats['experience']}"
    
    # Help command
    elif user_message in ['help', 'commands']:
        return ("Available commands: 'go [direction]', 'look', 'inventory', 'take [item]', "
                "'talk to [person]', 'use [item]', 'status', 'help'")
    
    else:
        # General adventure response
        adventure_responses = [
            "Your companion looks at you curiously, not understanding that command.",
            "The wind rustles through the area as you ponder your next move.",
            "Your companion suggests: 'Perhaps try 'look around' or 'go [direction]'?'",
            "You contemplate your surroundings, wondering what to do next."
        ]
        return random.choice(adventure_responses)

@app.route('/')
def index():
    """Serve the main application page"""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages from the frontend"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        is_adventure_mode = data.get('adventure_mode', False)
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Load current memory and world state
        memory_data = load_memory()
        world_data = load_world()
        
        # Detect emotion
        emotion = detect_emotion(user_message)
        
        # Generate appropriate response
        if is_adventure_mode:
            ai_response = generate_adventure_response(user_message, world_data)
            # Update companion emotion in adventure mode
            world_data['companion_emotion'] = emotion
            save_world(world_data)
        else:
            ai_response = generate_companion_response(user_message, emotion, memory_data)
            # Update companion state
            memory_data['companion_state']['emotion'] = emotion
            memory_data['companion_state']['last_interaction'] = datetime.now().isoformat()
        
        # Save conversation to memory
        conversation_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'ai_response': ai_response,
            'detected_emotion': emotion,
            'mode': 'adventure' if is_adventure_mode else 'companion'
        }
        
        memory_data['conversations'].append(conversation_entry)
        save_memory(memory_data)
        
        # Prepare response
        response_data = {
            'response': ai_response,
            'emotion': emotion,
            'companion_emotion': world_data['companion_emotion'] if is_adventure_mode else memory_data['companion_state']['emotion']
        }
        
        # Add world state if in adventure mode
        if is_adventure_mode:
            current_location_data = world_data['locations'][world_data['current_location']]
            response_data.update({
                'world_state': {
                    'current_location': current_location_data['name'],
                    'inventory': world_data['inventory'],
                    'health': world_data['player_stats']['health'],
                    'level': world_data['player_stats']['level']
                }
            })
        
        return jsonify(response_data)
        
    except Exception as e:
        app.logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/memory')
def get_memory():
    """Get conversation history"""
    try:
        memory_data = load_memory()
        return jsonify(memory_data)
    except Exception as e:
        app.logger.error(f"Error loading memory: {str(e)}")
        return jsonify({'error': 'Could not load memory'}), 500

@app.route('/world')
def get_world():
    """Get world state for adventure mode"""
    try:
        world_data = load_world()
        return jsonify(world_data)
    except Exception as e:
        app.logger.error(f"Error loading world: {str(e)}")
        return jsonify({'error': 'Could not load world state'}), 500

# Initialize data files on startup
initialize_data_files()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
