import threading
import requests
from io import BytesIO
from PIL import Image, ImageTk
from openai import OpenAI

class ImageGenClient:
    def __init__(self):
        # ---------------------------------------------------------
        # PASTE YOUR SILICONFLOW KEY HERE
        # ---------------------------------------------------------
        self.api_key = "sk-zmjipvszsprnwpsyflkkuxlvmbmbkbmjrzcwwxndkfonoyvc"
        
        # SiliconFlow Base URL
        self.base_url = "https://api.siliconflow.cn/v1"
        
        try:
            # We re-use the OpenAI client library as SiliconFlow is compatible
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            print("✅ Image Generator connected (SiliconFlow/Flux)")
        except Exception as e:
            print(f"❌ Image Gen connection failed: {e}")
            self.client = None

    def generate(self, prompt, callback):
        """
        Generates an image in a background thread to avoid freezing the GUI.
        Sizing: Resizes image to max 300px width for chat bubble display.
        """
        if not self.client or not prompt.strip():
            callback(None, "Error: Client not ready or empty prompt.")
            return

        def run_request():
            try:
                print(f"🎨 Generating image for: '{prompt}'...")
                
                # 1. Call API
                response = self.client.images.generate(
                    model="black-forest-labs/FLUX.1-schnell", # Fast, high quality model
                    prompt=prompt,
                    size="1024x1024",
                    n=1,
                )

                image_url = response.data[0].url
                print(f"Downloading from: {image_url}")
                
                # 2. Download Image Bytes
                img_response = requests.get(image_url, timeout=30)
                img_response.raise_for_status()
                img_data = BytesIO(img_response.content)
                
                # 3. Process with PIL (Resize for Chat)
                pil_image = Image.open(img_data)
                
                # Calculate new height keeping aspect ratio, max width 300px
                base_width = 300
                w_percent = (base_width / float(pil_image.size[0]))
                h_size = int((float(pil_image.size[1]) * float(w_percent)))
                # Use LANCZOS for high-quality downscaling
                pil_image_resized = pil_image.resize((base_width, h_size), Image.Resampling.LANCZOS)
                
                # Convert to Tkinter PhotoImage
                tk_image = ImageTk.PhotoImage(pil_image_resized)
                
                # Success callback (image exists, error is None)
                callback(tk_image, None)

            except Exception as e:
                print(f"Image Generation Error: {e}")
                # Failure callback (image None, error message exists)
                callback(None, f"Image Error: {str(e)}")

        # Start thread
        thread = threading.Thread(target=run_request, daemon=True)
        thread.start()