import os
import json
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# Choose API provider: "gemini" or "openai"
API_PROVIDER = "gemini"

# === OPENAI IMPORTS (COMMENTED OUT) ===
# from openai import OpenAI


class EmailIntroduction(BaseModel):
    greeting: str = Field(description="Personalized greeting with user's name and date")
    introduction: str = Field(description="2-3 sentence overview of what's in the top 10 ranked articles")


class RankedArticleDetail(BaseModel):
    digest_id: str
    rank: int
    relevance_score: float
    title: str
    summary: str
    url: str
    article_type: str
    reasoning: Optional[str] = None


class EmailDigestResponse(BaseModel):
    introduction: EmailIntroduction
    articles: List[RankedArticleDetail]
    total_ranked: int
    top_n: int
    
    def to_markdown(self) -> str:
        markdown = f"{self.introduction.greeting}\n\n"
        markdown += f"{self.introduction.introduction}\n\n"
        markdown += "---\n\n"
        
        for article in self.articles:
            markdown += f"## {article.title}\n\n"
            markdown += f"{article.summary}\n\n"
            markdown += f"[Read more →]({article.url})\n\n"
            markdown += "---\n\n"
        
        return markdown


class EmailDigest(BaseModel):
    introduction: EmailIntroduction
    ranked_articles: List[dict] = Field(description="Top 10 ranked articles with their details")


EMAIL_PROMPT = """You are an expert email writer specializing in creating engaging, personalized AI news digests.

Your role is to write a warm, professional introduction for a daily AI news digest email that:
- Greets the user by name
- Includes the current date
- Provides a brief, engaging overview of what's coming in the top 10 ranked articles
- Highlights the most interesting or important themes
- Sets expectations for the content ahead

Keep it concise (2-3 sentences for the introduction), friendly, and professional.

IMPORTANT: Return your response as valid JSON with this exact format:
{"greeting": "Your greeting here", "introduction": "Your introduction here"}"""


class EmailAgent:
    def __init__(self, user_profile: dict):
        self.user_profile = user_profile
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
        #     self.model = "gpt-4o-mini"

    def _generate_gemini_introduction(self, ranked_articles: List) -> EmailIntroduction:
        """Generate email introduction using Google Gemini API (new google.genai package)"""
        top_articles = ranked_articles[:10]
        article_summaries = "\n".join([
            f"{idx + 1}. {article.title if hasattr(article, 'title') else article.get('title', 'N/A')} (Score: {article.relevance_score if hasattr(article, 'relevance_score') else article.get('relevance_score', 0):.1f}/10)"
            for idx, article in enumerate(top_articles)
        ])
        
        current_date = datetime.now().strftime('%B %d, %Y')
        user_prompt = f"""{EMAIL_PROMPT}

Create an email introduction for {self.user_profile['name']} for {current_date}.

Top 10 ranked articles:
{article_summaries}

Generate a greeting and introduction that previews these articles.

Return ONLY valid JSON with this exact format:
{{"greeting": "Hey Name, here is your daily digest...", "introduction": "Today's highlights include..."}}"""

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
            intro = EmailIntroduction(greeting=result["greeting"], introduction=result["introduction"])
            
            # Ensure greeting starts with user's name
            if self.user_profile['name'] not in intro.greeting:
                intro.greeting = f"Hey {self.user_profile['name']}, here is your daily digest of AI news for {current_date}."
            
            return intro
        except Exception as e:
            print(f"Error generating introduction with Gemini: {e}")
            current_date = datetime.now().strftime('%B %d, %Y')
            return EmailIntroduction(
                greeting=f"Hey {self.user_profile['name']}, here is your daily digest of AI news for {current_date}.",
                introduction="Here are the top AI news articles ranked by relevance to your interests."
            )

    # === OPENAI CODE (COMMENTED OUT) ===
    # def _generate_openai_introduction(self, ranked_articles: List) -> EmailIntroduction:
    #     """Generate email introduction using OpenAI API"""
    #     top_articles = ranked_articles[:10]
    #     article_summaries = "\n".join([
    #         f"{idx + 1}. {article.title if hasattr(article, 'title') else article.get('title', 'N/A')} (Score: {article.relevance_score if hasattr(article, 'relevance_score') else article.get('relevance_score', 0):.1f}/10)"
    #         for idx, article in enumerate(top_articles)
    #     ])
    #     
    #     current_date = datetime.now().strftime('%B %d, %Y')
    #     user_prompt = f"""Create an email introduction for {self.user_profile['name']} for {current_date}.
    #
    # Top 10 ranked articles:
    # {article_summaries}
    #
    # Generate a greeting and introduction that previews these articles."""
    #
    #     try:
    #         response = self.client.responses.parse(
    #             model=self.model,
    #             instructions=EMAIL_PROMPT,
    #             temperature=0.7,
    #             input=user_prompt,
    #             text_format=EmailIntroduction
    #         )
    #         
    #         intro = response.output_parsed
    #         if not intro.greeting.startswith(f"Hey {self.user_profile['name']}"):
    #             intro.greeting = f"Hey {self.user_profile['name']}, here is your daily digest of AI news for {current_date}."
    #         
    #         return intro
    #     except Exception as e:
    #         print(f"Error generating introduction with OpenAI: {e}")
    #         current_date = datetime.now().strftime('%B %d, %Y')
    #         return EmailIntroduction(
    #             greeting=f"Hey {self.user_profile['name']}, here is your daily digest of AI news for {current_date}.",
    #             introduction="Here are the top AI news articles ranked by relevance to your interests."
    #         )

    def generate_introduction(self, ranked_articles: List) -> EmailIntroduction:
        if not ranked_articles:
            return EmailIntroduction(
                greeting=f"Hey {self.user_profile['name']}, here is your daily digest of AI news for {datetime.now().strftime('%B %d, %Y')}.",
                introduction="No articles were ranked today."
            )
        
        if self.api_provider == "gemini":
            return self._generate_gemini_introduction(ranked_articles)
        
        # === OPENAI CODE (COMMENTED OUT) ===
        # elif self.api_provider == "openai":
        #     return self._generate_openai_introduction(ranked_articles)
        
        # Fallback
        current_date = datetime.now().strftime('%B %d, %Y')
        return EmailIntroduction(
            greeting=f"Hey {self.user_profile['name']}, here is your daily digest of AI news for {current_date}.",
            introduction="Here are the top AI news articles ranked by relevance to your interests."
        )

    def create_email_digest(self, ranked_articles: List[dict], limit: int = 10) -> EmailDigest:
        top_articles = ranked_articles[:limit]
        introduction = self.generate_introduction(top_articles)
        
        return EmailDigest(
            introduction=introduction,
            ranked_articles=top_articles
        )
    
    def create_email_digest_response(self, ranked_articles: List[RankedArticleDetail], total_ranked: int, limit: int = 10) -> EmailDigestResponse:
        top_articles = ranked_articles[:limit]
        introduction = self.generate_introduction(top_articles)
        
        return EmailDigestResponse(
            introduction=introduction,
            articles=top_articles,
            total_ranked=total_ranked,
            top_n=limit
        )
