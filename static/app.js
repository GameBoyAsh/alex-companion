class AICompanionApp {
    constructor() {
        this.isListening = false;
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.lastResponse = '';
        this.adventureMode = false;
        this.conversationHistory = [];
        
        this.initializeElements();
        this.initializeSpeechRecognition();
        this.bindEvents();
        this.loadConversationHistory();
        this.updateAdventurePanel();
    }

    initializeElements() {
        // Chat elements
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.micButton = document.getElementById('micButton');
        this.speakButton = document.getElementById('speakButton');
        this.voiceStatus = document.getElementById('voiceStatus');
        
        // Mode and status elements
        this.adventureToggle = document.getElementById('adventureToggle');
        this.companionEmotion = document.getElementById('companionEmotion');
        this.adventurePanel = document.getElementById('adventurePanel');
        
        // Adventure panel elements
        this.currentLocation = document.getElementById('currentLocation');
        this.playerHealth = document.getElementById('playerHealth');
        this.playerLevel = document.getElementById('playerLevel');
        this.inventoryList = document.getElementById('inventoryList');
        
        // History and settings
        this.conversationHistoryEl = document.getElementById('conversationHistory');
        this.clearHistoryBtn = document.getElementById('clearHistoryBtn');
        this.autoSpeakToggle = document.getElementById('autoSpeakToggle');
        this.soundEffectsToggle = document.getElementById('soundEffectsToggle');
        this.voiceSpeedRange = document.getElementById('voiceSpeedRange');
        
        // Loading modal
        this.loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    }

    initializeSpeechRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'en-US';
            
            this.recognition.onstart = () => {
                this.isListening = true;
                this.micButton.classList.add('recording');
                this.voiceStatus.style.display = 'block';
                this.playSound('start');
            };
            
            this.recognition.onend = () => {
                this.isListening = false;
                this.micButton.classList.remove('recording');
                this.voiceStatus.style.display = 'none';
            };
            
            this.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                this.messageInput.value = transcript;
                this.sendMessage();
                this.playSound('success');
            };
            
            this.recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                this.isListening = false;
                this.micButton.classList.remove('recording');
                this.voiceStatus.style.display = 'none';
                this.showError('Voice recognition failed. Please try again.');
                this.playSound('error');
            };
        } else {
            this.micButton.disabled = true;
            this.micButton.title = 'Speech recognition not supported';
        }
    }

    bindEvents() {
        // Send message events
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Voice input
        this.micButton.addEventListener('click', () => this.toggleVoiceInput());
        
        // Voice output
        this.speakButton.addEventListener('click', () => this.speakLastResponse());
        
        // Adventure mode toggle
        this.adventureToggle.addEventListener('change', (e) => {
            this.adventureMode = e.target.checked;
            this.toggleAdventureMode();
        });
        
        // Clear history
        this.clearHistoryBtn.addEventListener('click', () => this.clearHistory());
        
        // Settings
        this.voiceSpeedRange.addEventListener('input', (e) => {
            // Voice speed will be applied when speaking
        });
        
        // Auto-scroll chat to bottom when new messages arrive
        const observer = new MutationObserver(() => {
            this.scrollToBottom();
        });
        observer.observe(this.chatMessages, { childList: true });
    }

    toggleVoiceInput() {
        if (!this.recognition) return;
        
        if (this.isListening) {
            this.recognition.stop();
        } else {
            this.recognition.start();
        }
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // Clear input and show user message
        this.messageInput.value = '';
        this.addMessage(message, 'user');
        
        // Show loading state
        this.sendButton.disabled = true;
        this.sendButton.classList.add('loading');
        
        try {
            // Send to backend
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    adventure_mode: this.adventureMode
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Add AI response
            this.addMessage(data.response, 'ai');
            this.lastResponse = data.response;
            
            // Update companion emotion
            this.updateCompanionEmotion(data.companion_emotion);
            
            // Update adventure panel if in adventure mode
            if (this.adventureMode && data.world_state) {
                this.updateWorldState(data.world_state);
            }
            
            // Auto-speak if enabled
            if (this.autoSpeakToggle.checked) {
                this.speakText(data.response);
            }
            
            // Refresh conversation history
            this.loadConversationHistory();
            
            this.playSound('message');
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.showError('Failed to send message. Please try again.');
            this.playSound('error');
        } finally {
            this.sendButton.disabled = false;
            this.sendButton.classList.remove('loading');
        }
    }

    addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message-bubble ${sender}-message`;
        
        const now = new Date();
        const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.innerHTML = `
            <div class="message-content">
                ${sender === 'ai' ? '<i class="fas fa-robot me-2"></i>' : ''}
                ${this.formatMessageText(text)}
            </div>
            <div class="message-time">
                <small class="text-muted">${timeString}</small>
            </div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    formatMessageText(text) {
        // Convert newlines to <br> tags
        return text.replace(/\n/g, '<br>');
    }

    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'message-bubble error ai-message';
        errorDiv.innerHTML = `
            <div class="message-content">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
            </div>
        `;
        this.chatMessages.appendChild(errorDiv);
        this.scrollToBottom();
    }

    scrollToBottom() {
        const chatContainer = document.getElementById('chatContainer');
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    speakLastResponse() {
        if (this.lastResponse) {
            this.speakText(this.lastResponse);
        }
    }

    speakText(text) {
        if (!this.synthesis) return;
        
        // Stop any ongoing speech
        this.synthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = parseFloat(this.voiceSpeedRange.value);
        utterance.pitch = 1;
        utterance.volume = 1;
        
        // Try to use a more natural voice
        const voices = this.synthesis.getVoices();
        const preferredVoice = voices.find(voice => 
            voice.name.includes('Natural') || 
            voice.name.includes('Enhanced') ||
            voice.lang.startsWith('en')
        );
        if (preferredVoice) {
            utterance.voice = preferredVoice;
        }
        
        this.synthesis.speak(utterance);
    }

    updateCompanionEmotion(emotion) {
        this.companionEmotion.textContent = emotion;
        
        // Update emotion icon based on emotion
        const emotionIcons = {
            'happy': 'fas fa-smile text-warning',
            'sad': 'fas fa-frown text-info',
            'angry': 'fas fa-angry text-danger',
            'fearful': 'fas fa-surprise text-secondary',
            'curious': 'fas fa-question text-primary',
            'loving': 'fas fa-heart text-danger',
            'neutral': 'fas fa-meh text-muted'
        };
        
        const emotionIcon = this.companionEmotion.previousElementSibling;
        emotionIcon.className = emotionIcons[emotion] || emotionIcons['neutral'];
    }

    toggleAdventureMode() {
        if (this.adventureMode) {
            this.adventurePanel.style.display = 'block';
            this.addMessage("🏰 Adventure mode activated! You find yourself in a mystical world. Type 'look' to examine your surroundings or 'help' for commands.", 'ai');
            this.updateAdventurePanel();
        } else {
            this.adventurePanel.style.display = 'none';
            this.addMessage("💬 Returning to companion mode. I'm here to chat and listen!", 'ai');
        }
    }

    async updateAdventurePanel() {
        if (!this.adventureMode) return;
        
        try {
            const response = await fetch('/world');
            if (response.ok) {
                const worldData = await response.json();
                this.updateWorldState({
                    current_location: worldData.locations[worldData.current_location].name,
                    inventory: worldData.inventory,
                    health: worldData.player_stats.health,
                    level: worldData.player_stats.level
                });
            }
        } catch (error) {
            console.error('Error loading world state:', error);
        }
    }

    updateWorldState(worldState) {
        if (this.currentLocation) {
            this.currentLocation.textContent = worldState.current_location;
        }
        if (this.playerHealth) {
            this.playerHealth.textContent = `${worldState.health}/100`;
        }
        if (this.playerLevel) {
            this.playerLevel.textContent = worldState.level;
        }
        if (this.inventoryList) {
            this.inventoryList.innerHTML = '';
            worldState.inventory.forEach(item => {
                const badge = document.createElement('span');
                badge.className = 'badge bg-primary me-1 mb-1';
                badge.textContent = item.replace('_', ' ');
                this.inventoryList.appendChild(badge);
            });
            
            if (worldState.inventory.length === 0) {
                this.inventoryList.innerHTML = '<small class="text-muted">Empty</small>';
            }
        }
    }

    async loadConversationHistory() {
        try {
            const response = await fetch('/memory');
            if (response.ok) {
                const memoryData = await response.json();
                this.conversationHistory = memoryData.conversations || [];
                this.displayConversationHistory();
            }
        } catch (error) {
            console.error('Error loading conversation history:', error);
        }
    }

    displayConversationHistory() {
        this.conversationHistoryEl.innerHTML = '';
        
        // Show last 10 conversations
        const recentConversations = this.conversationHistory.slice(-10).reverse();
        
        recentConversations.forEach((conv, index) => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            
            const timestamp = new Date(conv.timestamp);
            const timeString = timestamp.toLocaleString([], { 
                month: 'short', 
                day: 'numeric', 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            
            const emotionBadgeClass = this.getEmotionBadgeClass(conv.detected_emotion);
            
            historyItem.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div class="history-time">${timeString}</div>
                    <div>
                        <span class="badge ${emotionBadgeClass} emotion-badge">${conv.detected_emotion}</span>
                        ${conv.mode === 'adventure' ? '<span class="badge bg-secondary emotion-badge">⚔️</span>' : ''}
                    </div>
                </div>
                <div class="history-preview">
                    <strong>You:</strong> ${conv.user_message.substring(0, 50)}${conv.user_message.length > 50 ? '...' : ''}
                </div>
            `;
            
            historyItem.addEventListener('click', () => {
                this.showConversationDetail(conv);
            });
            
            this.conversationHistoryEl.appendChild(historyItem);
        });
        
        if (recentConversations.length === 0) {
            this.conversationHistoryEl.innerHTML = '<small class="text-muted">No conversations yet</small>';
        }
    }

    getEmotionBadgeClass(emotion) {
        const emotionClasses = {
            'happy': 'bg-warning',
            'sad': 'bg-info',
            'angry': 'bg-danger',
            'fearful': 'bg-secondary',
            'curious': 'bg-primary',
            'loving': 'bg-danger',
            'neutral': 'bg-secondary'
        };
        return emotionClasses[emotion] || 'bg-secondary';
    }

    showConversationDetail(conversation) {
        // Create a modal or tooltip showing the full conversation
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Conversation Detail</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p><strong>Time:</strong> ${new Date(conversation.timestamp).toLocaleString()}</p>
                        <p><strong>Mode:</strong> ${conversation.mode}</p>
                        <p><strong>Emotion:</strong> ${conversation.detected_emotion}</p>
                        <hr>
                        <p><strong>You said:</strong></p>
                        <p class="text-info">${conversation.user_message}</p>
                        <p><strong>AI responded:</strong></p>
                        <p class="text-success">${conversation.ai_response}</p>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
        
        // Clean up modal after hiding
        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
    }

    clearHistory() {
        if (confirm('Are you sure you want to clear all conversation history?')) {
            // Note: This would need a backend endpoint to actually clear the history
            this.conversationHistory = [];
            this.displayConversationHistory();
            this.chatMessages.innerHTML = `
                <div class="message-bubble ai-message">
                    <div class="message-content">
                        <i class="fas fa-robot me-2"></i>
                        History cleared! Let's start fresh. How can I help you today?
                    </div>
                    <div class="message-time">
                        <small class="text-muted">Just now</small>
                    </div>
                </div>
            `;
        }
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
            
            // Configure sound based on type
            switch (type) {
                case 'start':
                    oscillator.frequency.setValueAtTime(440, audioContext.currentTime);
                    oscillator.frequency.exponentialRampToValueAtTime(880, audioContext.currentTime + 0.1);
                    break;
                case 'success':
                    oscillator.frequency.setValueAtTime(523, audioContext.currentTime);
                    oscillator.frequency.exponentialRampToValueAtTime(659, audioContext.currentTime + 0.1);
                    break;
                case 'error':
                    oscillator.frequency.setValueAtTime(200, audioContext.currentTime);
                    oscillator.frequency.exponentialRampToValueAtTime(100, audioContext.currentTime + 0.2);
                    break;
                case 'message':
                    oscillator.frequency.setValueAtTime(600, audioContext.currentTime);
                    break;
                default:
                    oscillator.frequency.setValueAtTime(440, audioContext.currentTime);
            }
            
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.2);
        } catch (error) {
            // Sound effects not available
            console.log('Sound effects not available:', error);
        }
    }
}

// Initialize the app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new AICompanionApp();
});

// Handle page visibility change to pause/resume speech
document.addEventListener('visibilitychange', () => {
    if (document.hidden && window.speechSynthesis) {
        window.speechSynthesis.pause();
    } else if (window.speechSynthesis) {
        window.speechSynthesis.resume();
    }
});
