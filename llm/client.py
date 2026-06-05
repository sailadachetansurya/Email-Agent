
import requests,json

def chat(user_input):
    url = "http://127.0.0.1:8000/chat/completions"
    payload = {
    "messages": [{
        "role": "user",
        "content": user_input
    }]
    }
    response = requests.post(url, json=payload)
    assistant_reply =  response.json()["choices"][0]["message"]["content"]
    return assistant_reply