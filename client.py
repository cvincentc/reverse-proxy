import os
from openai import OpenAI
import httpx
from dotenv import load_dotenv

load_dotenv()

def main():
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://localhost/v1",
        http_client=httpx.Client(verify="./ssl/nginx.crt")
    )

    user_input = input("Enter prompt: ").strip()
    if not user_input:
        print("Empty input.")
        return

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": user_input}]
        )
        print(response.choices[0].message.content)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
