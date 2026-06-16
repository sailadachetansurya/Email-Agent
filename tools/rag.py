
from llm.client import chat 


INTENT_CONTENT_MAP = { "intent-1": "Content for intent 1" ,
                   "intent-2": "Content for intent 2" ,
                   "intent-3": "Content for intent 3",
                   "intent-4": "Content for intent 4",
                   "none": "Content for none intent"}

INTENTS = list(INTENT_CONTENT_MAP.keys())
def get_intent(input):
    PROMPT = f"""
You are an intent classification agent. You will be given a user input and you need to classify the intent of the input into one of intents given to you.
Here is the user input: {input}
Please classify the intent of the user input into one of the following intents: {list(INTENT_CONTENT_MAP.keys())}. Return only the intent name without any explanation.
    """
    intent = chat(PROMPT).strip().lower()
    intent = intent.replace(".", "").replace("\n", "").strip()
    if intent not in INTENT_CONTENT_MAP:
        intent = "none"  
    return intent

def add_context(input):
    intent = get_intent(input)
    context = INTENT_CONTENT_MAP.get(intent, "No content available for this intent.")
    return {
        "intent": intent,
        "context": context,
        "email": input,
        "final_input": f"{context}\n\nEMAIL:\n{input}"
    }

def convert_to_embedding()