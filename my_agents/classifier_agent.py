
from llm.client import chat


def classify(email_text):
    prompt = f"Classify the following email into three categories 'low' , 'medium' ,'urgent' no need to explain or reason why it was classified as such . :\n\n{email_text}"
    classification = chat(prompt)
    return classification.strip().lower()