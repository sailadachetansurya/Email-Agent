# Simple Task Agent with LLM Integration
#
# A Python agent that integrates an LLM for intelligent task analysis.
# Uses delegate_task subagents for LLM-powered breakdown of tasks.
#
# Features:
# - LLM-powered task identification and analysis
# - Automatic task decomposition into subtasks
# - Tool execution with Hermes integration
# - Human verification step
# - Status tracking and reporting
#
# Files:
#   - agent_llm.py    # Main agent with LLM integration
#   - launcher.py     # Entry point for LLM version
#   - test_agent.py   # Test suite
#
# Usage:
#   cd ~/task_agent
#   python3 launcher.py
#
# LLM Integration:
#   The agent uses delegate_task to spawn an LLM subagent for:
#   - Task analysis and understanding
#   - Breaking tasks into logical subtasks
#   - Suggesting appropriate tools
#
# To integrate with Hermes LLM:
#   1. Edit agent_llm.py's _simulate_llm_analysis method
#   2. Use delegate_task to spawn an LLM subagent
#   3. Parse the JSON response for subtasks
#
# Example tasks:
#   "Analyze this file and summarize it"
#   "Design a solution for X"
#   "Implement a feature that does Y"
#   "Test the application and verify results"

main.py
│
├── llm/
│   └── client.py
│
├── tools/
│   ├── email_reader.py
│   ├── email_sender.py
│   ├── ticket_manager.py
│   └── logger.py
│
├── agents/
│   ├── classifier_agent.py
│   ├── reply_agent.py
│   └── audit_agent.py
│
├── workflows/
│   └── email_workflow.py
│
├── memory/
│   └── sqlite_store.py
│
└── models/
    └── schemas.py