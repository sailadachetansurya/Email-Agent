import requests

def chat(user_input):
    url = "http://127.0.0.1:8080/chat/completions"

    # ---- Normalize input ----
    if isinstance(user_input, str):
        messages = [
            {"role": "user", "content": user_input}
        ]

    elif isinstance(user_input, list):
        messages = user_input

    else:
        raise TypeError("chat() expects a string or list of messages")

    # ---- Request payload ----
    payload = {
        "messages": messages
    }

    response = requests.post(url, json=payload)

    # ---- Debug output (keep or remove in production) ----
    print(response.status_code)
    print(response.text)

    # ---- Parse response safely ----
    data = response.json()

    if response.status_code != 200:
        raise Exception(f"API Error: {data}")

    if "choices" not in data:
        raise Exception(f"Unexpected response format: {data}")

    return data["choices"][0]["message"]["content"]