# Task Agent - Email Workflow Automation

## Overview

A Python-based email task agent that automates email processing with LLM-powered classification, reply generation, and workflow management. The system uses a state machine architecture to handle complex email routing with human-in-the-loop approval for urgent cases.

## Features

- **LLM-Powered Classification**: Automatically classifies emails into `urgent`, `medium`, or `low` priority
- **Context-Aware Reply Generation**: Uses RAG (Retrieval Augmented Generation) to generate professional responses
- **Workflow State Machine**: 5-state workflow engine with persistent state tracking
- **Human Approval Flow**: Urgent emails require human intervention before auto-reply
- **SQLite Persistence**: Complete workflow history and state management
- **Ticket System**: Auto-generated tickets for tracking
- **RAG Integration**: Context retrieval for better reply generation

## Project Structure

```
task_agent/
├── main.py                 # Entry point - runs email processing
├── agents/                 # Agent implementations
│   ├── classifier_agent.py  # Classifies email priority
│   ├── reply_agent.py       # Generates reply drafts
│   └── audit_agent.py       # [TODO: Implement audit/logging]
├── workflows/
│   └── email_workflow.py   # Main workflow engine with state machine
├── tools/
│   ├── rag.py              # RAG context retrieval & embeddings
│   ├── ticket_manager.py   # Ticket ID generation
│   └── logger.py           # Simple logging (needs upgrade)
├── memory/
│   └── sqlite_store.py     # SQLite database operations
├── llm/
│   └── client.py           # LLM API client (local endpoint)
├── models/
│   └── schemas.py          # EmailTask data model
├── dataset/
│   ├── dataset.md          # Sample emails for testing (50 emails)
│   └── emails_structured.py # Structured email data
├── workflow.db             # SQLite database (created at runtime)
├── To-do.md                # Roadmap with 50+ improvement items
└── README.md               # This file
```

## Installation & Setup

### Requirements

```bash
# Python 3.10+
pip install requests sentence-transformers
```

### Configuration

Currently uses hardcoded values in `llm/client.py`. Consider moving to `config.yaml`.

```python
# llm/client.py
LLM_ENDPOINT = "http://127.0.0.1:8000/chat/completions"
```

## Usage

### Basic Usage

```bash
cd /mnt/Storage/Code/task_agent
python main.py
```

This will process a sample email:
```python
fake_mail = "Our production server is down. Immediate assistance required."
email_workflow.process_email(fake_mail, db)
```

### Workflow States

1. **PENDING**: Email received, awaiting classification
2. **CLASSIFIED**: Email classified as urgent/medium/low
3. **AWAITING_HUMAN_RESPONSE**: Urgent emails pause here for human approval
4. **COMPLETED**: Reply generated and task completed
5. **LOGGED & COMPLETED**: Final logging step

### Resume Paused Workflow

```python
from memory.sqlite_store import DataBase
from workflows import email_workflow

db = DataBase("workflow.db")
task_dict = db.get_workflow_state(ticket_id)
email_workflow.resume_workflow(db, task_dict)
```

## How It Works

### 1. Email Classification

```python
# agents/classifier_agent.py
def classify(email_text):
    prompt = f"Classify the following email into three categories 'low', 'medium', 'urgent'..."
    return chat(prompt)
```

### 2. Context Retrieval (RAG)

```python
# tools/rag.py
def add_context(email_text):
    intent = get_intent(email_text)  # Classify intent
    context = INTENT_CONTENT_MAP[intent]  # Retrieve relevant context
    return {"intent": intent, "context": context, "email": email_text}
```

### 3. Reply Generation

```python
# agents/reply_agent.py
def generate_reply(email_text):
    context = rag.add_context(email_text)
    prompt = f"Generate a concise and professional reply..."
    return chat(prompt)
```

### 4. Workflow Routing

```python
# workflows/email_workflow.py
def route_task(task):
    match task.status:
        case "pending":
            return _start_workflow
        case "classified":
            return _check_urgent
        case "awaiting_human_response":
            return _awaiting_human_response  # PAUSE
        case "completed":
            return _log_task
```

## Sample Dataset

The `dataset/dataset.md` contains 50 diverse sample emails covering:
- Project updates
- Meeting requests
- Technical issues
- Invoice approvals
- Customer complaints
- HR requests
- Budget approvals
- And more...

Use these to test classification accuracy and reply generation.

## Current Limitations

- ❌ `agents/audit_agent.py` is empty (needs implementation)
- ❌ No error handling in LLM calls
- ❌ Print-based logging (not structured)
- ❌ No input validation
- ❌ No unit tests
- ⚠️ Hardcoded LLM endpoint

## Roadmap

See `To-do.md` for 50+ improvement items including:
- ✅ Workflow pause/resume (Complete)
- 🔲 State machine formalization (Enum)
- 🔲 Error handling & retry logic
- 🔲 Production logging system
- 🔲 API layer (FastAPI)
- 🔲 Async workflow execution
- 🔲 RAG vector store integration
- 🔲 External email integration (IMAP/SMTP)
- 🔲 Approval dashboard (Streamlit/FastAPI)
- 🔲 Security & access control

## Development Notes

- Uses Python 3.13+
- SQLite for persistence
- Local LLM endpoint at `http://127.0.0.1:8000/chat/completions`
- SentenceTransformer for embeddings (`all-MiniLM-L6-v2`)
- State machine pattern with `match/case`
- JSON serialization for workflow state

## License

MIT License

---

**Last Updated**: 2026-06-18
