import requests
import os
from dotenv import load_dotenv

def main():
    load_dotenv()

    url = os.getenv("ALLOWED_URL")
    if not url:
        raise RuntimeError("ALLOWED_URL is not set in .env")

    print("Enter your prompt (press Enter to send, Ctrl+C to exit):")
    user_input = input("> ").strip()

    if not user_input:
        print("Empty input. Nothing sent.")
        return

    payload = {
        "message": user_input
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=600, verify='./ssl/nginx.crt')
        print("\nResponse:")
        print(response.json())
    except Exception as e:
        print(f"\nRequest failed: {e}")

if __name__ == "__main__":
    main()
