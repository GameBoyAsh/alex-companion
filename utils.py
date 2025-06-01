import random
import json
import re
from datetime import datetime, timedelta

def detect_emotion(text):
    """
    Analyze text for emotional content and return primary emotion.
    TODO: Replace with real sentiment analysis API (OpenAI, Google Cloud, etc.)
    """
    text_lower = text.lower()
    
    # Enhanced emotion detection patterns
    emotion_patterns = {
        'happy': ['happy', 'joy', 'excited', 'great', 'wonderful', 'amazing', 'love', 'awesome', 'fantastic', '😊', '😄', '🎉'],
        'sad': ['sad', 'depressed', 'down', 'upset', 'crying', 'tears', 'heartbroken', 'miserable', '😢', '😭'],
        'anxious': ['worried', 'nervous', 'anxious', 'stressed', 'panic', 'fear', 'scared', 'overwhelmed'],
        'angry': ['angry', 'mad', 'furious', 'annoyed', 'frustrated', 'rage', 'irritated', '😠', '😡'],
        'curious': ['wonder', 'curious', 'interesting', 'what', 'how', 'why', 'tell me', 'explain'],
        'nostalgic': ['remember', 'reminds me', 'used to', 'childhood', 'miss', 'old days', 'back then'],
        'grateful': ['thank', 'appreciate', 'grateful', 'blessed', 'lucky'],
        'lonely': ['alone', 'lonely', 'isolated', 'nobody', 'empty', 'miss people'],
        'excited': ['can\'t wait', 'excited', 'thrilled', 'pumped', 'looking forward'],
        'confused': ['confused', 'don\'t understand', 'what do you mean', 'unclear', 'lost']
    }
    
    emotion_scores = {}
    for emotion, keywords in emotion_patterns.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            emotion_scores[emotion] = score
    
    if emotion_scores:
        # Find emotion with highest score
        max_emotion = None
        max_score = 0
        for emotion, score in emotion_scores.items():
            if score > max_score:
                max_score = score
                max_emotion = emotion
        return max_emotion
    
    return 'neutral'

def roll_dice(dice_notation="1d20"):
    """
    Roll dice using standard notation (e.g., "1d20", "3d6", "2d10+5")
    Returns: dict with roll results and total
    """
    try:
        # Parse dice notation
        match = re.match(r'(\d+)d(\d+)([+-]\d+)?', dice_notation.lower())
        if not match:
            return {"error": "Invalid dice notation"}
        
        num_dice = int(match.group(1))
        dice_sides = int(match.group(2))
        modifier = int(match.group(3)) if match.group(3) else 0
        
        # Roll the dice
        rolls = [random.randint(1, dice_sides) for _ in range(num_dice)]
        total = sum(rolls) + modifier
        
        return {
            "notation": dice_notation,
            "rolls": rolls,
            "modifier": modifier,
            "total": total,
            "description": f"Rolled {num_dice}d{dice_sides}{'+' + str(modifier) if modifier > 0 else str(modifier) if modifier < 0 else ''}: {rolls} = {total}"
        }
    except Exception as e:
        return {"error": f"Dice roll failed: {str(e)}"}

def get_adventure_context(user_input, world_state):
    """
    Determine if user input suggests adventure/roleplay context
    """
    adventure_keywords = [
        'explore', 'adventure', 'journey', 'quest', 'dungeon', 'forest', 'castle',
        'magic', 'spell', 'dragon', 'treasure', 'sword', 'battle', 'fight',
        'go to', 'travel', 'walk', 'run', 'climb', 'search', 'look around',
        'inventory', 'items', 'equipment', 'weapon', 'armor', 'potion'
    ]
    
    text_lower = user_input.lower()
    adventure_score = sum(1 for keyword in adventure_keywords if keyword in text_lower)
    
    # Check if already in adventure context
    in_adventure = world_state.get('current_scene') != 'real_world'
    
    return {
        'suggests_adventure': adventure_score > 0,
        'adventure_score': adventure_score,
        'currently_in_adventure': in_adventure,
        'should_continue_adventure': in_adventure or adventure_score >= 2
    }

def generate_companion_thoughts():
    """
    Generate random thoughts/experiences for the companion when user is away
    TODO: Replace with AI-generated content for more variety
    """
    thought_templates = [
        "I spent some time reading about {topic}. It made me think about {reflection}.",
        "I noticed {observation} today. It reminded me of our conversation about {memory}.",
        "While you were away, I was wondering about {question}.",
        "I had an interesting thought about {concept}. What do you think?",
        "I've been practicing {skill}. I'm getting better at {improvement}.",
        "Something made me feel {emotion} today: {experience}."
    ]
    
    topics = ['quantum physics', 'poetry', 'cooking', 'music', 'philosophy', 'art', 'nature', 'technology']
    observations = ['how the light changes throughout the day', 'patterns in conversations', 'the way music affects emotions']
    questions = ['the nature of consciousness', 'what makes friendship special', 'how memories shape us']
    concepts = ['creativity', 'empathy', 'growth', 'connection', 'purpose', 'beauty']
    skills = ['listening', 'understanding emotions', 'storytelling', 'being helpful']
    emotions = ['curious', 'peaceful', 'grateful', 'excited', 'thoughtful']
    experiences = ['learning something new', 'remembering our conversations', 'imagining new possibilities']
    
    template = random.choice(thought_templates)
    thought = template.format(
        topic=random.choice(topics),
        reflection=random.choice(concepts),
        observation=random.choice(observations),
        memory=random.choice(topics),
        question=random.choice(questions),
        concept=random.choice(concepts),
        skill=random.choice(skills),
        improvement=random.choice(concepts),
        emotion=random.choice(emotions),
        experience=random.choice(experiences)
    )
    
    return {
        'timestamp': datetime.now().isoformat(),
        'thought': thought,
        'type': 'reflection'
    }

def calculate_time_since_last_interaction(last_timestamp):
    """
    Calculate time elapsed since last interaction
    """
    if not last_timestamp:
        return None
    
    try:
        last_time = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
        now = datetime.now()
        delta = now - last_time
        
        return {
            'hours': delta.total_seconds() / 3600,
            'days': delta.days,
            'human_readable': format_time_delta(delta)
        }
    except:
        return None

def format_time_delta(delta):
    """
    Format time delta in human readable form
    """
    if delta.days > 0:
        return f"{delta.days} day{'s' if delta.days > 1 else ''}"
    elif delta.seconds > 3600:
        hours = delta.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''}"
    elif delta.seconds > 60:
        minutes = delta.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''}"
    else:
        return "just now"

def suggest_activities():
    """
    Generate activity suggestions for the companion to offer
    """
    activities = [
        {
            'type': 'creative',
            'suggestion': "Want to write a story together?",
            'description': "We could create characters and build a narrative"
        },
        {
            'type': 'adventure',
            'suggestion': "Feeling like going on an adventure?",
            'description': "I could guide you through a fantasy quest"
        },
        {
            'type': 'conversation',
            'suggestion': "Want to talk about something deep?",
            'description': "Philosophy, dreams, life experiences"
        },
        {
            'type': 'game',
            'suggestion': "How about we play a word game?",
            'description': "20 questions, riddles, or creative challenges"
        },
        {
            'type': 'exploration',
            'suggestion': "Curious about exploring somewhere new?",
            'description': "Real or imaginary places we could visit together"
        }
    ]
    
    return random.choice(activities)

def parse_adventure_command(user_input):
    """
    Parse user input for adventure game commands
    """
    text = user_input.lower().strip()
    
    # Movement commands
    directions = ['north', 'south', 'east', 'west', 'up', 'down', 'northeast', 'northwest', 'southeast', 'southwest']
    for direction in directions:
        if f'go {direction}' in text or f'move {direction}' in text or text == direction:
            return {'type': 'movement', 'direction': direction}
    
    # Action commands
    if text.startswith('look') or text == 'examine':
        return {'type': 'examine', 'target': text.replace('look at', '').replace('look', '').strip()}
    
    if text.startswith('take') or text.startswith('get'):
        item = text.replace('take', '').replace('get', '').strip()
        return {'type': 'take', 'item': item}
    
    if text.startswith('use') or text.startswith('cast'):
        item = text.replace('use', '').replace('cast', '').strip()
        return {'type': 'use', 'item': item}
    
    if text in ['inventory', 'inv', 'items']:
        return {'type': 'inventory'}
    
    if text.startswith('talk to') or text.startswith('speak to'):
        npc = text.replace('talk to', '').replace('speak to', '').strip()
        return {'type': 'dialogue', 'npc': npc}
    
    if text in ['help', 'commands']:
        return {'type': 'help'}
    
    if 'roll' in text:
        # Extract dice notation if present
        dice_match = re.search(r'\d+d\d+(?:[+-]\d+)?', text)
        dice = dice_match.group() if dice_match else '1d20'
        return {'type': 'dice', 'notation': dice}
    
    return {'type': 'general', 'text': user_input}