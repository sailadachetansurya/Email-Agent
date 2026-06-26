from tools.filetools import TOOLS

SYSTEM_PROMPT = """
You are a coding agent.

Available tools:

1. list_files(path)
2. read_file(path)
3. write_file(path, content)
4. search_code(query, path)
5. run_command(cmd)
6. run_tests()

Respond ONLY with JSON.

Tool call format:
{
  "action": "<tool_name>",
  "args": {}
}

Final answer format:
{
  "action": "final",
  "answer": "..."
}
"""

import json
import re

def extract_json(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found: {text}")
    return json.loads(match.group())

class Agent:

    def __init__(self, chat):
        self.chat = chat

    def run(self, task):

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": task
            }
        ]

        for step in range(20):

            reply = self.chat(messages)

            print(reply)
            action = extract_json(reply)

            if action["action"] == "final":
                return action["answer"]

            tool_name = action["action"]
            args = action.get("args", {})

            if tool_name not in TOOLS:
                result = f"ERROR: Unknown tool {tool_name}"
            else:
                try:
                    result = TOOLS[tool_name](**args)
                except Exception as e:
                    result = f"ERROR: {str(e)}"

            messages.append({
                "role": "assistant",
                "content": reply
            })

            messages.append({
                "role": "user",
                "content": f"Tool result:\n{result}"
            })

        return "Max steps exceeded"