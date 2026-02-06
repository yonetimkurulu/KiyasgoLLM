"""
Price Volatility Analyzer
Fiyat oynaklığını analiz eder.
"""
from src.models.product import PriceVolatilitySignal
import statistics


class PriceVolatilityAnalyzer:
    """
    Analyze price volatility and trends.
    
    Calculates:
    - Standard deviation of prices
    - Price change frequency
    - Trend direction
    - Buy timing recommendation
    """
    
    def analyze(self, price_history: list[dict]) -> PriceVolatilitySignal:
        """
        Analyze price history for volatility.
        
        Args:
            price_history: List of {date, price} dicts
            
        Returns:
            PriceVolatilitySignal with analysis results
        """
        if not price_history or len(price_history) < 7:
            return PriceVolatilitySignal(
                score=50,
                stability="unknown",
                confidence=0.5,
            )
        
        prices = [p.get("price", 0) for p in price_history]
        
        # Calculate volatility score
        volatility_score = self._calculate_volatility(prices)
        
        # Determine stability tier
        stability = self._determine_stability(volatility_score)
        
        # Calculate trend
        trend = self._calculate_trend(prices)
        
        # Weekly change
        weekly_change = self._calculate_weekly_change(prices)
        
        # Monthly range
        monthly_range = self._calculate_monthly_range(prices[-30:] if len(prices) >= 30 else prices)
        
        # Buy recommendation
        recommendation = self._determine_recommendation(trend, volatility_score, weekly_change)
        
        return PriceVolatilitySignal(
            score=volatility_score,
            stability=stability,
            trend=trend,
            weekly_change=weekly_change,
            monthly_range=monthly_range,
            recommendation=recommendation,
            confidence=0.82,
        )
    
    def _calculate_volatility(self, prices: list[int]) -> int:
        """
        Calculate volatility score (0-100).
        
        Higher score = more volatile
        """
        if len(prices) < 2:
            return 50
        
        # Calculate percentage changes
        changes = []
        for i in range(1, len(prices)):
            if prices[i-1] > 0:
                change = abs(prices[i] - prices[i-1]) / prices[i-1]
                changes.append(change)
        
        if not changes:
            return 0
        
        # Standard deviation of changes
        std_dev = statistics.stdev(changes) if len(changes) > 1 else 0
        
        # Change frequency (how often price changes)
        non_zero_changes = sum(1 for c in changes if c > 0.01)  # >1% change
        change_freq = non_zero_changes / len(changes)
        
        # Combine into score (0-100)
        # std_dev of 0.05 (5%) = ~50 score
        volatility = int(
            (std_dev * 100 * 0.6) +  # Magnitude weight
            (change_freq * 100 * 0.4)  # Frequency weight
        )
        
        return min(volatility, 100)
    
    def _determine_stability(self, score: int) -> str:
        """Determine stability tier from score."""
        if score <= 25:
            return "stable"
        elif score <= 50:
            return "moderate"
        else:
            return "volatile"
    
    def _calculate_trend(self, prices: list[int]) -> str:
        """Calculate price trend direction."""
        if len(prices) < 7:
            return "stable"
        
        # Compare recent week vs previous week
        recent = sum(prices[-7:]) / 7
        previous = sum(prices[-14:-7]) / 7 if len(prices) >= 14 else sum(prices[:7]) / 7
        
        if previous == 0:
            return "stable"
        
        change = (recent - previous) / previous
        
        if change > 0.03:  # >3% increase
            return "rising"
        elif change < -0.03:  # >3% decrease
            return "declining"
        else:
            return "stable"
    
    def _calculate_weekly_change(self, prices: list[int]) -> float:
        """Calculate weekly percentage change."""
        if len(prices) < 7:
            return 0.0
        
        current = prices[-1]
        week_ago = prices[-7]
        
        if week_ago == 0:
            return 0.0
        
        return round((current - week_ago) / week_ago * 100, 1)
    
    def _calculate_monthly_range(self, prices: list[int]) -> dict:
        """Calculate min/max prices in period."""
        if not prices:
            return {"min": 0, "max": 0}
        
        return {
            "min": min(prices),
            "max": max(prices),
        }
    
    def _determine_recommendation(self, trend: str, volatility: int, weekly_change: float) -> str:
        """Determine buy timing recommendation."""
        # Declining trend with low volatility = wait
        if trend == "declining" and volatility < 40:
            return "wait"
        
        # Rising trend = buy now before it gets more expensive
        if trend == "rising" and weekly_change > 2:
            return "buy_now"
        
        # Stable and low volatility = good time to buy
        if trend == "stable" and volatility < 30:
            return "buy_now"
        
        # High volatility = monitor
        if volatility > 60:
            return "monitor"
        
        return "monitor"
