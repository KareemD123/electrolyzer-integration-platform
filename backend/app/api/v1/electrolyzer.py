"""
Electrolyzer control API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from typing import List

from app.schemas.electrolyzer import (
    ElectrolyzerStatus,
    SetpointRequest,
    SetpointResponse,
    HistoricalDataRequest,
    HistoricalDataPoint
)
from app.services.simulator_service import get_simulator

router = APIRouter(prefix="/electrolyzer", tags=["electrolyzer"])


@router.get("/{electrolyzer_id}/status", response_model=ElectrolyzerStatus)
async def get_electrolyzer_status(electrolyzer_id: str):
    """
    Get current electrolyzer status
    
    Returns real-time metrics including production rate, efficiency,
    system health, and storage levels.
    
    **Use cases:**
    - Partner dashboards polling for status
    - Operator monitoring
    - Fleet management systems
    """
    if electrolyzer_id != "NH500-ONT-001":
        raise HTTPException(status_code=404, detail=f"Electrolyzer {electrolyzer_id} not found")
    
    simulator = get_simulator()
    status = simulator.get_status()
    return status


@router.post("/{electrolyzer_id}/setpoint", response_model=SetpointResponse)
async def set_production_setpoint(
    electrolyzer_id: str,
    request: SetpointRequest
):
    """
    Set new production target
    
    Commands the electrolyzer to ramp to a new production rate.
    The system will ramp at the specified rate (max 10%/sec for NH-X).
    
    **Use cases:**
    - Partner systems optimizing production
    - Manual operator adjustments
    - Automated schedulers applying optimized plans
    """
    if electrolyzer_id != "NH500-ONT-001":
        raise HTTPException(status_code=404, detail=f"Electrolyzer {electrolyzer_id} not found")
    
    simulator = get_simulator()
    
    # Get current status before change
    current_status = simulator.get_status()
    
    # Set new target
    result = simulator.set_target(request.target_kg_h)
    
    if result["status"] == "rejected":
        return SetpointResponse(
            status="rejected",
            message=result["reason"],
            current_production_kg_h=current_status.current_production_kg_h,
            target_production_kg_h=request.target_kg_h
        )
    
    # Calculate projected ramp
    current_pct = result["current_pct"]
    target_pct = result["target_pct"]
    projected_ramp = f"{current_pct:.0f}% → {target_pct:.0f}% capacity"
    
    return SetpointResponse(
        status="accepted",
        message=f"Ramping to {request.target_kg_h} kg/h ({target_pct:.0f}% capacity)",
        estimated_time_to_target_seconds=result["ramp_time_seconds"],
        projected_ramp=projected_ramp,
        current_production_kg_h=current_status.current_production_kg_h,
        target_production_kg_h=request.target_kg_h
    )



@router.get("/{electrolyzer_id}/telemetry", response_model=List[HistoricalDataPoint])
async def get_historical_data(
    electrolyzer_id: str,
    start_time: datetime = Query(..., description="Start time (UTC)"),
    end_time: datetime = Query(..., description="End time (UTC)"),
    interval_minutes: int = Query(15, ge=1, le=60, description="Data interval")
):
    """
    Get historical telemetry data
    
    Returns time-series data for the specified time range.
    
    **Note:** In MVP, this returns simulated data. In production,
    this would query TimescaleDB for actual historical data.
    """
    if electrolyzer_id != "NH500-ONT-001":
        raise HTTPException(status_code=404, detail=f"Electrolyzer {electrolyzer_id} not found")
    
    # Validate time range
    if start_time >= end_time:
        raise HTTPException(status_code=400, detail="start_time must be before end_time")
    
    duration = end_time - start_time
    if duration > timedelta(days=7):
        raise HTTPException(status_code=400, detail="Maximum time range is 7 days")
    
    # Generate mock historical data
    # In production, this would query the database
    data_points = []
    current_time = start_time
    
    while current_time <= end_time:
        # Simulate varying production based on time of day
        hour = current_time.hour
        
        # Higher production during off-peak hours (cheaper electricity)
        if 19 <= hour or hour < 7:  # 7pm - 7am
            operating_point = 85.0 + (hour % 5) * 2
        elif 11 <= hour < 17:  # 11am - 5pm (on-peak)
            operating_point = 45.0 + (hour % 3) * 5
        else:  # mid-peak
            operating_point = 65.0 + (hour % 4) * 3
        
        production = (operating_point / 100) * 45.0
        efficiency = 48.0 + (100 - operating_point) * 0.05
        
        data_points.append(
            HistoricalDataPoint(
                timestamp=current_time,
                production_kg_h=round(production, 2),
                efficiency_kwh_per_kg=round(efficiency, 2),
                temperature_c=round(60 + (operating_point / 100) * 15, 1),
                operating_point_pct=round(operating_point, 1)
            )
        )
        
        current_time += timedelta(minutes=interval_minutes)
    
    return data_points


@router.get("/list")
async def list_electrolyzers():
    """
    List all available electrolyzers
    
    Returns basic info about all electrolyzers in the system.
    """
    # In production, this would query the database
    return [
        {
            "electrolyzer_id": "NH500-ONT-001",
            "site_name": "Ontario Distribution Center",
            "model": "NH-500",
            "status": "operational",
            "location": "Toronto, ON"
        }
    ]
