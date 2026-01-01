import logging
from typing import Optional

import httpx

from app.models import VisaBaseline
from app.settings import settings

logger = logging.getLogger(__name__)


class TravelBriefingClient:
    """Client for TravelBriefing API (free baseline visa/entry info)"""

    def __init__(self):
        self.base_url = settings.travelbriefing_base_url

    async def get_visa_info(
        self, destination_country: str, passport_nationality: str
    ) -> Optional[VisaBaseline]:
        """
        Get baseline visa/entry information for a destination

        Args:
            destination_country: Destination country ISO code (e.g., "IN")
            passport_nationality: Passport country ISO code (e.g., "US")

        Returns:
            VisaBaseline object or None if data unavailable
        """
        try:
            async with httpx.AsyncClient() as client:
                # TravelBriefing API endpoint
                # Note: API may be limited; this is best-effort
                response = await client.get(
                    f"{self.base_url}/{destination_country.lower()}.json",
                    timeout=10.0,
                    follow_redirects=True,
                )

                if response.status_code != 200:
                    logger.warning(
                        f"TravelBriefing API returned {response.status_code} for {destination_country}"
                    )
                    return self._create_fallback_baseline(destination_country)

                data = response.json()

                # Extract visa/entry information
                # TravelBriefing structure varies; extract what we can
                visa_text = "Unknown - please verify with official sources"

                # Try to extract visa information
                if "visa" in data:
                    visa_data = data["visa"]
                    if isinstance(visa_data, dict):
                        visa_text = visa_data.get("text", visa_text)
                    elif isinstance(visa_data, str):
                        visa_text = visa_data

                # Try to get general entry info
                if "advise" in data and isinstance(data["advise"], dict):
                    advise = data["advise"]
                    if "text" in advise:
                        visa_text = f"{visa_text}\n\nGeneral advice: {advise['text']}"

                # Limit length
                if len(visa_text) > 500:
                    visa_text = visa_text[:497] + "..."

                return VisaBaseline(
                    destination_entry_summary=visa_text,
                    source="travelbriefing",
                    disclaimer="Best-effort information from TravelBriefing. Always verify with official embassy/consulate sources before booking.",
                )

        except Exception as e:
            logger.warning(f"Failed to fetch TravelBriefing data: {e}")
            return self._create_fallback_baseline(destination_country)

    def _create_fallback_baseline(self, destination_country: str) -> VisaBaseline:
        """Create fallback baseline when API is unavailable"""
        return VisaBaseline(
            destination_entry_summary=f"Visa information for {destination_country} unavailable. Please check official government travel advisory websites.",
            source="fallback",
            disclaimer="IMPORTANT: Verify all visa and entry requirements with official sources (embassy, consulate, or government travel websites) before booking.",
        )


# Global client instance
travelbriefing_client = TravelBriefingClient()
