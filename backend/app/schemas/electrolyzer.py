"""
Electrolyzer API schemas - defines contract between frontend and backend
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class SystemHealth(str, Enum):
    """System health status enumeration"""
    OPTIMAL = "optimal"
    DEGRADED = "degraded"
    MAINTENANCE_REQUIRED = "maintenance_required"
    FAULT = "fault"
    OFFLINE = "offline"


class ElectrolyzerStatus(BaseModel):
    """
    Real-time electrolyzer status
    
    This is the primary data model returned when querying electrolyzer state.
    Used by dashboards, partner APIs, and monitoring systems.
    """
    electrolyzer_id: str = Field(
        ..., 
        description="Unique identifier (e.g., 'NH500-ONT-001')",
        examples=["NH500-ONT-001"]
    )
    timestamp: datetime = Field(
        ..., 
        description="When this status was recorded (UTC)"
    )
    
    # Production metrics
    current_production_kg_h: float = Field(
        ..., 
        ge=0, 
        le=50, 
        description="Current H2 production rate (kg/hour)"
    )
    operating_point_pct: float = Field(
        ..., 
        ge=0, 
        le=100, 
        description="Current capacity utilization (0-100%)"
    )
    
    # Efficiency metrics
    cell_voltage_v: float = Field(
        ..., 
        ge=1.5, 
        le=2.5, 
        description="Average cell voltage (V)"
    )
    stack_current_a: float = Field(
        ..., 
        ge=0, 
        description="Stack current (Amps)"
    )
    energy_consumption_kwh_per_kg: float = Field(
        ..., 
        ge=40, 
        le=60, 
        description="Specific energy consumption (kWh/kg H2)"
    )
    power_consumption_kw: float = Field(
        ...,
        ge=0,
        description="Current power draw (kW)"
    )
    
    # System health
    system_health: SystemHealth = Field(
        ...,
        description="Overall system status"
    )
    stack_temperature_c: float = Field(
        ..., 
        ge=0, 
        le=100,
        description="Stack operating temperature (°C)"
    )
    h2_purity_pct: float = Field(
        ..., 
        ge=99.0, 
        le=100.0,
        description="Hydrogen purity percentage"
    )
    h2_pressure_bar: float = Field(
        ...,
        ge=0,
        le=35,
        description="Hydrogen output pressure (bar)"
    )
    
    # Storage (if connected)
    storage_level_kg: Optional[float] = Field(
        None, 
        ge=0,
        description="Current H2 storage level (kg)"
    )
    storage_capacity_kg: Optional[float] = Field(
        None, 
        ge=0,
        description="Maximum storage capacity (kg)"
    )
    storage_percentage: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Storage level as percentage of capacity"
    )
    
    # Availability
    available_capacity_pct: float = Field(
        ..., 
        ge=0, 
        le=100, 
        description="How much more can we ramp up? (% points)"
    )
    
    # Cost tracking (optional)
    current_electricity_price_per_mwh: Optional[float] = Field(
        None,
        ge=0,
        description="Current electricity price ($/MWh)"
    )
    estimated_cost_per_kg: Optional[float] = Field(
        None,
        ge=0,
        description="Current production cost ($/kg H2)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "electrolyzer_id": "NH500-ONT-001",
                "timestamp": "2025-11-08T14:30:00Z",
                "current_production_kg_h": 27.3,
                "operating_point_pct": 60.0,
                "cell_voltage_v": 1.92,
                "stack_current_a": 850.0,
                "energy_consumption_kwh_per_kg": 48.5,
                "power_consumption_kw": 1324.0,
                "system_health": "optimal",
                "stack_temperature_c": 68.0,
                "h2_purity_pct": 99.998,
                "h2_pressure_bar": 15.0,
                "storage_level_kg": 847.0,
                "storage_capacity_kg": 1500.0,
                "storage_percentage": 56.5,
                "available_capacity_pct": 40.0,
                "current_electricity_price_per_mwh": 45.0,
                "estimated_cost_per_kg": 2.73
            }
        }


class SetpointRequest(BaseModel):
    """
    Command to change electrolyzer production rate
    
    Partners and optimization engines use this to control the electrolyzer.
    The system will ramp to the target at the specified rate.
    """
    target_kg_h: float = Field(
        ..., 
        ge=2.25,  # 5% of 45 kg/h
        le=45.0,   # 100% of 45 kg/h
        description="Desired H2 production rate (kg/h). Must be within 5-100% of max capacity."
    )
    priority: Literal["cost", "speed", "renewable_matching", "reliability"] = Field(
        default="cost",
        description="Optimization priority for ramp trajectory"
    )
    ramp_rate_pct_per_sec: Optional[float] = Field(
        default=10.0,
        ge=0.1,
        le=10.0,
        description="Ramp rate (%/second). Max 10%/sec for NH-X series."
    )
    reason: Optional[str] = Field(
        None, 
        max_length=200,
        description="Reason for setpoint change (logging/audit)"
    )
    
    @field_validator('target_kg_h')
    @classmethod
    def validate_turndown(cls, v):
        """Enforce NH-X turndown range: 5-100% of 45 kg/h"""
        min_production = 2.25  # 5% of 45
        max_production = 45.0  # 100%
        if not (min_production <= v <= max_production):
            raise ValueError(
                f"Production must be between {min_production} and {max_production} kg/h "
                f"(5-100% of rated capacity)"
            )
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "target_kg_h": 38.5,
                "priority": "renewable_matching",
                "ramp_rate_pct_per_sec": 5.0,
                "reason": "Excess solar production available"
            }
        }


class SetpointResponse(BaseModel):
    """Response after processing setpoint command"""
    status: Literal["accepted", "rejected", "queued"] = Field(
        ...,
        description="Command status"
    )
    message: str = Field(
        ...,
        description="Human-readable status message"
    )
    estimated_time_to_target_seconds: Optional[float] = Field(
        None,
        ge=0,
        description="Estimated seconds to reach target"
    )
    projected_ramp: Optional[str] = Field(
        None,
        description="Human-readable ramp description (e.g., '60% → 95%')"
    )
    current_production_kg_h: float = Field(
        ...,
        description="Current production before ramp"
    )
    target_production_kg_h: float = Field(
        ...,
        description="Target production after ramp"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "accepted",
                "message": "Setpoint command accepted and executing",
                "estimated_time_to_target_seconds": 480,
                "projected_ramp": "60% → 85% capacity",
                "current_production_kg_h": 27.0,
                "target_production_kg_h": 38.5
            }
        }


class HistoricalDataRequest(BaseModel):
    """Query parameters for historical telemetry data"""
    electrolyzer_id: str = Field(
        ...,
        description="Electrolyzer to query"
    )
    start_time: datetime = Field(
        ...,
        description="Start of time range (UTC)"
    )
    end_time: datetime = Field(
        ...,
        description="End of time range (UTC)"
    )
    interval_minutes: int = Field(
        default=15, 
        ge=1, 
        le=60, 
        description="Data aggregation interval (minutes)"
    )
    metrics: list[str] = Field(
        default_factory=lambda: ["production", "efficiency", "temperature"],
        description="Metrics to return (production, efficiency, temperature, pressure, health)"
    )


class HistoricalDataPoint(BaseModel):
    """Single aggregated data point in time series"""
    timestamp: datetime
    production_kg_h: Optional[float] = None
    efficiency_kwh_per_kg: Optional[float] = None
    temperature_c: Optional[float] = None
    operating_point_pct: Optional[float] = None
    storage_level_kg: Optional[float] = None
    electricity_price_per_mwh: Optional[float] = None
    cost_per_kg: Optional[float] = None
