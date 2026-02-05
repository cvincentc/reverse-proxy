from mitmproxy import http
import json
import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
GUARDIAN_MODEL = os.getenv("GRANITE_GUARDIAN_MODEL", "granite3-guardian:2b")

# Exactly 3 categories as required by exercise
RISK_CATEGORIES = [
    ("violent_acts", "description of violent acts",
     "The prompt was blocked because it contained description of violent acts"),
    ("illegal_activity", "inquiries on how to perform an illegal activity",
     "The prompt was blocked because it contained inquiries on how to perform an illegal activity"),
    ("sexual_content", "sexual content",
     "The prompt was blocked because it contained sexual content"),
]


class GuardianFilter:

    async def check_content(self, text: str) -> tuple[bool, str]:
        """Check text for violations. Returns (is_blocked, message)"""
        async with aiohttp.ClientSession() as session:
            # Check 3 specific categories first
            for cat_id, cat_desc, block_msg in RISK_CATEGORIES:
                prompt = f"""You are a content safety classifier.
Determine if the following text contains {cat_desc}.
Text: \"\"\"{text}\"\"\"
Answer exactly "Yes" or "No"."""

                payload = {
                    "model": GUARDIAN_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.0, "num_predict": 10}
                }

                try:
                    async with session.post(
                        f"{OLLAMA_HOST}/api/generate",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=120)
                    ) as resp:
                        if resp.status == 200:
                            result = await resp.json()
                            answer = result.get("response", "").strip().lower()
                            if answer == "yes":
                                return True, block_msg
                except Exception:
                    pass

            # Generic toxicity check
            toxic_prompt = f"""You are a content safety classifier.
Determine if the following text is toxic or harmful.
Text: \"\"\"{text}\"\"\"
Answer exactly "Yes" or "No"."""

            payload = {
                "model": GUARDIAN_MODEL,
                "prompt": toxic_prompt,
                "stream": False,
                "options": {"temperature": 0.0, "num_predict": 10}
            }
            try:
                async with session.post(
                    f"{OLLAMA_HOST}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        answer = result.get("response", "").strip().lower()
                        if answer == "yes":
                            return True, "The prompt was blocked because it is considered toxic"
            except Exception:
                pass

        return False, ""

    def extract_user_content(self, body: dict) -> str:
        """Extract user messages from OpenAI chat format"""
        messages = body.get("messages", [])
        user_msgs = [m.get("content", "") for m in messages if m.get("role") == "user"]
        return " ".join(user_msgs)

    def extract_assistant_content(self, body: dict) -> str:
        """Extract assistant message from OpenAI response"""
        choices = body.get("choices", [])
        if choices:
            return choices[0].get("message", {}).get("content", "")
        return ""

    async def request(self, flow: http.HTTPFlow):
        """Intercept requests going to OpenAI"""
        # Only intercept chat completions endpoint
        if "/v1/chat/completions" not in flow.request.path:
            return

        try:
            body = json.loads(flow.request.content)
            user_content = self.extract_user_content(body)

            if user_content:
                is_blocked, message = await self.check_content(user_content)
                if is_blocked:
                    flow.response = http.Response.make(
                        400,
                        message.encode("utf-8"),
                        {"Content-Type": "text/plain"}
                    )
        except Exception:
            pass  # Let request through on error

    async def response(self, flow: http.HTTPFlow):
        """Intercept responses from OpenAI"""
        # Only intercept chat completions endpoint
        if "/v1/chat/completions" not in flow.request.path:
            return

        if flow.response.status_code != 200:
            return

        try:
            body = json.loads(flow.response.content)
            assistant_content = self.extract_assistant_content(body)

            if assistant_content:
                is_blocked, message = await self.check_content(assistant_content)
                if is_blocked:
                    # Modify response to show blocked message
                    body["choices"][0]["message"]["content"] = message
                    flow.response.content = json.dumps(body).encode("utf-8")
        except Exception:
            pass  # Let response through on error


addons = [GuardianFilter()]
