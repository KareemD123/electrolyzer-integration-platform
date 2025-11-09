"""
Optimization API endpoints
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
import json
from pathlib import Path

from app.schemas.optimization import OptimizationRequest, OptimizationResponse, ElectricityPrice
from app.services.optimization_service import get_optimizer
from app.config import settings

router = APIRouter(prefix="/optimize", tags=["optimization"])


@router.post("", response_model=OptimizationResponse)
async def optimize_production_schedule(request: OptimizationRequest):
    """
    Optimize production schedule
    
    Takes electricity price forecasts, demand forecasts, and constraints,
    then returns an optimal hour-by-hour production schedule.
    
    **Use cases:**
    - Operator requesting optimized schedule for next 24 hours
    - Automated scheduler running daily optimization
    - What-if scenario analysis
    """
    optimizer = get_optimizer()
    
    try:
        result = optimizer.optimize_schedule(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.get("/quick-optimize/{electrolyzer_id}")
async def quick_optimize(electrolyzer_id: str):
    """
    Quick optimization using default Ontario pricing
    
    Convenience endpoint that uses pre-loaded Ontario TOU prices
    and typical demand patterns. Good for demos.
    """
    if electrolyzer_id != "NH500-ONT-001":
        raise HTTPException(status_code=404, detail="Electrolyzer not found")
    
    # Load Ontario prices
    price_path = Path(settings.DATA_DIR) / "ontario_prices.json"
    with open(price_path) as f:
        price_data = json.load(f)
    
    # Build 24-hour price forecast
    now = datetime.utcnow()
    prices = []
    for hour_data in price_data["sample_day"]:
        prices.append(ElectricityPrice(
            timestamp=now + timedelta(hours=hour_data["hour"]),
            price_per_mwh=hour_data["price_per_mwh"],
            source="IESO",
            price_type=hour_data["type"]
        ))
    
    # Create request
    from app.schemas.optimization import OptimizationConstraints
    request = OptimizationRequest(
        electrolyzer_id=electrolyzer_id,
        horizon_hours=24,
        electricity_prices=prices,
        constraints=OptimizationConstraints(
            current_storage_kg=850.0,
            min_storage_kg=500.0,
            max_storage_kg=1500.0
        ),
        objective="minimize_cost"
    )
    
    # Optimize
    optimizer = get_optimizer()
    return optimizer.optimize_schedule(request)
