from llm.client import chat
from tools import rag

def generate_reply(email_text):
    email_text = rag.add_context(email_text)
    prompt=" Generate a concise and professional reply to the following email:\n\n" + email_text["context"] 
    reply = chat(prompt)
    return reply.strip()