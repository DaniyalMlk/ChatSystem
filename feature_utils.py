"""
feature_utils.py - Feature Manager for AI Bot and Sentiment Analysis
Handles chatbot integration and sentiment analysis of messages
"""

from textblob import TextBlob
import threading

class FeatureManager:
    """Manages AI chatbot and sentiment analysis features"""
    
    def __init__(self, chatbot_client=None):
        """
        Initialize feature manager
        
        Args:
            chatbot_client: Instance of ChatBotClient (optional)
        """
        self.chatbot_client = chatbot_client
        self.sentiment_enabled = True
        self.chatbot_enabled = True
    
    def process_message_for_bot(self, message, callback):
        """
        Check if message is for bot and process it
        
        Args:
            message: The message text
            callback: Function to call with bot response
            
        Returns:
            True if message was for bot, False otherwise
        """
        if not self.chatbot_enabled:
            return False
            
        if message.strip().startswith("@bot"):
            # Extract message after @bot
            bot_query = message.strip()[4:].strip()
            
            if not bot_query:
                callback("Bot: Please provide a message after @bot")
                return True
            
            # Process in separate thread to avoid blocking
            thread = threading.Thread(
                target=self._get_bot_response,
                args=(bot_query, callback)
            )
            thread.daemon = True
            thread.start()
            
            return True
        
        return False
    
    def _get_bot_response(self, query, callback):
        """
        Get response from chatbot (runs in separate thread)
        
        Args:
            query: User's query
            callback: Function to call with response
        """
        try:
            if self.chatbot_client:
                response = self.chatbot_client.chat(query)
                callback(f"Bot: {response}")
            else:
                callback(f"Bot: I received your message '{query}' but I'm not connected to an AI service.")
        except Exception as e:
            callback(f"Bot Error: {str(e)}")
    
    def analyze_sentiment(self, message):
        """
        Analyze sentiment of a message
        
        Args:
            message: The message text
            
        Returns:
            Dict with sentiment info: {'polarity': float, 'color': str, 'label': str}
        """
        if not self.sentiment_enabled:
            return {
                'polarity': 0.0,
                'color': 'black',
                'label': 'neutral'
            }
        
        try:
            # Use TextBlob for sentiment analysis
            blob = TextBlob(message)
            polarity = blob.sentiment.polarity
            
            # Classify sentiment
            if polarity > 0.1:
                color = 'green'
                label = 'positive'
            elif polarity < -0.1:
                color = 'red'
                label = 'negative'
            else:
                color = 'black'
                label = 'neutral'
            
            return {
                'polarity': polarity,
                'color': color,
                'label': label
            }
        except Exception as e:
            print(f"[WARN] Sentiment analysis error: {e}")
            return {
                'polarity': 0.0,
                'color': 'black',
                'label': 'neutral'
            }
    
    def get_sentiment_color(self, message):
        """
        Quick method to get just the color for a message
        
        Args:
            message: The message text
            
        Returns:
            Color string ('green', 'red', or 'black')
        """
        return self.analyze_sentiment(message)['color']
    
    def toggle_sentiment(self, enabled):
        """Enable or disable sentiment analysis"""
        self.sentiment_enabled = enabled
    
    def toggle_chatbot(self, enabled):
        """Enable or disable chatbot"""
        self.chatbot_enabled = enabled


class DummyChatBotClient:
    """Dummy chatbot for testing when real chatbot is not available"""
    
    def chat(self, message):
        """
        Simple rule-based response system
        
        Args:
            message: User's message
            
        Returns:
            Bot's response
        """
        message_lower = message.lower()
        
        # Simple keyword-based responses
        if 'hello' in message_lower or 'hi' in message_lower:
            return "Hello! How can I help you today?"
        elif 'how are you' in message_lower:
            return "I'm doing great, thank you for asking!"
        elif 'bye' in message_lower or 'goodbye' in message_lower:
            return "Goodbye! Have a great day!"
        elif 'help' in message_lower:
            return "I'm a simple chatbot. Try asking me about the weather, telling me hello, or asking how I am!"
        elif 'weather' in message_lower:
            return "I'm not connected to weather services, but I hope it's nice where you are!"
        elif 'name' in message_lower:
            return "I'm ChatBot, your friendly AI assistant!"
        elif 'thank' in message_lower:
            return "You're welcome!"
        elif '?' in message:
            return "That's an interesting question! I'm a simple bot, so I might not have the best answer."
        else:
            return f"I heard you say: '{message}'. I'm a simple bot, so I can only respond to basic greetings!"