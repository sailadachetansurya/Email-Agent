from sentence_transformers import SentenceTransformer
from llm.client import chat

model = SentenceTransformer('all-MiniLM-L6-v2')

INTENT_CONTENT_MAP = {
    "approval_request": "This email requires approval. Respond professionally, acknowledge the request, and indicate next steps or approval status.",
    "technical_support": "This is a technical support issue. Respond with empathy, provide troubleshooting steps, and offer escalation if needed.",
    "complaint": "This is a customer complaint. Respond apologetically, acknowledge the issue, and offer a resolution or escalation path.",
    "status_update_request": "This is a request for a status update. Provide a clear, concise summary of current progress and next steps.",
    "meeting_reschedule": "This is a meeting reschedule request. Acknowledge the conflict, propose alternative times, and confirm availability.",
    "information_request": "This is a general information request. Provide the requested information clearly or indicate when it will be available.",
    "feedback": "This is feedback. Thank the sender, acknowledge their input, and indicate how it will be used.",
    "feature_request": "This is a feature request. Thank the sender, acknowledge the suggestion, and indicate it will be reviewed by the product team.",
    "reminder": "This is a reminder. Acknowledge receipt and confirm compliance or indicate when the action will be completed.",
    "invoice_request": "This email involves an invoice or payment. Respond professionally, confirm receipt, and indicate processing timeline.",
    "none": "General email. Respond professionally and address the content appropriately."
}

INTENTS = list(INTENT_CONTENT_MAP.keys())


def get_intent(input):
    PROMPT = f"""
You are an intent classification agent. You will be given a user input and you need to classify the intent of the input into one of intents given to you.
Here is the user input: {input}
Please classify the intent of the user input into one of the following intents: {INTENTS}. Return only the intent name without any explanation.
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


def chunk_input(text, chunk_size: int = 200, overlap: int = 50):
    chunks = []
    for i in range(0, len(text), max(1, chunk_size - overlap)):
        chunk = text[i:i + chunk_size]
        chunks.append(chunk)
    return chunks


def get_embeddings(chunks):
    embeddings = []
    for chunk in chunks:
        embedding = model.encode(chunk)
        embeddings.append(embedding)
    return embeddings


def get_similarity(embedding1, embedding2):
    return model.similarity(embedding1, embedding2)
