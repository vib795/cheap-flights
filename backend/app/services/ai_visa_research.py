"""
AI-Powered Visa Information Research Service

This service provides fallback visa information using web search and AI summarization
when primary sources (like TravelBriefing) are unavailable.

IMPORTANT: This generates AI-assisted research and is NOT authoritative.
Users must verify all information with official sources.
"""

import logging
from typing import Optional

import httpx

from app.models import VisaBaseline
from app.settings import settings

logger = logging.getLogger(__name__)


class AIVisaResearchService:
    """
    AI-powered visa research using web search and summarization

    This is a best-effort fallback service that uses:
    1. Web search to find relevant visa information
    2. AI summarization to extract key points

    Results are HEURISTIC and require official verification.
    """

    def __init__(self):
        self.enabled = settings.enable_ai_visa_research
        self.anthropic_api_key = settings.anthropic_api_key

    async def research_visa_requirements(
        self,
        destination_country: str,
        passport_nationality: str,
    ) -> Optional[VisaBaseline]:
        """
        Research visa requirements using AI-assisted web search

        Args:
            destination_country: Destination country ISO code
            passport_nationality: Passport country ISO code

        Returns:
            VisaBaseline with AI-generated summary or None if disabled/failed
        """
        if not self.enabled or not self.anthropic_api_key:
            logger.info("AI visa research is disabled (no API key configured)")
            return None

        try:
            logger.info(
                f"Starting AI visa research for {passport_nationality} → {destination_country}"
            )

            # Step 1: Construct search query
            search_query = self._build_search_query(destination_country, passport_nationality)

            # Step 2: Perform web search using a search API
            search_results = await self._search_web(search_query)

            if not search_results:
                logger.warning("No search results found for visa research")
                return None

            # Step 3: Use Claude to summarize findings
            summary = await self._summarize_with_ai(
                search_results, destination_country, passport_nationality
            )

            if not summary:
                return None

            return VisaBaseline(
                destination_entry_summary=summary,
                source="ai-research",
                disclaimer=(
                    "⚠️ AI-GENERATED RESEARCH (NOT AUTHORITATIVE): "
                    "This information was gathered via web search and summarized by AI. "
                    "It is provided as helpful context only. "
                    "You MUST verify all visa requirements with official sources: "
                    "embassy websites, consulate offices, official government travel advisories, "
                    "or professional visa services before making travel decisions. "
                    "Visa rules change frequently and vary by individual circumstances."
                ),
            )

        except Exception as e:
            logger.error(f"AI visa research failed: {e}", exc_info=True)
            return None

    def _build_search_query(self, destination: str, passport: str) -> str:
        """Build an effective search query for visa requirements"""
        # Use country names for better search results (simplified mapping)
        country_names = {
            "IN": "India Indian",
            "US": "United States American",
            "GB": "United Kingdom British",
            "CA": "Canada Canadian",
            "AU": "Australia Australian",
            "DE": "Germany German",
            "FR": "France French",
            "SG": "Singapore Singaporean",
            "AE": "UAE Emirates",
            "JP": "Japan Japanese",
            "CN": "China Chinese",
            # Add more as needed
        }

        dest_name = country_names.get(destination, destination)
        pass_name = country_names.get(passport, passport)

        return (
            f"{pass_name} passport visa requirements for {dest_name} "
            f"entry requirements tourist visa 2026"
        )

    async def _search_web(self, query: str) -> Optional[str]:
        """
        Perform web search (using DuckDuckGo or similar free API)

        For MVP, we'll use a simple HTTP search that doesn't require API keys.
        In production, consider using Google Custom Search, Bing API, etc.
        """
        try:
            # Using DuckDuckGo HTML search (no API key needed)
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; GeoFlightScout/0.1; +https://github.com/yourproject)"
                    },
                    timeout=15.0,
                    follow_redirects=True,
                )

                # Accept both 200 (OK) and 202 (Accepted) responses
                # DuckDuckGo may return 202 for valid searches
                if response.status_code in [200, 202]:
                    # Extract text snippets from HTML (simplified)
                    # In production, use proper HTML parsing
                    text = response.text[:3000]  # Limit to first 3000 chars
                    logger.info(f"Web search completed with status {response.status_code}")
                    return text
                else:
                    logger.warning(f"Web search returned status {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return None

    async def _summarize_with_ai(
        self, search_results: str, destination: str, passport: str
    ) -> Optional[str]:
        """
        Use Claude AI to summarize search results into concise visa guidance
        """
        try:
            prompt = f"""Based on the web search results below, provide a brief, factual summary of visa/entry requirements for {passport} passport holders traveling to {destination}.

Focus on:
- Whether a visa is required or visa-free/eVisa available
- Validity period if visa-free
- Key requirements or restrictions
- Any important notes about transit vs tourist entry

Keep it under 200 words and factual. If information is unclear, say so.

Search results:
{search_results[:2000]}

Summary:"""

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.anthropic_api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-3-haiku-20240307",  # Fast, cheap model for summaries
                        "max_tokens": 300,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    summary = data["content"][0]["text"].strip()

                    # Add AI-generated prefix
                    summary = f"[AI Research Summary] {summary}"

                    logger.info("AI summarization completed successfully")
                    return summary
                else:
                    logger.warning(f"AI API returned status {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"AI summarization failed: {e}")
            return None


# Global instance
ai_visa_research_service = AIVisaResearchService()
