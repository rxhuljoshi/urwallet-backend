# Groq AI service for categorization and insights
from collections import defaultdict
from typing import Optional, List
import logging

from groq import Groq

from ..core.config import get_settings

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        settings = get_settings()
        self.client = Groq(api_key=settings.groq_api_key) if settings.groq_api_key else None
        self.model = "llama-3.3-70b-versatile"
    
    @property
    def enabled(self) -> bool:
        return self.client is not None
    
    async def categorize_transaction(self, amount: float, remarks: str) -> str:
        if not self.enabled:
            return "Other"
        
        try:
            prompt = f"""Given this transaction:
Amount: {amount}
Remarks: {remarks}

Categorize it into ONE of these categories: Food, Rent, Travel, Bills, Shopping, Savings, Investment, Other

Respond with ONLY the category name, nothing else."""
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=20
            )
            
            category = completion.choices[0].message.content.strip()
            valid = ["Food", "Rent", "Travel", "Bills", "Shopping", "Savings", "Investment", "Other"]
            
            return category if category in valid else "Other"
        except Exception as e:
            logger.error(f"AI categorization error: {e}")
            return "Other"
    
    async def generate_monthly_insights(
        self,
        user_id: str,
        month: int,
        year: int,
        transactions: List[dict],
        budget: Optional[float] = None,
        currency: str = "USD"
    ) -> str:
        if not self.enabled or not transactions:
            return "No insights available."
        
        # Currency symbols for display
        symbols = {"USD": "$", "EUR": "€", "GBP": "£", "INR": "₹", "JPY": "¥", 
                   "AUD": "A$", "CAD": "C$", "CHF": "CHF", "CNY": "¥"}
        sym = symbols.get(currency, currency)
        
        try:
            total_expense = sum(t["amount"] for t in transactions if t["category"] not in ["Savings", "Investment"])
            total_savings = sum(t["amount"] for t in transactions if t["category"] == "Savings")
            total_investment = sum(t["amount"] for t in transactions if t["category"] == "Investment")
            
            category_totals = defaultdict(float)
            for t in transactions:
                category_totals[t["category"]] += t["amount"]
            
            category_summary = "\n".join([f"- {cat}: {sym}{amt:.2f}" for cat, amt in category_totals.items()])
            budget_info = f"Monthly budget: {sym}{budget}\n" if budget else ""
            
            prompt = f"""Analyze this monthly expense data and provide insights:

Month: {month}/{year}
Currency: {currency} ({sym})
{budget_info}Total Expenses: {sym}{total_expense:.2f}
Total Savings: {sym}{total_savings:.2f}
Total Investments: {sym}{total_investment:.2f}

Category Breakdown:
{category_summary}

Provide:
1. A brief plain-English spending summary (2-3 sentences)
2. Identify any overspending categories (percentage of total)
3. Calculate savings rate if applicable
4. ONE blunt, actionable suggestion to improve finances

Use the {sym} symbol for all amounts. Be direct and specific with numbers. Keep it under 150 words."""
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            
            return completion.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"AI insights generation error: {e}")
            return "Unable to generate insights at this time."
    
    async def detect_spending_spike(
        self,
        current_month_transactions: List[dict],
        previous_month_transactions: List[dict]
    ) -> Optional[str]:
        if not self.enabled:
            return None
        
        try:
            current_expenses = [t for t in current_month_transactions if t["category"] not in ["Savings", "Investment"]]
            prev_expenses = [t for t in previous_month_transactions if t["category"] not in ["Savings", "Investment"]]
            
            if not prev_expenses:
                return None
            
            current_total = sum(t["amount"] for t in current_expenses)
            prev_total = sum(t["amount"] for t in prev_expenses)
            
            if current_total <= prev_total * 1.2:
                return None
            
            increase_pct = ((current_total - prev_total) / prev_total) * 100
            
            prompt = f"""Spending increased by {increase_pct:.1f}% this month compared to last month.

Current month total: {current_total:.2f}
Previous month total: {prev_total:.2f}

Generate a brief warning message (1-2 sentences) about this spike. Be direct and specific."""
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )
            
            return completion.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Spike detection error: {e}")
            return None


_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
