"""Pydantic schemas for API request/response validation"""
from .electrolyzer import (
    ElectrolyzerStatus,
    SetpointRequest,
    SetpointResponse,
    HistoricalDataRequest,
    HistoricalDataPoint,
    SystemHealth
)
from .optimization import (
    OptimizationRequest,
    OptimizationResponse,
    SchedulePoint,
    ElectricityPrice,
    DemandForecast
)

__all__ = [
    "ElectrolyzerStatus",
    "SetpointRequest",
    "SetpointResponse",
    "HistoricalDataRequest",
    "HistoricalDataPoint",
    "SystemHealth",
    "OptimizationRequest",
    "OptimizationResponse",
    "SchedulePoint",
    "ElectricityPrice",
    "DemandForecast",
]
