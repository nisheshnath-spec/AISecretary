# summarizer.py
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
MODEL = "openai/gpt-oss-20b"
#MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"

#rank the summaries based upon importance
def rank(email_list):
    if not email_list:
        return []
    numbered_list = ""
    for summary in email_list:
        numbered_list += f"{summary['email_id']}. {summary['body_summary']}\n"
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
        max_tokens=450
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
                "content": """You are an assistant that processes email content.
                    Given an email, return a short summary and determine if a response is needed.
                    Only include it near the body summary. 

                    Reply Code Legend:
                    - 0 = No reply needed. Sender isn't asking questions or looking for information
                    - 1 = Reply is needed. Sender asked question or needs information.
                    - 2 = Urgent reply required. Sender asked question or needs information. Asked for urgent response.

                    Completely ensure the reply code and body summary by a period and space.
                    Example: 0. summary....
                    """
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
    


# def checkreply(summary, subject, sender, reply_code):
#     if reply_code == 0:
#         return "No reply needed"

#     elif "No summary available" in summary:
#         return "No reply needed" 
    
#     else:
#         #Step 1: find out what is needed from the user
#         response_query = client.chat.completions.create(
#         model=MODEL,
#         messages=[
#             {
#                 "role": "system",
#                 "content": f"You are a helpful assistant preparing to write a reply to the following email."
#             },
#             {

#                 "role": "user",
#                 "content": f"""

#                 Context:
#                 - Sender: {sender}
#                 - Subject: {subject}
#                 - Summary: {summary}

#                 You are helping the user craft a reply to this email.
#                 Ask the user what personal details or information they need to provide to complete the reply 
#                 (for example, how they feel, which company they want to work for, etc.).
#                 The question should be direct, relevant, and assume the user is the one replying to the sender above.

#                 Return only the question.
#                 """
#             }
#             ],
#             temperature=0.3,
#             max_tokens=256
#         )
#         question = response_query.choices[0].message.content.strip()

#         #Step 2: prompt back to the user and get a response
#         print("\n📬 This email needs a reply.")
#         print("🤖 The AI needs more information first:")
#         print(f"👉 {question}\n")
#         user_input = input("Your answer: ")
#         print(user_input)

#         #Step 3: return a final reply message from all the information
        
#         reply_prompt = client.chat.completions.create(
#         model=MODEL,
#         messages=[
#             {
#                 "role": "system",
#                 "content": f"""
#                 You are a helpful assistant writing an email reply in a tone that matches the sent email.
                
#                 Email Summary:
#                 Sender: {sender}
#                 Subject: {subject}
#                 Summary: {summary}

#                 The user has provided this additional information:
#                 "{user_input}"

#                 You are writing in behalf of the user, who is responding to the email itself.
#                 The sender of the email is who this email is being written for. Use the given information
#                 in order to answer the email as if it you were the person themself writing a full reply.
#                 """
#             }
#             ],
#             temperature=0.3,
#             max_tokens=256
#         )
        
#         return reply_prompt.choices[0].message.content.strip() 

def reply_info_question(sender, subject, summary, model = MODEL):
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You help users craft replies by first asking ONE key clarifying question."},
            {"role": "user", "content": f"Sender: {sender}\nSubject: {subject}\nSummary: {summary}\nReturn only ONE question the user must answer before replying."}
        ],
        temperature=0.3,
        max_tokens=128
    )
    return completion.choices[0].message.content.strip()

def compose_reply(subject, sender, summary, user_input, model = MODEL):
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Write a concise, professional reply in the user's voice."},
            {"role": "user", "content": f"Sender: {sender}\nSubject: {subject}\nSummary: {summary}\nExtra info from user: {user_input}\nWrite the full email body only."}
        ],
        temperature=0.3,
        max_tokens=256
    )
    return completion.choices[0].message.content.strip()

