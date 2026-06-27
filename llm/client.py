import os
import json
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from tools.metrics import track

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "..", "llm_config.json")

DEFAULT_CONFIG = {
    "provider": "local",
    "providers": {
        "local": {
            "endpoint": "http://127.0.0.1:8080/chat/completions",
            "model": "local"
        },
        "google": {
            "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            "api_key": "",
            "model": "gemini-2.0-flash"
        }
    }
}


def _load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return DEFAULT_CONFIG


def _save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_provider():
    config = _load_config()
    return config.get("provider", "local")


def set_provider(provider_name):
    config = _load_config()
    if provider_name not in config["providers"]:
        available = ", ".join(config["providers"].keys())
        raise ValueError(f"Unknown provider '{provider_name}'. Available: {available}")
    config["provider"] = provider_name
    _save_config(config)
    return config["providers"][provider_name]


def list_providers():
    config = _load_config()
    current = config.get("provider", "local")
    providers = []
    for name, settings in config["providers"].items():
        providers.append({"name": name, "model": settings.get("model", ""), "active": name == current})
    return providers, current


def set_google_api_key(api_key):
    config = _load_config()
    config["providers"]["google"]["api_key"] = api_key
    _save_config(config)


def set_model(model_name):
    config = _load_config()
    provider = config.get("provider", "local")
    config["providers"][provider]["model"] = model_name
    _save_config(config)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout))
)
def _chat_local(messages):
    config = _load_config()
    endpoint = config["providers"]["local"]["endpoint"]
    payload = {"messages": messages}
    response = requests.post(endpoint, json=payload, timeout=30)
    data = response.json()
    if response.status_code != 200:
        raise Exception(f"API Error: {data}")
    if "choices" not in data:
        raise Exception(f"Unexpected response format: {data}")
    return data["choices"][0]["message"]["content"]


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout))
)
def _chat_google(messages):
    config = _load_config()
    google_config = config["providers"]["google"]
    api_key = google_config.get("api_key", "")
    if not api_key:
        raise Exception("Google API key not set. Use: /provider google --api-key YOUR_KEY")
    model = google_config.get("model", "gemini-2.0-flash")
    endpoint = google_config["endpoint"].format(model=model)
    url = f"{endpoint}?key={api_key}"
    contents = []
    for msg in messages:
        role = "user" if msg["role"] in ("user", "system") else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    payload = {"contents": contents}
    response = requests.post(url, json=payload, timeout=30)
    data = response.json()
    if response.status_code != 200:
        raise Exception(f"Google API Error: {data}")
    if "candidates" not in data or not data["candidates"]:
        raise Exception(f"Unexpected response format: {data}")
    return data["candidates"][0]["content"]["parts"][0]["text"]


def chat(user_input):
    if isinstance(user_input, str):
        messages = [{"role": "user", "content": user_input}]
    elif isinstance(user_input, list):
        messages = user_input
    else:
        raise TypeError("chat() expects a string or list of messages")

    provider = get_provider()

    with track(f"llm_{provider}"):
        if provider == "local":
            return _chat_local(messages)
        elif provider == "google":
            return _chat_google(messages)
        else:
            raise Exception(f"Unknown provider: {provider}")
