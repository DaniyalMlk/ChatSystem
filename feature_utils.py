import requests
from io import BytesIO
from PIL import Image, ImageTk
from chat_bot_client import ChatBotClient
try:
    from textblob import TextBlob
except ImportError:
    TextBlob = None

class FeatureManager:
    def __init__(self):
        # Feature 1: Chatbot
        try:
            self.ai_bot = ChatBotClient()
            print("AI Chatbot connected.")
        except:
            print("AI Chatbot not connected (Server off?).")
            self.ai_bot = None

    def process_ai_command(self, user_input):
        """
        Returns (Text_Response, Image_Object)
        """
        # 1. Image Generation: /pic description
        if user_input.startswith("/pic "):
            prompt = user_input.replace("/pic ", "").strip()
            return "Generating image...", self.generate_image(prompt)
        
        # 2. Chatbot: @bot message
        elif user_input.startswith("@bot "):
            prompt = user_input.replace("@bot ", "").strip()
            if self.ai_bot:
                try:
                    resp = self.ai_bot.chat(prompt)
                    return f"[AI]: {resp}", None
                except Exception as e:
                    return f"AI Error: {e}", None
            else:
                return "AI not available.", None
        
        return None, None

    def generate_image(self, prompt):
        """
        Uses pollinations.ai to generate an image from text.
        Returns a Tkinter-compatible Image object.
        """
        try:
            # Create a safe URL
            encoded_prompt = requests.utils.quote(prompt)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            
            response = requests.get(url)
            if response.status_code == 200:
                img_data = response.content
                img = Image.open(BytesIO(img_data))
                img = img.resize((250, 250)) # Resize for chat window
                return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Image Gen Error: {e}")
        return None

    def analyze_sentiment(self, text):
        if not TextBlob: return "black"
        try:
            score = TextBlob(text).sentiment.polarity
            if score > 0.3: return "green"
            if score < -0.3: return "red"
        except: pass
        return "black"