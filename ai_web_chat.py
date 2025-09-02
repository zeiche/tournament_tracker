#!/usr/bin/env python3
"""
Web-based AI Chat Interface for Tournament Tracker
Provides a browser-based chat with the AI assistant
"""

from flask import Flask, render_template_string, request, jsonify, session
import os
import sys
import uuid
import logging
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_service import get_ai_service, ChannelType

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ai_web_chat')

# Initialize AI service
ai_service = get_ai_service()

# HTML template with modern chat interface
CHAT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tournament Tracker AI Assistant</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .chat-container {
            width: 90%;
            max-width: 800px;
            height: 90vh;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .chat-header h1 {
            font-size: 1.5rem;
            font-weight: 600;
        }
        
        .mode-selector {
            display: flex;
            gap: 10px;
        }
        
        .mode-btn {
            padding: 8px 16px;
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 20px;
            color: white;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .mode-btn:hover {
            background: rgba(255,255,255,0.3);
        }
        
        .mode-btn.active {
            background: white;
            color: #667eea;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f7f7f8;
        }
        
        .message {
            margin-bottom: 20px;
            display: flex;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .message.user {
            justify-content: flex-end;
        }
        
        .message-content {
            max-width: 70%;
            padding: 12px 18px;
            border-radius: 18px;
            word-wrap: break-word;
        }
        
        .message.user .message-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .message.ai .message-content {
            background: white;
            color: #333;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .message-time {
            font-size: 0.75rem;
            color: #999;
            margin-top: 5px;
        }
        
        .typing-indicator {
            display: none;
            padding: 12px 18px;
            background: white;
            border-radius: 18px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            width: fit-content;
        }
        
        .typing-indicator.show {
            display: block;
        }
        
        .typing-indicator span {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #999;
            margin: 0 2px;
            animation: typing 1.4s infinite;
        }
        
        .typing-indicator span:nth-child(2) {
            animation-delay: 0.2s;
        }
        
        .typing-indicator span:nth-child(3) {
            animation-delay: 0.4s;
        }
        
        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
            }
            30% {
                transform: translateY(-10px);
            }
        }
        
        .chat-input {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }
        
        .input-container {
            display: flex;
            gap: 10px;
        }
        
        #message-input {
            flex: 1;
            padding: 12px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 1rem;
            outline: none;
            transition: border-color 0.3s;
        }
        
        #message-input:focus {
            border-color: #667eea;
        }
        
        #send-btn {
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 1rem;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        #send-btn:hover {
            transform: scale(1.05);
        }
        
        #send-btn:active {
            transform: scale(0.95);
        }
        
        .quick-actions {
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }
        
        .quick-action {
            padding: 6px 12px;
            background: #f0f0f0;
            border: 1px solid #ddd;
            border-radius: 15px;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .quick-action:hover {
            background: #e0e0e0;
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>🎮 Tournament Tracker AI Assistant</h1>
            <div class="mode-selector">
                <button class="mode-btn active" data-mode="general">General</button>
                <button class="mode-btn" data-mode="stats">Stats</button>
                <button class="mode-btn" data-mode="developer">Dev</button>
            </div>
        </div>
        
        <div class="chat-messages" id="chat-messages">
            <div class="message ai">
                <div>
                    <div class="message-content">
                        Hello! I'm your AI assistant for the Tournament Tracker. I can help with tournament statistics, organization data, or just chat. What would you like to know?
                    </div>
                    <div class="message-time">{{ current_time }}</div>
                </div>
            </div>
        </div>
        
        <div class="typing-indicator" id="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
        
        <div class="chat-input">
            <div class="quick-actions">
                <button class="quick-action" onclick="sendQuickMessage('Show me the top organizations')">Top Orgs</button>
                <button class="quick-action" onclick="sendQuickMessage('What are the tournament statistics?')">Stats</button>
                <button class="quick-action" onclick="sendQuickMessage('Show me a heat map')">Heat Map</button>
                <button class="quick-action" onclick="sendQuickMessage('Tell me about the biggest tournaments')">Big Events</button>
            </div>
            <div class="input-container">
                <input type="text" id="message-input" placeholder="Type your message..." autofocus>
                <button id="send-btn">Send</button>
            </div>
        </div>
    </div>
    
    <script>
        let currentMode = 'general';
        
        // Mode selector
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                currentMode = this.dataset.mode;
            });
        });
        
        // Send message
        async function sendMessage() {
            const input = document.getElementById('message-input');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message
            addMessage(message, 'user');
            input.value = '';
            
            // Show typing indicator
            showTyping();
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        mode: currentMode
                    })
                });
                
                const data = await response.json();
                hideTyping();
                addMessage(data.response, 'ai');
                
            } catch (error) {
                hideTyping();
                addMessage('Sorry, I encountered an error. Please try again.', 'ai');
            }
        }
        
        function addMessage(text, sender) {
            const messagesDiv = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            
            const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            
            messageDiv.innerHTML = `
                <div>
                    <div class="message-content">${escapeHtml(text)}</div>
                    <div class="message-time">${time}</div>
                </div>
            `;
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function showTyping() {
            document.getElementById('typing-indicator').classList.add('show');
        }
        
        function hideTyping() {
            document.getElementById('typing-indicator').classList.remove('show');
        }
        
        function sendQuickMessage(message) {
            document.getElementById('message-input').value = message;
            sendMessage();
        }
        
        function escapeHtml(text) {
            const map = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            };
            return text.replace(/[&<>"']/g, m => map[m]);
        }
        
        // Event listeners
        document.getElementById('send-btn').addEventListener('click', sendMessage);
        document.getElementById('message-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Render the chat interface"""
    current_time = datetime.now().strftime('%I:%M %p')
    return render_template_string(CHAT_TEMPLATE, current_time=current_time)

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    data = request.json
    message = data.get('message', '')
    mode = data.get('mode', 'general')
    
    # Get or create session ID
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    # Map mode to ChannelType
    channel_map = {
        'general': ChannelType.WEB,
        'stats': ChannelType.STATS,
        'developer': ChannelType.DEVELOPER
    }
    channel_type = channel_map.get(mode, ChannelType.WEB)
    
    # Get AI response
    context = {
        'session_id': session['session_id'],
        'interface': 'web',
        'mode': mode
    }
    
    response = ai_service.get_response_sync(message, channel_type, context)
    
    logger.info(f"Web chat - User: {message[:50]}... | AI: {response[:50]}...")
    
    return jsonify({
        'response': response,
        'session_id': session['session_id']
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'ai_enabled': ai_service.enabled,
        'model': ai_service.model if ai_service.enabled else None
    })

if __name__ == '__main__':
    port = int(os.getenv('AI_CHAT_PORT', 8082))
    print(f"Starting AI Web Chat on port {port}")
    print(f"AI Service Enabled: {ai_service.enabled}")
    print(f"Access at: http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)