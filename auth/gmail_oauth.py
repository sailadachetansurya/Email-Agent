import os
import json
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "..", "gmail_credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "..", "gmail_token.json")

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"]

AUTH_URL_TEMPLATE = "https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope={scope}&access_type=offline&prompt=consent"
TOKEN_URL = "https://oauth2.googleapis.com/token"

auth_code = None
server_running = False


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    global auth_code

    def do_GET(self):
        global auth_code
        query = parse_qs(urlparse(self.path).query)
        if "code" in query:
            auth_code = query["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Logged in!</h1><p>You can close this tab.</p>")
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h1>Error</h1><p>No auth code received.</p>")

    def log_message(self, format, *args):
        pass


def _start_server(port=8085):
    global server_running
    server_running = True
    server = HTTPServer(("localhost", port), OAuthCallbackHandler)
    server.timeout = 120
    while server_running:
        server.handle_request()


def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    return None


def save_credentials(client_id, client_secret):
    creds = {"client_id": client_id, "client_secret": client_secret, "redirect_uri": "http://localhost:8085/callback"}
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(creds, f, indent=2)


def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    return None


def save_token(token_data):
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)


def is_logged_in():
    token = load_token()
    return token is not None and "access_token" in token


def login(client_id=None, client_secret=None):
    global auth_code, server_running

    creds = load_credentials()
    if client_id and client_secret:
        save_credentials(client_id, client_secret)
        creds = {"client_id": client_id, "client_secret": client_secret, "redirect_uri": "http://localhost:8085/callback"}

    if not creds:
        return None, "No credentials found. Run: gmail --setup <client_id> <client_secret>"

    auth_code = None
    port = 8085
    redirect_uri = f"http://localhost:{port}/callback"
    scope = " ".join(SCOPES)
    auth_url = AUTH_URL_TEMPLATE.format(client_id=creds["client_id"], redirect_uri=redirect_uri, scope=scope)

    server_thread = threading.Thread(target=_start_server, args=(port,), daemon=True)
    server_thread.start()

    webbrowser.open(auth_url)

    server_thread.join(timeout=120)

    if not auth_code:
        return None, "Login timed out or cancelled."

    import requests
    token_data = {
        "code": auth_code,
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }

    response = requests.post(TOKEN_URL, data=token_data)
    if response.status_code != 200:
        return None, f"Token exchange failed: {response.text}"

    token = response.json()
    save_token(token)
    return token, "Logged in successfully."


def refresh_token():
    token = load_token()
    creds = load_credentials()
    if not token or not creds:
        return None

    if "refresh_token" not in token:
        return None

    import requests
    data = {
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": token["refresh_token"],
        "grant_type": "refresh_token"
    }

    response = requests.post(TOKEN_URL, data=data)
    if response.status_code != 200:
        return None

    new_token = response.json()
    new_token["refresh_token"] = token["refresh_token"]
    save_token(new_token)
    return new_token


def get_access_token():
    token = load_token()
    if not token:
        return None
    return token.get("access_token")


def logout():
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)
    return True
