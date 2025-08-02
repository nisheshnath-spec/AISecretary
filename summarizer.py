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

#global list of summaries
summariesList = []

# Model to use (you can swap this out if you like)
MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"

#add summaries to summary list
def add_summary(body_summary):
    summariesList.append({
        'number': len(summariesList)+1,
        'summary': body_summary
    })
    
def returnList():
    return summariesList

def clear_summaries():
    summariesList.clear()

#rank the summaries based upon importance
def rank():
    if not summariesList:
        return []
    numbered_list = ""
    for summary in summariesList:
        numbered_list += f"{summary['number']}. {summary['summary']}\n"
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": f"You are an assistant secretary that ranks emails in terms of importance. You will receive a list of emails and you must rank them in terms of importance by urgency, upcoming meetings, dates, assignments, and job opportunities, and scholarships."
            },
            {
                "role": "user",
                "content": "Return only the numbers in ranked order of importance of these emails, comma separated. Example: 2, 1, 3.\n"
                f"Here are the emails: {numbered_list}"
            }
        ],
        temperature=0.3,
        max_tokens=500
    )
    answer = completion.choices[0].message.content.strip()
    ranked_order = []
    num = ""
    for a in answer:
        if a.isdigit():
            num += a
        elif num:
            ranked_order.append(int(num))
            num = ""
    
    if num:
        ranked_order.append(int(num))
    return ranked_order


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
