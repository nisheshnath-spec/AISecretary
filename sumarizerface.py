import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env
load_dotenv()

# Get API key
HF_TOKEN = os.getenv("HF_TOKEN")
if HF_TOKEN is None:
    raise ValueError("HF_TOKEN is not set in environment variables")

# Create the client
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

# Function to summarize email
def summarize_email(plain_body):
    completion = client.chat.completions.create(
        model="moonshotai/Kimi-K2-Instruct:groq",
        messages=[
            {
                "role": "user",
                "content": f"Summarize this email:\n\n{plain_body}"
            }
        ],
        temperature=0.3,
        max_tokens=256
    )
    return completion.choices[0].message.content