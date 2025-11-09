"""
Optimization API schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class ElectricityPrice(BaseModel):
    """Electricity price at a specific time"""
    timestamp: datetime = Field(
        ...,
        description="Time this price applies (UTC)"
    )
    price_per_mwh: float = Field(
        ..., 
        ge=0, 
        description="Electricity price ($/MWh)"
    )
    source: str = Field(
        default="IESO", 
        description="Price source (IESO, AESO, ERCOT, etc.)"
    )
    price_type: Literal["off_peak", "mid_peak", "on_peak", "spot"] = Field(
        default="spot",
        description="Price category (for TOU markets)"
    )


class DemandForecast(BaseModel):
    """Hydrogen demand forecast for a time period"""
    timestamp: datetime = Field(
        ...,
        description="Time this demand applies (UTC)"
    )
    demand_kg_h: float = Field(
        ..., 
        ge=0,
        description="Expected H2 consumption rate (kg/h)"
    )
    confidence: Optional[float] = Field(
        None,
        ge=0,
        le=1,
        description="Forecast confidence (0-1)"
    )


class OptimizationConstraints(BaseModel):
    """Constraints for optimization problem"""
    current_storage_kg: float = Field(
        ..., 
        ge=0,
        description="Current H2 storage level (kg)"
    )
    min_storage_kg: float = Field(
        default=500.0,
        ge=0,
        description="Minimum storage safety buffer (kg)"
    )
    max_storage_kg: float = Field(
        default=1500.0,
        ge=0,
        description="Maximum storage capacity (kg)"
    )
    max_grid_power_kw: Optional[float] = Field(
        None,
        ge=0,
        description="Maximum grid power draw (kW). None = unlimited"
    )



class OptimizationRequest(BaseModel):
    """
    Request to optimize production schedule
    
    This is the main input for the optimization engine. It takes forecasts
    and constraints, then returns an optimal production schedule.
    """
    electrolyzer_id: str = Field(
        ...,
        description="Electrolyzer to optimize"
    )
    horizon_hours: int = Field(
        default=24, 
        ge=1, 
        le=168, 
        description="Optimization horizon (hours ahead). Default 24h, max 7 days."
    )
    
    # Forecasts
    electricity_prices: List[ElectricityPrice] = Field(
        ..., 
        min_length=1,
        description="Electricity price forecast for horizon"
    )
    demand_forecast: Optional[List[DemandForecast]] = Field(
        None,
        description="H2 demand forecast (optional, assumes constant if not provided)"
    )
    renewable_available_mw: Optional[List[float]] = Field(
        None,
        description="Renewable energy availability by hour (MW)"
    )
    
    # Constraints
    constraints: OptimizationConstraints = Field(
        default_factory=OptimizationConstraints,
        description="Operating constraints"
    )
    
    # Optimization parameters
    objective: Literal["minimize_cost", "maximize_renewable_use", "meet_demand"] = Field(
        default="minimize_cost",
        description="Primary optimization objective"
    )
    allow_grid_purchases: bool = Field(
        default=True,
        description="Allow grid power purchases vs renewable-only"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "electrolyzer_id": "NH500-ONT-001",
                "horizon_hours": 24,
                "electricity_prices": [
                    {
                        "timestamp": "2025-11-08T00:00:00Z",
                        "price_per_mwh": 35.0,
                        "source": "IESO",
                        "price_type": "off_peak"
                    }
                ],
                "constraints": {
                    "current_storage_kg": 850.0,
                    "min_storage_kg": 500.0,
                    "max_storage_kg": 1500.0
                },
                "objective": "minimize_cost"
            }
        }



class SchedulePoint(BaseModel):
    """Single point in optimized schedule"""
    hour: int = Field(
        ..., 
        ge=0, 
        le=167,
        description="Hour offset from now (0 = current hour)"
    )
    timestamp: datetime = Field(
        ...,
        description="Absolute timestamp (UTC)"
    )
    operating_point_pct: float = Field(
        ..., 
        ge=5, 
        le=100,
        description="Optimal operating point (%)"
    )
    production_kg_h: float = Field(
        ...,
        ge=0,
        description="H2 production rate (kg/h)"
    )
    power_consumption_kw: float = Field(
        ...,
        ge=0,
        description="Expected power draw (kW)"
    )
    electricity_price_per_mwh: float = Field(
        ...,
        ge=0,
        description="Electricity price for this hour ($/MWh)"
    )
    estimated_cost_per_kg: float = Field(
        ...,
        ge=0,
        description="Production cost ($/kg H2)"
    )
    storage_level_kg: float = Field(
        ...,
        ge=0,
        description="Projected storage level (kg)"
    )
    is_renewable: bool = Field(
        default=False,
        description="Is this hour powered by renewables?"
    )


class OptimizationSummary(BaseModel):
    """Summary statistics for optimization result"""
    total_production_kg: float = Field(
        ...,
        description="Total H2 produced over horizon (kg)"
    )
    total_energy_kwh: float = Field(
        ...,
        description="Total energy consumed (kWh)"
    )
    total_cost_usd: float = Field(
        ...,
        description="Total electricity cost ($)"
    )
    average_cost_per_kg: float = Field(
        ...,
        description="Average production cost ($/kg)"
    )
    renewable_percentage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentage of energy from renewables"
    )
    average_efficiency_kwh_per_kg: float = Field(
        ...,
        description="Average energy efficiency (kWh/kg)"
    )
    
    # Savings vs baseline
    baseline_cost_usd: float = Field(
        ...,
        description="Cost if running at constant 60% capacity"
    )
    savings_usd: float = Field(
        ...,
        description="Cost savings vs baseline ($)"
    )
    savings_percentage: float = Field(
        ...,
        description="Percentage cost reduction vs baseline"
    )
    
    # Storage metrics
    min_storage_kg: float = Field(
        ...,
        description="Minimum storage level reached (kg)"
    )
    max_storage_kg: float = Field(
        ...,
        description="Maximum storage level reached (kg)"
    )
    storage_violations: int = Field(
        default=0,
        description="Number of times storage limits violated (should be 0)"
    )


class OptimizationResponse(BaseModel):
    """
    Complete optimization result
    
    Returns the optimal production schedule plus summary statistics.
    """
    electrolyzer_id: str
    generated_at: datetime = Field(
        ...,
        description="When this optimization was generated (UTC)"
    )
    horizon_hours: int
    
    schedule: List[SchedulePoint] = Field(
        ...,
        description="Hour-by-hour optimal production schedule"
    )
    
    summary: OptimizationSummary = Field(
        ...,
        description="Summary statistics and savings"
    )
    
    # Metadata
    objective_used: str = Field(
        ...,
        description="Optimization objective that was applied"
    )
    computation_time_seconds: float = Field(
        ...,
        description="How long optimization took"
    )
    solver_status: str = Field(
        ...,
        description="Optimization solver status (success, infeasible, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "electrolyzer_id": "NH500-ONT-001",
                "generated_at": "2025-11-08T14:30:00Z",
                "horizon_hours": 24,
                "schedule": [
                    {
                        "hour": 0,
                        "timestamp": "2025-11-08T14:00:00Z",
                        "operating_point_pct": 60.0,
                        "production_kg_h": 27.0,
                        "power_consumption_kw": 1310.0,
                        "electricity_price_per_mwh": 45.0,
                        "estimated_cost_per_kg": 2.85,
                        "storage_level_kg": 850.0,
                        "is_renewable": False
                    }
                ],
                "summary": {
                    "total_production_kg": 800.0,
                    "total_energy_kwh": 38400.0,
                    "total_cost_usd": 2140.0,
                    "average_cost_per_kg": 2.68,
                    "renewable_percentage": 78.5,
                    "average_efficiency_kwh_per_kg": 48.0,
                    "baseline_cost_usd": 2520.0,
                    "savings_usd": 380.0,
                    "savings_percentage": 15.1,
                    "min_storage_kg": 520.0,
                    "max_storage_kg": 1380.0,
                    "storage_violations": 0
                },
                "objective_used": "minimize_cost",
                "computation_time_seconds": 0.84,
                "solver_status": "optimal"
            }
        }
