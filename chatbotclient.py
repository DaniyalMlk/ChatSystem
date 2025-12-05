# File: chat_bot_client.py
import time
import random

class ChatBotClient:
    def __init__(self):
        self.history = []
        self.personality = "helpful assistant"

    def set_personality(self, personality):
        self.personality = personality

    def chat(self, user_input):
        """
        Simulates an AI response. 
        Replace this logic with the real OpenAI/Ollama code later.
        """
        self.history.append(user_input)
        
        # Simulate "thinking" time so the GUI doesn't freeze
        time.sleep(1)

        # Simple logic to demonstrate "Context Awareness"
        if "hello" in user_input.lower():
            return f"[{self.personality}] Hello there! How can I help you?"
        elif "weather" in user_input.lower():
            return f"[{self.personality}] I am just a code bot, but I hope it's sunny!"
        elif "bye" in user_input.lower():
            return f"[{self.personality}] Goodbye! Chat with you soon."
        else:
            return f"[{self.personality}] You said: '{user_input}'. Tell me more!"