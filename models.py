import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Text, JSON

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_input = db.Column(Text, nullable=False)
    ai_response = db.Column(Text, nullable=False)
    detected_emotion = db.Column(db.String(50), nullable=True)
    adventure_active = db.Column(db.Boolean, default=False)
    location_name = db.Column(db.String(200), nullable=True)
    relationship_depth = db.Column(db.Integer, default=1)
    context_data = db.Column(JSON, nullable=True)
    
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

class CompanionPersona(db.Model):
    __tablename__ = 'companion_persona'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), default='Alex')
    core_traits = db.Column(JSON, nullable=False)
    communication_style = db.Column(JSON, nullable=False)
    interests = db.Column(JSON, nullable=False)
    learned_preferences = db.Column(JSON, default=dict)
    conversations_count = db.Column(db.Integer, default=0)
    adaptations_made = db.Column(JSON, default=list)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'core_traits': self.core_traits,
            'communication_style': self.communication_style,
            'interests': self.interests,
            'learned_preferences': self.learned_preferences,
            'personality_evolution': {
                'conversations_count': self.conversations_count,
                'adaptations_made': self.adaptations_made
            },
            'last_updated': self.last_updated.isoformat()
        }

class WorldState(db.Model):
    __tablename__ = 'world_state'
    
    id = db.Column(db.Integer, primary_key=True)
    current_scene = db.Column(db.String(100), default='real_world')
    adventure_active = db.Column(db.Boolean, default=False)
    current_location = db.Column(JSON, nullable=False)
    inventory = db.Column(JSON, default=list)
    companions = db.Column(JSON, default=list)
    story_state = db.Column(JSON, default=dict)
    game_mechanics = db.Column(JSON, default=dict)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'current_scene': self.current_scene,
            'adventure_active': self.adventure_active,
            'location': self.current_location,
            'inventory': self.inventory,
            'companions': self.companions,
            'story_state': self.story_state,
            'game_mechanics': self.game_mechanics,
            'last_updated': self.last_updated.isoformat()
        }

class CompanionThoughts(db.Model):
    __tablename__ = 'companion_thoughts'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    thought_text = db.Column(Text, nullable=False)
    thought_type = db.Column(db.String(50), default='reflection')
    emotional_context = db.Column(db.String(50), nullable=True)
    triggered_by = db.Column(db.String(200), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'thought': self.thought_text,
            'type': self.thought_type,
            'emotional_context': self.emotional_context,
            'triggered_by': self.triggered_by
        }

class EmotionalPattern(db.Model):
    __tablename__ = 'emotional_patterns'
    
    id = db.Column(db.Integer, primary_key=True)
    emotion = db.Column(db.String(50), nullable=False)
    intensity = db.Column(db.Float, default=1.0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=True)
    context = db.Column(db.String(200), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'emotion': self.emotion,
            'intensity': self.intensity,
            'timestamp': self.timestamp.isoformat(),
            'conversation_id': self.conversation_id,
            'context': self.context
        }

class UserPreferences(db.Model):
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    communication_style = db.Column(db.String(50), default='friendly')
    favorite_topics = db.Column(JSON, default=list)
    activity_preferences = db.Column(JSON, default=list)
    voice_settings = db.Column(JSON, default=dict)
    ui_preferences = db.Column(JSON, default=dict)
    last_interaction = db.Column(db.DateTime, nullable=True)
    relationship_depth = db.Column(db.Integer, default=1)
    
    def to_dict(self):
        return {
            'id': self.id,
            'communication_style': self.communication_style,
            'favorite_topics': self.favorite_topics,
            'activity_preferences': self.activity_preferences,
            'voice_settings': self.voice_settings,
            'ui_preferences': self.ui_preferences,
            'last_interaction': self.last_interaction.isoformat() if self.last_interaction else None,
            'relationship_depth': self.relationship_depth
        }