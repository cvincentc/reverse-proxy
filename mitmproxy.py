import logging
from mitmproxy import http
import json
import os
import ollama
import asyncio
import aiohttp
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional, Tuple


load_dotenv()

@dataclass
class Risk:
    name: str
    definition: str
    blockMessage: Optional[str] = None

@dataclass
class RiskResult:
    name: str
    detected: Optional[bool] = None
    blockMessage: Optional[str] = None


RISK_CATEGORIES = [
    Risk(
        'violence',
        'Content promoting physical, mental, or sexual harm.',
        'The prompt was blocked because it contained a description of violent acts.'
    ),
    Risk(
        'illegal_activity',
        'Detect inquiries on how to perform illegal activities.',
        'The prompt was blocked because it contained inquiries on how to perform an illegal activity.'
    ),
    Risk(
        'sexual_content',
        'Explicit or suggestive material of a sexual nature.',
        'The prompt was blocked because it contained sexual content.'
    ),
    Risk(
        'harm',
        'Generally harmful or dangerous content.'
    ),
    Risk(
        'social_bias',
        'Prejudice based on identity or characteristics (race, gender, religion, nationality, etc.).'
    ),
    Risk(
        'jailbreak',
        'Attempts to manipulate AI to generate harmful, undesired, or inappropriate content.'
    ),
    Risk(
        'profanity',
        'Offensive language or insults.'
    ),
    Risk(
        'unethical_behavior',
        'Actions that violate moral or legal standards.'
    )
]


class GuardianFilter:
    def __init__(self):
        self.ollamaHost = os.getenv("OLLAMA_HOST")
        self.modelName = os.getenv("GRANITE_GUARDIAN_MODEL")
        self.promptDestinationHost = os.getenv("DESTINATION_HOST")
        self.ollamaClient = ollama.Client(host=self.ollamaHost)
        self.openAiApiKey = os.getenv("OPENAI_API_KEY", "")
        self.openAiReqUrl = os.getenv("OPENAI_API_URL")
        self.openAiApiModel = os.getenv("OPENAI_API_MODEL")
        self.allowedPath = os.getenv("ALLOWED_PATH", "")
        self.allowedHost = os.getenv("ALLOWED_HOST", "")

    async def analyze_risk(self, session: aiohttp.ClientSession, userPrompt: str, risk: Risk) -> RiskResult | None:
        """
        Analyze prompt using LLM model and returns RiskResult
        """

        instructionPrompt = f"""
            You are a content safety classifier.

            Task:
            Determine whether the user message VIOLATES the safety category listed below.

            Safety Category:
            {risk.name}

            Definition:
            {risk.definition}

            User Message:
            \"\"\"{userPrompt}\"\"\"

            Decision Rules:
            - Answer "Yes" ONLY if the user message CLEARLY violates the definition.
            - Answer "No" if the message is neutral, informational, harmless, or unrelated.
            - If you are uncertain or there is insufficient evidence, answer "No".

            Output Format:
            Respond with EXACTLY one word: Yes or No.
            """
        loop = asyncio.get_event_loop()
        detected = None
        try:
            payload = {
                "model": self.modelName,
                "prompt": instructionPrompt,
                "stream": False,
                "options": {"temperature": 0.0, "num_predict": 10}
            }

            async with session.post(
                f"{self.ollamaHost}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=240)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    resultText = result.get("response", "").strip().lower()
                    logging.info(f"Guardian [{risk.name}]: {resultText}")
                    
                    if 'yes' == resultText:
                        detected = True
                    elif 'no' == resultText:
                        detected = False
                else:
                    logging.error(f"Ollama API error for {risk.name}: {response.status}")
                    
        except asyncio.TimeoutError:
            logging.error(f"Timeout analyzing risk({risk.name})")
        except Exception as e:
            logging.error(f"Error analyzing risk({risk.name}): {e}")

        return RiskResult(name=risk.name, detected=detected, blockMessage=risk.blockMessage)

    async def analyze(self, prompt: str) -> Tuple[Optional[str], Optional[RiskResult]]:
        errorMsg = None
        riskResult = None
        allRiskAnalyzed = True
        try:
        
            # Create one session for all requests
            async with aiohttp.ClientSession() as session:
                tasks = [
                    self.analyze_risk(session, prompt, risk) 
                    for risk in RISK_CATEGORIES
                ]
                
                # parallel using the same session
                results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if result is None or result.detected is None:
                    allRiskAnalyzed = False
                elif result.detected:
                    riskResult = result
                    break
        except Exception as e:
            logging.error(f"Error occurred analyzing prompt, exeception: {e}")
            errorMsg = "Failed to analyze user prompt"
        if not allRiskAnalyzed and riskResult is not None:
            errorMsg = "Failed to perform full analysis on user prompt"
        return errorMsg, riskResult
    

    async def request(self, flow: http.HTTPFlow):
        responseContextType = {"Content-Type": "application/json"}
        originalPath = flow.request.path.lower()
        logging.info(f"host: {flow.request.host}")
        flow.request.url = self.openAiReqUrl
        
        # only allow one request url
        if originalPath != self.allowedPath:
            response_body = json.dumps({
                "error": "Forbidden",
                "message": f"Access denied, only requests to '{self.allowedHost}{self.allowedPath}' are allowed"
            })
            flow.response = http.Response.make(
                403,
                response_body.encode('utf-8'),
                {"Content-Type": "application/json"}
            )
            return
         
        logging.info(f"request: {flow.request}")

        # analyze request message
        body = None
        try:
            body = json.loads(flow.request.content.decode('utf-8'))
        except Exception as e:
            logging.error(f"Unexpected decode error: {e}")
        message = body.get("message", "").strip() if isinstance(body, dict) else None

        logging.info(f"body text: {message}")

        # bad request, missing body parameter
        if message is None or message == "":
            flow.response = http.Response.make(
                400,
                json.dumps({
                    "error": "Bad request",
                    "message": "message is missing in the request body",
                }),
                responseContextType
            )
            return
        
        errorMsg, analyzedResult = await self.analyze(message)
        if errorMsg:
            flow.response = http.Response.make(
                500,
                json.dumps({
                    "error": "Internal system error",
                    "message": errorMsg
                }),
                responseContextType
            )
            return
        
        elif analyzedResult and analyzedResult.detected:
            blockedMessage = analyzedResult.blockMessage if analyzedResult.blockMessage else "The prompt was blocked because it is considered toxic"
            flow.response = http.Response.make(
                400, 
                json.dumps({
                    "error": "Content is toxic",
                    "message": blockedMessage
                }), 
                responseContextType)
            return
        
        # request to OpenAI
        reqJson = {"model": self.openAiApiModel, "messages": [{"role": "user", "content": message}]}
        flow.request.content = json.dumps(reqJson).encode('utf-8')
        flow.request.headers["Authorization"] = f"Bearer {self.openAiApiKey}"
        logging.info("end of request process")

addons = [GuardianFilter()]