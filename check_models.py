import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize client using standard environment variables
client = OpenAI(
    api_key=os.getenv("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"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
)

try:
    models = client.models.list()
    print("Successfully connected to Groq! Available models:")
    for m in models.data:
        print(f" - {m.id}")
except Exception as e:
    print(f"Connection failed: {e}")