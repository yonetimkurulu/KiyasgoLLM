"""
Lifecycle Scorer
Ürünün yaşam döngüsündeki yerini belirler.
"""
from datetime import datetime, timedelta
from src.models.product import LifecycleSignal


class LifecycleScorer:
    """
    Determine product lifecycle stage.
    
    Stages:
    - launch: New product, premium pricing
    - growth: Gaining popularity
    - mature: Stable market position
    - decline: New model coming
    - clearance: Stock clearing
    - discontinued: No longer produced
    """
    
    def determine_stage(self, product_data: dict) -> LifecycleSignal:
        """
        Determine lifecycle stage from product data.
        
        Args:
            product_data: Product information dict
            
        Returns:
            LifecycleSignal with stage and context
        """
        release_date = product_data.get("release_date")
        
        # Calculate months since launch
        months_since_launch = self._calculate_months_since_launch(release_date)
        
        # Check for successor announcement (mock)
        successor_announced = product_data.get("successor_announced", False)
        expected_replacement = product_data.get("expected_replacement")
        
        # Get stock trend (mock)
        stock_trend = product_data.get("stock_trend", "normal")
        
        # Get price trend (mock)
        price_trend = product_data.get("price_trend", "stable")
        
        # Determine stage
        stage = self._classify_stage(
            months_since_launch,
            successor_announced,
            stock_trend,
            price_trend,
        )
        
        return LifecycleSignal(
            stage=stage,
            months_since_launch=months_since_launch,
            successor_announced=successor_announced,
            expected_replacement=expected_replacement,
            confidence=0.85,
        )
    
    def _calculate_months_since_launch(self, release_date: str) -> int:
        """Calculate months since product launch."""
        if not release_date:
            return 12  # Assume 1 year if unknown
        
        try:
            # Handle various date formats
            if len(release_date) == 7:  # YYYY-MM
                release = datetime.strptime(release_date, "%Y-%m")
            elif len(release_date) == 10:  # YYYY-MM-DD
                release = datetime.strptime(release_date, "%Y-%m-%d")
            else:
                return 12
            
            now = datetime.now()
            months = (now.year - release.year) * 12 + (now.month - release.month)
            return max(months, 0)
            
        except ValueError:
            return 12
    
    def _classify_stage(
        self,
        months: int,
        successor_announced: bool,
        stock_trend: str,
        price_trend: str,
    ) -> str:
        """Classify product into lifecycle stage."""
        
        # Launch phase: First 2 months, no successor
        if months < 2 and not successor_announced:
            return "launch"
        
        # Growth phase: 2-6 months, price declining normally
        if months < 6 and price_trend in ["declining", "stable"]:
            return "growth"
        
        # Clearance: Stock critically low
        if stock_trend == "critical_low":
            return "clearance"
        
        # Discontinued: Zero stock, old product
        if stock_trend == "zero" and months > 12:
            return "discontinued"
        
        # Decline: Successor announced or product old
        if successor_announced:
            return "decline"
        
        if months > 18 and price_trend == "declining":
            return "decline"
        
        # Mature: Default stable state
        return "mature"
