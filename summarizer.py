import os
from dotenv import load_dotenv
from together import Together

# Load environment variables from .env
load_dotenv()

# Get API key
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
if TOGETHER_API_KEY is None:
    raise ValueError("TOGETHER_API_KEY is not set in environment variables")

# Create the Together client
client = Together(api_key=TOGETHER_API_KEY)

# Model to use (you can swap this out if you like)
MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"

# Function to summarize email
def summarize_email(plain_body):
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are an assistant that summarizes briefly summarizes emails, including but not limited to upcoming meetings, dates, assignments, and news."
            },  
            {
                "role": "user",
                "content": f"Summarize this email:\n\n{plain_body}"
            }
        ],
        temperature=0.3,
        max_tokens=256
    )
    return completion.choices[0].message.content.strip()
