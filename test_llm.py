import requests
import sys

def send_request_to_server(url, data=None, method='POST'):
    """
    Send a request to the local server and print the response.
    
    Args:
        url: The URL to send the request to
        data: Optional data to send with the request
        method: HTTP method (GET or POST)
    
    Returns:
        The response text if successful, None otherwise
    """
    try:
        print(f"\nSending {method} request to: {url}")
        print("-" * 50)
        
        # Send the request
        if method == 'POST':
            response = requests.post(url, json=data, timeout=10)
        else:
            response = requests.get(url, timeout=10)
        
        # Print response information
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print("-" * 50)
        print(f"Response Body:\n{response.text}")
        
        return response
        
    except requests.exceptions.ConnectionError as e:
        print(f"\nError: Connection failed - {e}")
        return None
    except requests.exceptions.Timeout as e:
        print(f"\nError: Request timed out - {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"\nError: Request failed - {e}")
        return None
    except Exception as e:
        print(f"\nUnexpected Error: {e}")
        return None

def main():
    """Main function to demonstrate LLM capabilities."""
    server_url = "http://localhost:8080/v1/chat/completions"  # Change to your local server URL
    test_data = {
        "messages": [
            {
                "role": "user",
                "content": "Hello, this is a test message!"
            }
        ],
        "temperature": 0.7,
        "max_tokens": 200
    }
    
    # Send request
    response = send_request_to_server(server_url, data=test_data)
    
    if response and response.status_code == 200:
        print("\nRequest successful!")
    else:
        print(f"\nRequest failed.+ {response.status_code}") 

if __name__ == "__main__":
    main()