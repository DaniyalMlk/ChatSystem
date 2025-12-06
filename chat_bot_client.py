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
    # --- ADD THIS NEW METHOD TO ChatBotClient CLASS ---
    def analyze_text(self, text_data, mode, callback):
        """
        Analyzes chat history for summary or keywords using DeepSeek.
        mode: 'summary' or 'keywords'
        """
        if not self.client:
            callback("Error: Bot not connected.")
            return

        def run_analysis():
            try:
                # 1. Define specific instructions based on mode
                if mode == "summary":
                    system_prompt = "You are a helpful assistant. Summarize the following chat conversation briefly in 2-3 sentences."
                else:
                    system_prompt = "You are a helpful assistant. Extract the top 5 most important keywords or topics from this chat. Return them as a comma-separated list."

                print(f"🧠 Analyzing chat for {mode}...")

                # 2. Call API with the chat history
                response = self.client.chat.completions.create(
                    model="deepseek-ai/DeepSeek-V2.5", 
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Chat History:\n{text_data}"}
                    ],
                    stream=False
                )
                
                reply = response.choices[0].message.content
                print("Analysis complete.")
                callback(reply)

            except Exception as e:
                print(f"Analysis Error: {e}")
                callback(f"Analysis Error: {str(e)}")

        thread = threading.Thread(target=run_analysis)
        thread.start()
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