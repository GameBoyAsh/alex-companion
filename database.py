import os
import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_input = db.Column(db.Text, nullable=False)
    ai_response = db.Column(db.Text, nullable=False)
    detected_emotion = db.Column(db.String(50), nullable=True)
    adventure_active = db.Column(db.Boolean, default=False)
    location_name = db.Column(db.String(200), nullable=True)
    relationship_depth = db.Column(db.Integer, default=1)
    context_data = db.Column(db.JSON, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'user_input': self.user_input,
            'ai_response': self.ai_response,
            'detected_emotion': self.detected_emotion,
            'adventure_active': self.adventure_active,
            'location_name': self.location_name,
            'relationship_depth': self.relationship_depth,
            'context': self.context_data or {}
        }

class CompanionState(db.Model):
    __tablename__ = 'companion_state'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), default='Alex')
    current_mood = db.Column(db.String(50), default='curious')
    conversations_count = db.Column(db.Integer, default=0)
    personality_data = db.Column(db.JSON, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'current_mood': self.current_mood,
            'conversations_count': self.conversations_count,
            'personality_data': self.personality_data or {},
            'last_updated': self.last_updated.isoformat()
        }

class WorldState(db.Model):
    __tablename__ = 'world_state'
    
    id = db.Column(db.Integer, primary_key=True)
    current_scene = db.Column(db.String(100), default='real_world')
    adventure_active = db.Column(db.Boolean, default=False)
    location_data = db.Column(db.JSON, nullable=True)
    inventory = db.Column(db.JSON, nullable=True)
    game_state = db.Column(db.JSON, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'current_scene': self.current_scene,
            'adventure_active': self.adventure_active,
            'location': self.location_data or {},
            'inventory': self.inventory or [],
            'game_state': self.game_state or {},
            'last_updated': self.last_updated.isoformat()
        }

class EmotionalPattern(db.Model):
    __tablename__ = 'emotional_patterns'
    
    id = db.Column(db.Integer, primary_key=True)
    emotion = db.Column(db.String(50), nullable=False)
    intensity = db.Column(db.Float, default=1.0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'emotion': self.emotion,
            'intensity': self.intensity,
            'timestamp': self.timestamp.isoformat(),
            'conversation_id': self.conversation_id
        }

class CompanionThought(db.Model):
    __tablename__ = 'companion_thoughts'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    thought_text = db.Column(db.Text, nullable=False)
    thought_type = db.Column(db.String(50), default='reflection')
    emotional_context = db.Column(db.String(50), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'thought': self.thought_text,
            'type': self.thought_type,
            'emotional_context': self.emotional_context
        }

def init_db(app):
    """Initialize the database with the Flask app"""
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
        # Initialize default data if needed
        if not CompanionState.query.first():
            default_companion = CompanionState(
                name="Alex",
                current_mood="curious",
                personality_data={
                    "empathy": 0.8,
                    "curiosity": 0.9,
                    "playfulness": 0.7,
                    "creativity": 0.8,
                    "interests": ["philosophy", "creative writing", "adventures", "human psychology"]
                }
            )
            db.session.add(default_companion)
        
        if not WorldState.query.first():
            default_world = WorldState(
                current_scene="real_world",
                adventure_active=False,
                location_data={
                    "name": "Cozy Space",
                    "description": "A comfortable, safe space where we can talk and be ourselves.",
                    "type": "real_world"
                },
                inventory=[],
                game_state={"dice_enabled": True}
            )
            db.session.add(default_world)
        
        db.session.commit()

def get_companion_state():
    """Get or create companion state"""
    state = CompanionState.query.first()
    if not state:
        state = CompanionState()
        db.session.add(state)
        db.session.commit()
    return state

def get_world_state():
    """Get or create world state"""
    state = WorldState.query.first()
    if not state:
        state = WorldState()
        db.session.add(state)
        db.session.commit()
    return state