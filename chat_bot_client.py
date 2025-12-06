from openai import OpenAI
import threading

class ChatBotClient:
    def __init__(self):
        # ---------------------------------------------------------
        # PASTE YOUR SILICONFLOW KEY HERE (starts with sk-...)
        # ---------------------------------------------------------
        self.api_key = "sk-zmjipvszsprnwpsyflkkuxlvmbmbkbmjrzcwwxndkfonoyvc" 
        
        # CORRECT URL FOR SILICONFLOW:
        self.base_url = "https://api.siliconflow.cn/v1"
        
        try:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            print("✅ Bot connected (SiliconFlow)")
        except Exception as e:
            print(f"❌ Bot connection failed: {e}")
            self.client = None

    def ask(self, prompt, callback):
        if not self.client:
            callback("Error: Bot not connected.")
            return

        def run_request():
            try:
                print(f"Thinking about: {prompt}...")
                
                # SiliconFlow uses this specific model name
                # Inside chat_bot_client.py, find the ask() method and update the model line:
                response = self.client.chat.completions.create(
                    model="deepseek-ai/DeepSeek-V2.5",  # <--- UPDATED MODEL NAME
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    stream=False
                )
                reply = response.choices[0].message.content
                print("Got reply!")
                callback(reply)
            except Exception as e:
                print(f"API Error: {e}")
                callback(f"Bot Error: {str(e)}")

        thread = threading.Thread(target=run_request)
        thread.start()