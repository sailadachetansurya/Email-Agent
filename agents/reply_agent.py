from llm.client import chat

def generate_reply(email_text):
    prompt=" Generate a concise and professional reply to the following email:\n\n" + email_text
    reply = chat(prompt)
    return reply.strip()