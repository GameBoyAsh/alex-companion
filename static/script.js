class AICompanionApp {
    constructor() {
        this.isListening = false;
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.lastResponse = '';
        this.conversationHistory = [];
        this.companionData = null;
        
        this.initializeElements();
        this.initializeSpeechRecognition();
        this.bindEvents();
        this.loadInitialData();
        this.updateTimestamp();
    }

    initializeElements() {
        // Main UI elements
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.voiceButton = document.getElementById('voiceButton');
        this.speakButton = document.getElementById('speakButton');
        this.voiceStatus = document.getElementById('voiceStatus');
        
        // Status and context elements
        this.companionMood = document.getElementById('companionMood');
        this.adventureContext = document.getElementById('adventureContext');
        this.currentLocation = document.getElementById('currentLocation');
        this.inventoryCount = document.getElementById('inventoryCount');
        this.relationshipDepth = document.getElementById('relationshipDepth');
        this.imageArea = document.getElementById('imageArea');
        
        // Sidebar elements
        this.sidebar = document.getElementById('sidebar');
        this.sidebarMood = document.getElementById('sidebarMood');
        this.conversationCount = document.getElementById('conversationCount');
        this.sidebarDepth = document.getElementById('sidebarDepth');
        this.recentEmotions = document.getElementById('recentEmotions');
        this.advStatus = document.getElementById('advStatus');
        this.advLocation = document.getElementById('advLocation');
        this.advItems = document.getElementById('advItems');
        
        // Settings
        this.autoSpeakToggle = document.getElementById('autoSpeakToggle');
        this.soundEffectsToggle = document.getElementById('soundEffectsToggle');
        this.voiceSpeedRange = document.getElementById('voiceSpeedRange');
        
        // Modals
        this.loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    }

    initializeSpeechRecognition() {
        // Check for browser support
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            
            // Configure recognition
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'en-US';
            this.recognition.maxAlternatives = 1;
            
            // Recognition event handlers
            this.recognition.onstart = () => {
                this.isListening = true;
                this.voiceButton.classList.add('recording');
                this.voiceStatus.style.display = 'block';
                this.playSound('start');
                console.log('Voice recognition started');
            };
            
            this.recognition.onend = () => {
                this.isListening = false;
                this.voiceButton.classList.remove('recording');
                this.voiceStatus.style.display = 'none';
                console.log('Voice recognition ended');
            };
            
            this.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                console.log('Voice transcript:', transcript);
                this.messageInput.value = transcript;
                this.sendMessage();
                this.playSound('success');
            };
            
            this.recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                this.isListening = false;
                this.voiceButton.classList.remove('recording');
                this.voiceStatus.style.display = 'none';
                this.showError(`Voice recognition failed: ${event.error}`);
                this.playSound('error');
            };
        } else {
            // Disable voice button if not supported
            this.voiceButton.disabled = true;
            this.voiceButton.title = 'Speech recognition not supported in this browser';
            console.warn('Speech recognition not supported');
        }
    }

    bindEvents() {
        // Input events
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => this.handleKeyPress(e));
        
        // Voice events
        this.voiceButton.addEventListener('click', () => this.toggleVoice());
        this.speakButton.addEventListener('click', () => this.speakLastResponse());
        
        // Settings events
        this.voiceSpeedRange.addEventListener('input', () => {
            // Speed will be applied when speaking
        });
        
        // Auto-scroll chat when new messages arrive
        const observer = new MutationObserver(() => {
            this.scrollToBottom();
        });
        observer.observe(this.chatMessages, { childList: true });
        
        // Handle page visibility for companion thoughts
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                // User returned to page - could trigger companion thoughts
                this.handleUserReturn();
            }
        });
    }

    async loadInitialData() {
        try {
            // Load memory data to update UI
            const response = await fetch('/memory');
            if (response.ok) {
                const memoryData = await response.json();
                this.updateUIFromMemory(memoryData);
            }
        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    }

    updateUIFromMemory(memoryData) {
        // Update conversation count
        const conversations = memoryData.conversations || [];
        this.conversationCount.textContent = conversations.length;
        this.sidebarDepth.textContent = memoryData.relationship_depth || 1;
        this.relationshipDepth.textContent = memoryData.relationship_depth || 1;
        
        // Update recent emotions
        const emotions = memoryData.emotional_patterns?.dominant_emotions || [];
        this.updateRecentEmotions(emotions.slice(-5)); // Show last 5 emotions
        
        // Update companion mood
        const recentMood = memoryData.emotional_patterns?.recent_mood || 'curious';
        this.updateCompanionMood(recentMood);
    }

    updateRecentEmotions(emotions) {
        this.recentEmotions.innerHTML = '';
        emotions.forEach(emotion => {
            const badge = document.createElement('span');
            badge.className = `badge ${this.getEmotionBadgeClass(emotion)} me-1`;
            badge.textContent = emotion;
            this.recentEmotions.appendChild(badge);
        });
    }

    getEmotionBadgeClass(emotion) {
        const emotionClasses = {
            'happy': 'bg-warning',
            'sad': 'bg-info',
            'angry': 'bg-danger',
            'anxious': 'bg-secondary',
            'excited': 'bg-success',
            'curious': 'bg-primary',
            'nostalgic': 'bg-dark',
            'grateful': 'bg-success',
            'lonely': 'bg-secondary',
            'confused': 'bg-muted',
            'neutral': 'bg-secondary'
        };
        return emotionClasses[emotion] || 'bg-secondary';
    }

    updateCompanionMood(mood) {
        const moodDescriptions = {
            'happy': 'Joyful and energetic',
            'sad': 'Thoughtful and empathetic',
            'curious': 'Curious and ready to chat',
            'excited': 'Excited and enthusiastic',
            'anxious': 'Concerned and supportive',
            'grateful': 'Warm and appreciative',
            'nostalgic': 'Reflective and contemplative',
            'neutral': 'Calm and attentive'
        };
        
        const description = moodDescriptions[mood] || 'Ready to chat';
        this.companionMood.textContent = description;
        this.sidebarMood.textContent = mood;
    }

    handleKeyPress(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.sendMessage();
        }
    }

    toggleVoice() {
        if (!this.recognition) {
            this.showError('Voice recognition not available in this browser');
            return;
        }
        
        if (this.isListening) {
            this.recognition.stop();
        } else {
            try {
                this.recognition.start();
            } catch (error) {
                console.error('Error starting voice recognition:', error);
                this.showError('Failed to start voice recognition');
            }
        }
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // Clear input and add user message
        this.messageInput.value = '';
        this.addMessage(message, 'user');
        
        // Show loading state
        this.setLoadingState(true);
        
        try {
            // Send message to backend
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message
                })
            });
            
            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Add AI response
            this.addMessage(data.response, 'ai', data.emotion);
            this.lastResponse = data.response;
            
            // Update UI with context
            this.updateContextFromResponse(data);
            
            // Auto-speak if enabled
            if (this.autoSpeakToggle.checked) {
                this.speakText(data.response);
            }
            
            // Play notification sound
            this.playSound('message');
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.showError('Failed to send message. Please try again.');
            this.playSound('error');
        } finally {
            this.setLoadingState(false);
        }
    }

    updateContextFromResponse(data) {
        const context = data.context || {};
        
        // Update adventure context
        if (context.adventure_active) {
            this.adventureContext.style.display = 'block';
            this.currentLocation.textContent = context.location?.name || 'Unknown';
            this.inventoryCount.textContent = `${context.inventory?.length || 0} items`;
            this.advStatus.textContent = 'Adventure Active';
            this.advLocation.textContent = context.location?.name || 'Unknown';
            this.advItems.textContent = context.inventory?.length ? context.inventory.join(', ') : 'None';
        } else {
            this.adventureContext.style.display = 'none';
            this.advStatus.textContent = 'Real World';
            this.advLocation.textContent = 'Cozy Space';
        }
        
        // Update relationship depth
        if (context.relationship_depth) {
            this.relationshipDepth.textContent = context.relationship_depth;
            this.sidebarDepth.textContent = context.relationship_depth;
        }
        
        // Update companion mood
        if (data.companion_emotion) {
            this.updateCompanionMood(data.companion_emotion);
        }
        
        // Update conversation count
        this.loadInitialData(); // Refresh sidebar data
    }

    addMessage(text, sender, emotion = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const now = new Date();
        const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        const emotionBadge = emotion ? `<span class="emotion-badge">${emotion}</span>` : '';
        
        messageDiv.innerHTML = `
            <div class="message-content">
                ${sender === 'ai' ? '<i class="fas fa-sparkles me-2"></i>' : ''}
                ${this.formatMessageText(text)}
            </div>
            <div class="message-meta">
                <span>${timeString}</span>
                ${emotionBadge}
            </div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    formatMessageText(text) {
        // Convert newlines to <br> and handle basic formatting
        return text
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'message ai';
        errorDiv.innerHTML = `
            <div class="message-content" style="background: rgba(229, 62, 62, 0.1); border-color: #e53e3e;">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
            </div>
        `;
        this.chatMessages.appendChild(errorDiv);
        this.scrollToBottom();
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    setLoadingState(loading) {
        this.sendButton.disabled = loading;
        if (loading) {
            this.loadingModal.show();
        } else {
            this.loadingModal.hide();
        }
    }

    speakLastResponse() {
        if (this.lastResponse) {
            this.speakText(this.lastResponse);
        }
    }

    speakText(text) {
        if (!this.synthesis) {
            console.warn('Speech synthesis not supported');
            return;
        }
        
        // Stop any ongoing speech
        this.synthesis.cancel();
        
        // Create utterance
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = parseFloat(this.voiceSpeedRange.value);
        utterance.pitch = 1;
        utterance.volume = 0.8;
        
        // Try to select a natural voice
        const voices = this.synthesis.getVoices();
        const preferredVoice = voices.find(voice => 
            voice.name.includes('Natural') || 
            voice.name.includes('Enhanced') ||
            (voice.lang.startsWith('en') && voice.name.includes('Google'))
        );
        
        if (preferredVoice) {
            utterance.voice = preferredVoice;
        }
        
        // Speak the text
        this.synthesis.speak(utterance);
    }

    playSound(type) {
        if (!this.soundEffectsToggle.checked) return;
        
        // Create audio context for sound effects
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            // Different frequencies for different sound types
            const frequencies = {
                'start': 440,
                'success': 523,
                'message': 349,
                'error': 220
            };
            
            oscillator.frequency.value = frequencies[type] || 440;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
        } catch (error) {
            console.warn('Could not play sound effect:', error);
        }
    }

    updateTimestamp() {
        const initialTime = document.getElementById('initialTime');
        if (initialTime) {
            const now = new Date();
            initialTime.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
    }

    handleUserReturn() {
        // Could trigger special companion responses when user returns
        console.log('User returned to page');
    }
}

// Global functions for HTML onclick handlers
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
}

function suggestActivity() {
    // Trigger activity suggestion
    const app = window.companionApp;
    if (app) {
        app.messageInput.value = "Can you suggest something fun we could do together?";
        app.sendMessage();
    }
}

function rollDice() {
    // Trigger dice roll
    fetch('/adventure', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            action: 'roll_dice',
            dice: '1d20'
        })
    })
    .then(response => response.json())
    .then(data => {
        const app = window.companionApp;
        if (app && data.dice_result) {
            app.addMessage(`🎲 ${data.dice_result.description}`, 'ai', 'excited');
        }
    })
    .catch(error => {
        console.error('Error rolling dice:', error);
    });
}

function showMemory() {
    // Show memory/conversation history
    fetch('/memory')
    .then(response => response.json())
    .then(data => {
        const conversations = data.conversations || [];
        const recentCount = Math.min(conversations.length, 5);
        const app = window.companionApp;
        if (app) {
            app.addMessage(`I remember our last ${recentCount} conversations. We've talked ${conversations.length} times total, and our relationship depth is ${data.relationship_depth || 1}.`, 'ai', 'nostalgic');
        }
    })
    .catch(error => {
        console.error('Error loading memory:', error);
    });
}

function clearAllData() {
    if (confirm('Are you sure you want to clear all conversation data? This cannot be undone.')) {
        // This would need a backend endpoint to clear data
        alert('Data clearing feature needs to be implemented in the backend.');
    }
}

// Initialize the app when page loads
document.addEventListener('DOMContentLoaded', function() {
    window.companionApp = new AICompanionApp();
    console.log('AI Companion App initialized');
});

// Global function for HTML onkeypress
function handleKeyPress(event) {
    if (window.companionApp) {
        window.companionApp.handleKeyPress(event);
    }
}