# Currency exchange rate service
import httpx
import logging
from datetime import datetime, timezone

from ..core.config import get_settings


logger = logging.getLogger(__name__)


class CurrencyService:
    """Service for fetching currency exchange rates from ExchangeRate-API."""

    def __init__(self):
        self.settings = get_settings()
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"User-Agent": "urWallet/1.0"}
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def fetch_rates(self, base_currency: str = "USD") -> dict | None:
        """
        Fetch latest exchange rates from the API.
        
        Returns dict with rates data or None if failed.
        """
        if not self.settings.fx_api_key:
            logger.error("FX_API_KEY not configured")
            return None

        try:
            url = f"{self.settings.fx_api_base_url}/{self.settings.fx_api_key}/latest/{base_currency.upper()}"
            logger.info(f"Fetching rates for {base_currency}")

            response = await self.client.get(url)
            response.raise_for_status()

            data = response.json()

            if data.get("result") != "success":
                logger.error(f"FX API returned error: {data}")
                return None

            if "conversion_rates" not in data:
                logger.error("FX API response missing conversion_rates")
                return None

            logger.info(f"Fetched {len(data['conversion_rates'])} currency rates")
            return {
                "base_currency": base_currency.upper(),
                "rates": data["conversion_rates"],
                "fetched_at": datetime.now(timezone.utc)
            }

        except httpx.TimeoutException:
            logger.error("Timeout fetching rates from FX API")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching rates: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Unexpected error fetching rates: {e}")

        return None

    async def get_rate(self, from_currency: str, to_currency: str) -> float | None:
        """Get conversion rate from one currency to another."""
        rates_data = await self.fetch_rates(base_currency=from_currency)
        if not rates_data:
            return None

        to_currency = to_currency.upper()
        if to_currency not in rates_data["rates"]:
            logger.error(f"Currency {to_currency} not found in rates")
            return None

        return rates_data["rates"][to_currency]

    async def convert(
        self, amount: float, from_currency: str, to_currency: str
    ) -> dict | None:
        """Convert amount from one currency to another."""
        rate = await self.get_rate(from_currency, to_currency)
        if rate is None:
            return None

        converted = round(amount * rate, 2)
        return {
            "amount": amount,
            "from_currency": from_currency.upper(),
            "to_currency": to_currency.upper(),
            "rate": rate,
            "converted_amount": converted,
            "fetched_at": datetime.now(timezone.utc).isoformat()
        }
