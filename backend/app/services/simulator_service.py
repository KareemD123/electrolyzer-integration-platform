"""
Mock electrolyzer simulator

Simulates a Next Hydrogen NH-500 electrolyzer with realistic behavior.
In production, this would be replaced with actual PLC communication.
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional
import random

from app.schemas.electrolyzer import ElectrolyzerStatus, SystemHealth
from app.config import settings


class ElectrolyzerSimulator:
    """
    Simulates NH-500 electrolyzer behavior
    
    This class maintains state and simulates realistic electrolyzer responses
    including ramp rates, efficiency curves, and minor variations.
    """
    
    def __init__(self, electrolyzer_id: str):
        self.electrolyzer_id = electrolyzer_id
        self._load_config()
        
        # Current state
        self.current_operating_point = 60.0  # Start at 60%
        self.target_operating_point = 60.0
        self.last_update = datetime.utcnow()
        
        # Storage simulation
        self.storage_level_kg = self.config["storage"]["current_level_kg"]
        
    def _load_config(self):
        """Load electrolyzer configuration from JSON"""
        config_path = Path(settings.DATA_DIR) / "electrolyzer_config.json"
        with open(config_path) as f:
            all_configs = json.load(f)
            self.config = all_configs.get(self.electrolyzer_id)
            if not self.config:
                raise ValueError(f"No config found for {self.electrolyzer_id}")
    
    def set_target(self, target_kg_h: float) -> Dict:
        """
        Set new production target
        
        Args:
            target_kg_h: Desired production rate (kg/h)
            
        Returns:
            Dict with ramp information
        """
        max_production = self.config["max_production_kg_h"]
        target_pct = (target_kg_h / max_production) * 100
        
        # Validate turndown range
        if not (5.0 <= target_pct <= 100.0):
            return {
                "status": "rejected",
                "reason": f"Target {target_pct:.1f}% outside turndown range (5-100%)"
            }
        
        self.target_operating_point = target_pct
        
        # Calculate ramp time
        delta_pct = abs(self.target_operating_point - self.current_operating_point)
        max_ramp = self.config["max_ramp_rate_pct_per_sec"]
        ramp_time_seconds = delta_pct / max_ramp
        
        return {
            "status": "accepted",
            "current_pct": self.current_operating_point,
            "target_pct": self.target_operating_point,
            "ramp_time_seconds": ramp_time_seconds
        }
    
    def update_state(self):
        """
        Update simulator state based on elapsed time
        
        Simulates ramping behavior and storage changes
        """
        now = datetime.utcnow()
        elapsed_seconds = (now - self.last_update).total_seconds()
        self.last_update = now
        
        # Ramp toward target
        if self.current_operating_point != self.target_operating_point:
            max_ramp = self.config["max_ramp_rate_pct_per_sec"]
            max_change = max_ramp * elapsed_seconds
            
            delta = self.target_operating_point - self.current_operating_point
            if abs(delta) <= max_change:
                self.current_operating_point = self.target_operating_point
            else:
                direction = 1 if delta > 0 else -1
                self.current_operating_point += direction * max_change
        
        # Update storage (simplified)
        production_kg_h = (self.current_operating_point / 100) * self.config["max_production_kg_h"]
        demand_kg_h = self._get_current_demand()
        
        net_change_kg_h = production_kg_h - demand_kg_h
        net_change_kg = (net_change_kg_h * elapsed_seconds) / 3600
        
        self.storage_level_kg += net_change_kg
        
        # Clamp storage to limits
        max_storage = self.config["storage"]["capacity_kg"]
        self.storage_level_kg = max(0, min(self.storage_level_kg, max_storage))
    
    def _get_current_demand(self) -> float:
        """Get current H2 demand based on time of day"""
        # Load demand pattern
        demand_path = Path(settings.DATA_DIR) / "forklift_demand_pattern.json"
        with open(demand_path) as f:
            pattern = json.load(f)
        
        hour = datetime.utcnow().hour
        demand_kg_h = pattern["weekday_pattern"][hour]["demand_kg_h"]
        
        # Add small random variation (±5%)
        variation = random.uniform(0.95, 1.05)
        return demand_kg_h * variation
    
    def get_status(self) -> ElectrolyzerStatus:
        """
        Get current electrolyzer status
        
        Returns:
            ElectrolyzerStatus with all current metrics
        """
        self.update_state()
        
        # Calculate production
        operating_point_pct = self.current_operating_point
        max_production = self.config["max_production_kg_h"]
        current_production = (operating_point_pct / 100) * max_production
        
        # Calculate power consumption
        # Uses linear approximation: power scales with production
        rated_power = self.config["rated_power_kw"]
        power_consumption = (operating_point_pct / 100) * rated_power
        
        # Calculate efficiency
        # NH-X efficiency slightly degrades at lower operating points
        if operating_point_pct < 20:
            efficiency_multiplier = 1.10  # 10% worse efficiency
        elif operating_point_pct < 40:
            efficiency_multiplier = 1.05  # 5% worse
        else:
            efficiency_multiplier = 1.0
        
        base_efficiency = self.config["stack_energy_kwh_per_kg"]
        energy_consumption = base_efficiency * efficiency_multiplier
        
        # Cell voltage (increases slightly at higher current)
        base_voltage = 1.90
        voltage_increase = (operating_point_pct / 100) * 0.05
        cell_voltage = base_voltage + voltage_increase + random.uniform(-0.01, 0.01)
        
        # Stack current (scales with operating point)
        max_current = 1000  # Amps at 100%
        stack_current = (operating_point_pct / 100) * max_current
        
        # Temperature (increases with load)
        base_temp = 60.0
        temp_rise = (operating_point_pct / 100) * 15.0
        stack_temperature = base_temp + temp_rise + random.uniform(-2, 2)
        
        # Purity (very stable for NH-X)
        h2_purity = 99.998 + random.uniform(-0.002, 0.001)
        
        # System health
        if self.storage_level_kg < self.config["storage"]["min_safe_level_kg"]:
            health = SystemHealth.DEGRADED
        elif stack_temperature > 85:
            health = SystemHealth.MAINTENANCE_REQUIRED
        else:
            health = SystemHealth.OPTIMAL
        
        # Available capacity
        available_capacity = 100 - operating_point_pct
        
        # Storage percentage
        storage_pct = (self.storage_level_kg / self.config["storage"]["capacity_kg"]) * 100
        
        # Cost estimation (simplified)
        electricity_price = self._get_current_electricity_price()
        cost_per_kg = (energy_consumption * electricity_price) / 1000  # Convert MWh to kWh
        
        return ElectrolyzerStatus(
            electrolyzer_id=self.electrolyzer_id,
            timestamp=datetime.utcnow(),
            current_production_kg_h=round(current_production, 2),
            operating_point_pct=round(operating_point_pct, 1),
            cell_voltage_v=round(cell_voltage, 3),
            stack_current_a=round(stack_current, 1),
            energy_consumption_kwh_per_kg=round(energy_consumption, 2),
            power_consumption_kw=round(power_consumption, 1),
            system_health=health,
            stack_temperature_c=round(stack_temperature, 1),
            h2_purity_pct=round(h2_purity, 3),
            h2_pressure_bar=15.0,
            storage_level_kg=round(self.storage_level_kg, 1),
            storage_capacity_kg=self.config["storage"]["capacity_kg"],
            storage_percentage=round(storage_pct, 1),
            available_capacity_pct=round(available_capacity, 1),
            current_electricity_price_per_mwh=electricity_price,
            estimated_cost_per_kg=round(cost_per_kg, 2)
        )
    
    def _get_current_electricity_price(self) -> float:
        """Get current Ontario electricity price based on TOU"""
        price_path = Path(settings.DATA_DIR) / "ontario_prices.json"
        with open(price_path) as f:
            prices = json.load(f)
        
        hour = datetime.utcnow().hour
        day_of_week = datetime.utcnow().weekday()
        
        # Weekend: all off-peak
        if day_of_week >= 5:
            return prices["prices"]["off_peak"]["price_per_mwh"]
        
        # Weekday: use TOU schedule
        sample_day = prices["sample_day"]
        return sample_day[hour]["price_per_mwh"]


# Singleton instance
_simulator_instance: Optional[ElectrolyzerSimulator] = None

def get_simulator() -> ElectrolyzerSimulator:
    """Get or create simulator instance"""
    global _simulator_instance
    if _simulator_instance is None:
        _simulator_instance = ElectrolyzerSimulator("NH500-ONT-001")
    return _simulator_instance
