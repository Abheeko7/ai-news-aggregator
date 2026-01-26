import os
import json
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Set to True to use mock responses (no API billing required)
USE_MOCK = False

# Choose API provider: "gemini" or "openai"
API_PROVIDER = "gemini"


class DigestOutput(BaseModel):
    title: str
    summary: str

PROMPT = """You are an expert AI news analyst specializing in summarizing technical articles, research papers, and video content about artificial intelligence.

Your role is to create concise, informative digests that help readers quickly understand the key points and significance of AI-related content.

Guidelines:
- Create a compelling title (5-10 words) that captures the essence of the content
- Write a 2-3 sentence summary that highlights the main points and why they matter
- Focus on actionable insights and implications
- Use clear, accessible language while maintaining technical accuracy
- Avoid marketing fluff - focus on substance

IMPORTANT: Return your response as valid JSON with exactly this format:
{"title": "Your title here", "summary": "Your summary here"}"""


class DigestAgent:
    def __init__(self):
        self.use_mock = USE_MOCK
        self.api_provider = API_PROVIDER
        self.system_prompt = PROMPT
        
        if not self.use_mock:
            if self.api_provider == "gemini":
                from google import genai
                # Initialize Gemini client with API key
                self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
                # Available free tier models: gemini-2.0-flash, gemini-2.5-flash, gemini-2.5-pro
                self.model_name = "gemini-2.5-flash"
            # === OPENAI CODE (COMMENTED OUT) ===
            # elif self.api_provider == "openai":
            #     from openai import OpenAI
            #     self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            #     self.model = "gpt-4o-mini"

    def _generate_mock_digest(self, title: str, content: str, article_type: str) -> DigestOutput:
        """Generate a simple mock digest without calling any API"""
        short_content = content[:200].replace('\n', ' ').strip()
        if len(content) > 200:
            short_content += "..."
        
        mock_title = f"[MOCK] {title[:50]}"
        mock_summary = f"This {article_type} discusses: {short_content}"
        
        return DigestOutput(title=mock_title, summary=mock_summary)

    def _generate_gemini_digest(self, title: str, content: str, article_type: str) -> Optional[DigestOutput]:
        """Generate digest using Google Gemini API (new google.genai package)"""
        try:
            user_prompt = f"""{self.system_prompt}

Create a digest for this {article_type}:
Title: {title}
Content: {content[:8000]}

Return ONLY valid JSON with this exact format:
{{"title": "Your compelling title", "summary": "Your 2-3 sentence summary"}}"""

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
            )
            
            # Parse JSON from response
            response_text = response.text.strip()
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            result = json.loads(response_text)
            return DigestOutput(title=result["title"], summary=result["summary"])
        except Exception as e:
            print(f"Error generating digest with Gemini: {e}")
            return None

    # === OPENAI CODE (COMMENTED OUT) ===
    # def _generate_openai_digest(self, title: str, content: str, article_type: str) -> Optional[DigestOutput]:
    #     """Generate digest using OpenAI API"""
    #     try:
    #         from openai import OpenAI
    #         user_prompt = f"Create a digest for this {article_type}: \n Title: {title} \n Content: {content[:8000]}"
    #
    #         response = self.client.responses.parse(
    #             model=self.model,
    #             instructions=self.system_prompt,
    #             temperature=0.7,
    #             input=user_prompt,
    #             text_format=DigestOutput
    #         )
    #         
    #         return response.output_parsed
    #     except Exception as e:
    #         print(f"Error generating digest with OpenAI: {e}")
    #         return None

    def generate_digest(self, title: str, content: str, article_type: str) -> Optional[DigestOutput]:
        # Use mock if enabled (free, no API needed)
        if self.use_mock:
            return self._generate_mock_digest(title, content, article_type)
        
        # Use Gemini API
        if self.api_provider == "gemini":
            return self._generate_gemini_digest(title, content, article_type)
        
        # === OPENAI CODE (COMMENTED OUT) ===
        # elif self.api_provider == "openai":
        #     return self._generate_openai_digest(title, content, article_type)
        
        return None
