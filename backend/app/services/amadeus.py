import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx

from app.models import CabinClass, SearchRequest
from app.settings import settings

logger = logging.getLogger(__name__)


class AmadeusClient:
    """Client for Amadeus Self-Service API"""

    def __init__(self):
        self.base_url = settings.amadeus_base_url
        self.client_id = settings.amadeus_client_id
        self.client_secret = settings.amadeus_client_secret
        self._token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    async def _get_access_token(self) -> str:
        """Get OAuth2 access token with caching"""
        now = datetime.utcnow()

        # Return cached token if still valid
        if self._token and self._token_expires_at and now < self._token_expires_at:
            return self._token

        # Request new token
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/security/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            self._token = data["access_token"]
            # Set expiry with 60 second buffer
            expires_in = data.get("expires_in", 1799)
            self._token_expires_at = now + timedelta(seconds=expires_in - 60)

            logger.info("Obtained new Amadeus access token")
            return self._token

    async def search_flights(self, request: SearchRequest) -> list[dict[str, Any]]:
        """
        Search for flight offers using Amadeus Flight Offers Search API

        Returns list of raw flight offer dictionaries
        """
        token = await self._get_access_token()

        params = {
            "originLocationCode": request.origin,
            "destinationLocationCode": request.destination,
            "departureDate": request.date,
            "adults": request.adults,
            "max": 250,  # Get up to 250 offers for better sorting
            "currencyCode": "USD",
        }

        # Add cabin class if not economy
        if request.cabin != CabinClass.ECONOMY:
            params["travelClass"] = request.cabin.value

        # Add max stops if specified
        if request.max_stops < 2:
            params["maxStops"] = request.max_stops

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/v2/shopping/flight-offers",
                params=params,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
                timeout=60.0,
            )

            if response.status_code != 200:
                logger.error(
                    f"Amadeus API error: {response.status_code} - {response.text}"
                )
                response.raise_for_status()

            data = response.json()
            offers = data.get("data", [])
            logger.info(f"Retrieved {len(offers)} flight offers from Amadeus")
            return offers


# Global client instance
amadeus_client = AmadeusClient()
