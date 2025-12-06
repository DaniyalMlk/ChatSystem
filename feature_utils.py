from textblob import TextBlob
# Assuming you have this file/class based on the prompt
# from chat_bot_client import ChatBotClient 

class FeatureManager:
    def __init__(self):
        # Initialize AI Bot (Mocking if file doesn't exist for safety)
        try:
            from chat_bot_client import ChatBotClient
            self.bot = ChatBotClient()
            self.has_bot = True
        except ImportError:
            self.bot = None
            self.has_bot = False
            print("Warning: chat_bot_client.py not found. AI features disabled.")

    def get_sentiment_color(self, text):
        """
        Analyzes text sentiment.
        Returns: ('color_tag', 'hex_code')
        """
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity # Range -1.0 to 1.0

        if polarity > 0.1:
            return 'positive', '#00AA00' # Green
        elif polarity < -0.1:
            return 'negative', '#FF0000' # Red
        else:
            return 'neutral', '#000000' # Black

    def is_bot_command(self, text):
        return text.strip().startswith("@bot")

    def get_bot_response(self, text):
        if not self.has_bot:
            return "AI Bot is not installed."
        
        # Strip the @bot tag
        prompt = text.replace("@bot", "", 1).strip()
        return self.bot.chat(prompt)