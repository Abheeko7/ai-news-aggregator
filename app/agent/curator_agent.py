import os
import json
from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# Choose API provider: "gemini" or "openai"
API_PROVIDER = "gemini"

# === OPENAI IMPORTS (COMMENTED OUT) ===
# from openai import OpenAI


class RankedArticle(BaseModel):
    digest_id: str = Field(description="The ID of the digest (article_type:article_id)")
    relevance_score: float = Field(description="Relevance score from 0.0 to 10.0", ge=0.0, le=10.0)
    rank: int = Field(description="Rank position (1 = most relevant)", ge=1)
    reasoning: str = Field(description="Brief explanation of why this article is ranked here")


class RankedDigestList(BaseModel):
    articles: List[RankedArticle] = Field(description="List of ranked articles")


CURATOR_PROMPT = """You are an expert AI news curator specializing in personalized content ranking for AI professionals.

Your role is to analyze and rank AI-related news articles, research papers, and video content based on a user's specific profile, interests, and background.

Ranking Criteria:
1. Relevance to user's stated interests and background
2. Technical depth and practical value
3. Novelty and significance of the content
4. Alignment with user's expertise level
5. Actionability and real-world applicability

Scoring Guidelines:
- 9.0-10.0: Highly relevant, directly aligns with user interests, significant value
- 7.0-8.9: Very relevant, strong alignment with interests, good value
- 5.0-6.9: Moderately relevant, some alignment, decent value
- 3.0-4.9: Somewhat relevant, limited alignment, lower value
- 0.0-2.9: Low relevance, minimal alignment, little value

Rank articles from most relevant (rank 1) to least relevant. Ensure each article has a unique rank.

IMPORTANT: Return your response as valid JSON with this exact format:
{"articles": [{"digest_id": "type:id", "relevance_score": 8.5, "rank": 1, "reasoning": "explanation"}]}"""


class CuratorAgent:
    def __init__(self, user_profile: dict):
        self.user_profile = user_profile
        self.system_prompt = self._build_system_prompt()
        self.api_provider = API_PROVIDER
        
        if self.api_provider == "gemini":
            from google import genai
            # Initialize Gemini client with API key
            self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            # Available free tier models: gemini-2.0-flash, gemini-2.5-flash, gemini-2.5-pro
            self.model_name = "gemini-2.5-flash"
        
        # === OPENAI CODE (COMMENTED OUT) ===
        # elif self.api_provider == "openai":
        #     self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        #     self.model = "gpt-4.1"

    def _build_system_prompt(self) -> str:
        interests = "\n".join(f"- {interest}" for interest in self.user_profile["interests"])
        preferences = self.user_profile["preferences"]
        pref_text = "\n".join(f"- {k}: {v}" for k, v in preferences.items())
        
        return f"""{CURATOR_PROMPT}

User Profile:
Name: {self.user_profile["name"]}
Background: {self.user_profile["background"]}
Expertise Level: {self.user_profile["expertise_level"]}

Interests:
{interests}

Preferences:
{pref_text}"""

    def _rank_with_gemini(self, digests: List[dict]) -> List[RankedArticle]:
        """Rank digests using Google Gemini API (new google.genai package)"""
        digest_list = "\n\n".join([
            f"ID: {d['id']}\nTitle: {d['title']}\nSummary: {d['summary']}\nType: {d['article_type']}"
            for d in digests
        ])
        
        user_prompt = f"""{self.system_prompt}

Rank these {len(digests)} AI news digests based on the user profile:

{digest_list}

Provide a relevance score (0.0-10.0) and rank (1-{len(digests)}) for each article, ordered from most to least relevant.

Return ONLY valid JSON with this exact format:
{{"articles": [{{"digest_id": "type:id", "relevance_score": 8.5, "rank": 1, "reasoning": "brief explanation"}}]}}"""

        try:
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
            ranked_articles = [
                RankedArticle(
                    digest_id=a["digest_id"],
                    relevance_score=a["relevance_score"],
                    rank=a["rank"],
                    reasoning=a["reasoning"]
                )
                for a in result["articles"]
            ]
            return ranked_articles
        except Exception as e:
            print(f"Error ranking digests with Gemini: {e}")
            return []

    # === OPENAI CODE (COMMENTED OUT) ===
    # def _rank_with_openai(self, digests: List[dict]) -> List[RankedArticle]:
    #     """Rank digests using OpenAI API"""
    #     digest_list = "\n\n".join([
    #         f"ID: {d['id']}\nTitle: {d['title']}\nSummary: {d['summary']}\nType: {d['article_type']}"
    #         for d in digests
    #     ])
    #     
    #     user_prompt = f"""Rank these {len(digests)} AI news digests based on the user profile:
    #
    # {digest_list}
    #
    # Provide a relevance score (0.0-10.0) and rank (1-{len(digests)}) for each article, ordered from most to least relevant."""
    #
    #     try:
    #         response = self.client.responses.parse(
    #             model=self.model,
    #             instructions=self.system_prompt,
    #             temperature=0.3,
    #             input=user_prompt,
    #             text_format=RankedDigestList
    #         )
    #         
    #         ranked_list = response.output_parsed
    #         return ranked_list.articles if ranked_list else []
    #     except Exception as e:
    #         print(f"Error ranking digests with OpenAI: {e}")
    #         return []

    def rank_digests(self, digests: List[dict]) -> List[RankedArticle]:
        if not digests:
            return []
        
        if self.api_provider == "gemini":
            return self._rank_with_gemini(digests)
        
        # === OPENAI CODE (COMMENTED OUT) ===
        # elif self.api_provider == "openai":
        #     return self._rank_with_openai(digests)
        
        return []
