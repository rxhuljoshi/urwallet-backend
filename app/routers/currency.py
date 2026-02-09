# Currency conversion endpoints
from fastapi import APIRouter, HTTPException, Query
import logging
import re

from ..services.currency import CurrencyService


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/currency", tags=["currency"])


def validate_currency_code(currency: str) -> str:
    """Normalize and validate a 3-letter currency code."""
    if not currency:
        raise HTTPException(status_code=400, detail="Currency code is required")
    
    currency = currency.upper().strip()
    
    if not re.match(r'^[A-Z]{3}$', currency):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid currency code '{currency}'. Must be 3 letters (e.g., USD, EUR)."
        )
    
    return currency


@router.get("/rates/{currency}")
async def get_rates(currency: str):
    """
    Get conversion rates from a currency to all others.
    
    Pass a 3-letter currency code (e.g., USD, EUR, INR) and get
    its value converted to all other supported currencies.
    """
    currency = validate_currency_code(currency)
    
    async with CurrencyService() as service:
        rates_data = await service.fetch_rates(base_currency=currency)
        
        if not rates_data:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to fetch rates for {currency}. Check your FX_API_KEY."
            )
        
        return {
            "from_currency": currency,
            "conversions": rates_data["rates"],
            "fetched_at": rates_data["fetched_at"].isoformat(),
            "total_currencies": len(rates_data["rates"]),
            "message": f"1 {currency} equals the following amounts in other currencies"
        }


@router.get("/convert")
async def convert_currency(
    amount: float = Query(..., description="Amount to convert"),
    from_currency: str = Query(..., alias="from", description="Source currency code"),
    to_currency: str = Query(..., alias="to", description="Target currency code")
):
    """
    Convert an amount from one currency to another.
    
    Example: /api/currency/convert?amount=100&from=USD&to=EUR
    """
    from_currency = validate_currency_code(from_currency)
    to_currency = validate_currency_code(to_currency)
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    async with CurrencyService() as service:
        result = await service.convert(amount, from_currency, to_currency)
        
        if not result:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to convert {from_currency} to {to_currency}. Check your FX_API_KEY."
            )
        
        return result
