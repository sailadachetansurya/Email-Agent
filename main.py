from llm.client import chat
from memory.sqlite_store import DataBase
from workflows import email_workflow
from my_agents.agent import Agent

db = DataBase("workflow.db")
if __name__ == "__main__":
    fake_mail = "Our production server is down. Immediate assistance required."
    # email_workflow.process_email(fake_mail, db)
    task = db.get_workflow_state(1)
    llm_agent = Agent(chat)
    result = llm_agent.run(f"""write a simple python code to demonstrate your capabilities inside the file ./test_llm.py. The code should be able to send a request to the local server and print the response. The code should be able to handle errors gracefully and print the error message if the request fails.""")
    print(result)
    