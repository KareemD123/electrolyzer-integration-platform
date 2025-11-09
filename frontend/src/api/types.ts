/**
 * TypeScript types matching backend schemas
 */

export enum SystemHealth {
  OPTIMAL = 'optimal',
  DEGRADED = 'degraded',
  MAINTENANCE_REQUIRED = 'maintenance_required',
  FAULT = 'fault',
  OFFLINE = 'offline',
}

export interface ElectrolyzerStatus {
  electrolyzer_id: string;
  timestamp: string;
  current_production_kg_h: number;
  operating_point_pct: number;
  cell_voltage_v: number;
  stack_current_a: number;
  energy_consumption_kwh_per_kg: number;
  power_consumption_kw: number;
  system_health: SystemHealth;
  stack_temperature_c: number;
  h2_purity_pct: number;
  h2_pressure_bar: number;
  storage_level_kg?: number;
  storage_capacity_kg?: number;
  storage_percentage?: number;
  available_capacity_pct: number;
  current_electricity_price_per_mwh?: number;
  estimated_cost_per_kg?: number;
}

export interface SetpointRequest {
  target_kg_h: number;
  priority?: 'cost' | 'speed' | 'renewable_matching' | 'reliability';
  ramp_rate_pct_per_sec?: number;
  reason?: string;
}

export interface SetpointResponse {
  status: 'accepted' | 'rejected' | 'queued';
  message: string;
  estimated_time_to_target_seconds?: number;
  projected_ramp?: string;
  current_production_kg_h: number;
  target_production_kg_h: number;
}

export interface SchedulePoint {
  hour: number;
  timestamp: string;
  operating_point_pct: number;
  production_kg_h: number;
  power_consumption_kw: number;
  electricity_price_per_mwh: number;
  estimated_cost_per_kg: number;
  storage_level_kg: number;
  is_renewable: boolean;
}

export interface OptimizationSummary {
  total_production_kg: number;
  total_cost_usd: number;
  average_cost_per_kg: number;
  renewable_percentage: number;
  baseline_cost_usd: number;
  savings_usd: number;
  savings_percentage: number;
}

export interface OptimizationResponse {
  electrolyzer_id: string;
  generated_at: string;
  horizon_hours: number;
  schedule: SchedulePoint[];
  summary: OptimizationSummary;
  objective_used: string;
  computation_time_seconds: number;
  solver_status: string;
}
