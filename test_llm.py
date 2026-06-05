import requests
import json 

url = "http://127.0.0.1:8000/chat/completions"

user_prompt = input("You: ")
payload = {
    "messages": [{
        "role": "user",
        "content": user_prompt
    }]
}

print(payload)

response = requests.post(url, json=payload)

print(response.status_code)
print(response.json())


response_json = response.json()

assistant_message = response_json["choices"][0]["message"]["content"]

print("\nAssistant:")
print(assistant_message)