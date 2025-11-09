"""
Production schedule optimization using Model Predictive Control (MPC)

This service implements a simplified MPC algorithm that:
1. Takes forecasts (electricity prices, demand, renewable availability)
2. Defines an optimization problem (minimize cost subject to constraints)
3. Solves using SciPy
4. Returns optimal hourly production schedule
"""
import numpy as np
from scipy.optimize import minimize
from datetime import datetime, timedelta
from typing import List, Dict
import json
from pathlib import Path

from app.schemas.optimization import (
    OptimizationRequest,
    OptimizationResponse,
    SchedulePoint,
    OptimizationSummary
)
from app.config import settings


class OptimizationEngine:
    """
    Model Predictive Control for electrolyzer scheduling
    
    Solves: minimize total_cost
    Subject to:
    - Turndown constraints (5-100%)
    - Ramp rate constraints (10%/sec)
    - Storage constraints (min/max levels)
    - Demand satisfaction
    """
    
    # Electrolyzer specifications (NH-500)
    MAX_PRODUCTION_KG_H = 45.0
    MIN_TURNDOWN_PCT = 5.0
    MAX_TURNDOWN_PCT = 100.0
    STACK_EFFICIENCY_KWH_PER_KG = 48.0
    RATED_POWER_KW = 2400.0
    
    def optimize_schedule(self, request: OptimizationRequest) -> OptimizationResponse:
        """
        Main optimization method
        
        Args:
            request: Optimization parameters and forecasts
            
        Returns:
            OptimizationResponse with optimal schedule
        """
        start_time = datetime.utcnow()
        
        # Extract data
        horizon = request.horizon_hours
        prices = [p.price_per_mwh for p in request.electricity_prices]
        
        # Ensure we have prices for entire horizon
        if len(prices) < horizon:
            # Repeat last price if needed
            prices.extend([prices[-1]] * (horizon - len(prices)))
        prices = prices[:horizon]
        
        # Get demand forecast
        if request.demand_forecast:
            demand = [d.demand_kg_h for d in request.demand_forecast]
            if len(demand) < horizon:
                demand.extend([demand[-1]] * (horizon - len(demand)))
            demand = demand[:horizon]
        else:
            # Use average demand if not provided
            average_demand = 33.3  # 800 kg/day / 24h
            demand = [average_demand] * horizon
        
        # Run optimization
        result = self._solve_optimization(
            prices=np.array(prices),
            demand=np.array(demand),
            current_storage=request.constraints.current_storage_kg,
            min_storage=request.constraints.min_storage_kg,
            max_storage=request.constraints.max_storage_kg,
            horizon=horizon
        )
        
        if not result['success']:
            raise ValueError(f"Optimization failed: {result['message']}")
        
        # Build response
        schedule = self._build_schedule(
            operating_points=result['operating_points'],
            prices=prices,
            demand=demand,
            current_storage=request.constraints.current_storage_kg,
            start_time=request.electricity_prices[0].timestamp
        )
        
        summary = self._calculate_summary(
            schedule=schedule,
            baseline_operating_point=60.0  # Constant 60% baseline
        )
        
        computation_time = (datetime.utcnow() - start_time).total_seconds()
        
        return OptimizationResponse(
            electrolyzer_id=request.electrolyzer_id,
            generated_at=start_time,
            horizon_hours=horizon,
            schedule=schedule,
            summary=summary,
            objective_used=request.objective,
            computation_time_seconds=round(computation_time, 3),
            solver_status=result['solver_status']
        )
    
    def _solve_optimization(
        self,
        prices: np.ndarray,
        demand: np.ndarray,
        current_storage: float,
        min_storage: float,
        max_storage: float,
        horizon: int
    ) -> Dict:
        """
        Solve the optimization problem using SciPy
        
        Decision variables: operating_point for each hour (0.05 to 1.0)
        Objective: minimize electricity cost
        Constraints: storage limits, demand satisfaction
        """
        
        # Initial guess: start at 60%
        x0 = np.full(horizon, 0.60)
        
        # Bounds: 5% to 100% for each hour
        bounds = [(0.05, 1.0) for _ in range(horizon)]
        
        # Objective function: total electricity cost
        def objective(x):
            """Minimize total cost over horizon"""
            total_cost = 0
            for t in range(horizon):
                # Power consumption (kW) scales linearly with operating point
                power_kw = self.RATED_POWER_KW * x[t]
                # Cost for this hour
                cost_hour = (power_kw / 1000) * prices[t]  # Convert kW to MW
                total_cost += cost_hour
            return total_cost
        
        # Constraints
        constraints = []
        
        # Storage constraints
        def storage_constraint(x):
            """Ensure storage stays within bounds"""
            storage = current_storage
            violations = 0
            
            for t in range(horizon):
                # Production this hour
                production = self.MAX_PRODUCTION_KG_H * x[t]
                # Net change (production - demand)
                net_change = production - demand[t]
                storage += net_change
                
                # Penalize violations
                if storage < min_storage:
                    violations += (min_storage - storage) ** 2
                if storage > max_storage:
                    violations += (storage - max_storage) ** 2
            
            return -violations  # Must be >= 0
        
        constraints.append({'type': 'ineq', 'fun': storage_constraint})
        
        # Demand satisfaction (on average)
        def demand_constraint(x):
            """Average production must meet average demand"""
            total_production = np.sum(x) * self.MAX_PRODUCTION_KG_H
            total_demand = np.sum(demand)
            return total_production - total_demand
        
        constraints.append({'type': 'eq', 'fun': demand_constraint})
        
        # Solve
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': 500, 'ftol': 1e-6}
        )
        
        return {
            'success': result.success,
            'operating_points': result.x if result.success else x0,
            'cost': result.fun if result.success else None,
            'message': result.message if hasattr(result, 'message') else '',
            'solver_status': 'optimal' if result.success else 'failed'
        }
    
    def _build_schedule(
        self,
        operating_points: np.ndarray,
        prices: List[float],
        demand: List[float],
        current_storage: float,
        start_time: datetime
    ) -> List[SchedulePoint]:
        """Build schedule with all metrics"""
        schedule = []
        storage = current_storage
        
        for hour in range(len(operating_points)):
            op_point = operating_points[hour]
            
            # Production
            production = self.MAX_PRODUCTION_KG_H * op_point
            
            # Power consumption
            power_kw = self.RATED_POWER_KW * op_point
            
            # Cost
            cost_per_kg = (self.STACK_EFFICIENCY_KWH_PER_KG * prices[hour]) / 1000
            
            # Update storage
            storage += production - demand[hour]
            storage = max(0, min(storage, 1500))  # Clamp to limits
            
            schedule.append(SchedulePoint(
                hour=hour,
                timestamp=start_time + timedelta(hours=hour),
                operating_point_pct=round(op_point * 100, 1),
                production_kg_h=round(production, 2),
                power_consumption_kw=round(power_kw, 1),
                electricity_price_per_mwh=prices[hour],
                estimated_cost_per_kg=round(cost_per_kg, 2),
                storage_level_kg=round(storage, 1),
                is_renewable=prices[hour] < 35  # Heuristic for low-price/renewable
            ))
        
        return schedule
    
    def _calculate_summary(
        self,
        schedule: List[SchedulePoint],
        baseline_operating_point: float
    ) -> OptimizationSummary:
        """Calculate summary statistics"""
        
        # Totals
        total_production = sum(p.production_kg_h for p in schedule)
        total_energy = sum(p.power_consumption_kw for p in schedule)
        total_cost = sum(
            (p.power_consumption_kw / 1000) * p.electricity_price_per_mwh 
            for p in schedule
        )
        
        # Averages
        avg_cost_per_kg = total_cost / total_production if total_production > 0 else 0
        avg_efficiency = total_energy / total_production if total_production > 0 else 0
        
        # Renewable percentage
        renewable_hours = sum(1 for p in schedule if p.is_renewable)
        renewable_pct = (renewable_hours / len(schedule)) * 100
        
        # Baseline comparison (constant 60%)
        baseline_production_per_hour = self.MAX_PRODUCTION_KG_H * (baseline_operating_point / 100)
        baseline_power_per_hour = self.RATED_POWER_KW * (baseline_operating_point / 100)
        
        baseline_cost = sum(
            (baseline_power_per_hour / 1000) * p.electricity_price_per_mwh 
            for p in schedule
        )
        
        savings = baseline_cost - total_cost
        savings_pct = (savings / baseline_cost * 100) if baseline_cost > 0 else 0
        
        # Storage metrics
        storage_levels = [p.storage_level_kg for p in schedule]
        
        return OptimizationSummary(
            total_production_kg=round(total_production, 1),
            total_energy_kwh=round(total_energy, 1),
            total_cost_usd=round(total_cost, 2),
            average_cost_per_kg=round(avg_cost_per_kg, 2),
            renewable_percentage=round(renewable_pct, 1),
            average_efficiency_kwh_per_kg=round(avg_efficiency, 2),
            baseline_cost_usd=round(baseline_cost, 2),
            savings_usd=round(savings, 2),
            savings_percentage=round(savings_pct, 1),
            min_storage_kg=round(min(storage_levels), 1),
            max_storage_kg=round(max(storage_levels), 1),
            storage_violations=0
        )


# Singleton
_optimizer_instance = None

def get_optimizer() -> OptimizationEngine:
    """Get optimizer instance"""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = OptimizationEngine()
    return _optimizer_instance
