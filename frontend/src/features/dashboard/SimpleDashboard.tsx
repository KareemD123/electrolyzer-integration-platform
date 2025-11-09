/**
 * Simple operator dashboard - Real-time electrolyzer monitoring
 */
import { useElectrolyzerStatus } from '../../hooks/useElectrolyzer';

export function SimpleDashboard() {
  const { data: status, isLoading, error } = useElectrolyzerStatus('NH500-ONT-001');

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-screen">
        <div className="text-xl text-gray-600">Loading electrolyzer data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 flex items-center justify-center min-h-screen">
        <div className="text-xl text-red-600">
          Error loading electrolyzer status. Please check if the backend is running.
        </div>
      </div>
    );
  }

  if (!status) {
    return null;
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-6 text-gray-800">Electrolyzer Dashboard</h1>

      {/* Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {/* Production Card */}
        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <p className="text-sm text-gray-600 mb-1">Current Production</p>
          <p className="text-3xl font-bold text-blue-600">
            {status.current_production_kg_h.toFixed(1)}
          </p>
          <p className="text-sm text-gray-500">kg/h</p>
        </div>

        {/* Operating Point Card */}
        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <p className="text-sm text-gray-600 mb-1">Operating Point</p>
          <p className="text-3xl font-bold text-green-600">
            {status.operating_point_pct.toFixed(0)}%
          </p>
          <p className="text-sm text-gray-500">of capacity</p>
        </div>

        {/* Efficiency Card */}
        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <p className="text-sm text-gray-600 mb-1">Efficiency</p>
          <p className="text-3xl font-bold text-purple-600">
            {status.energy_consumption_kwh_per_kg.toFixed(1)}
          </p>
          <p className="text-sm text-gray-500">kWh/kg</p>
        </div>

        {/* Cost Card */}
        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <p className="text-sm text-gray-600 mb-1">Production Cost</p>
          <p className="text-3xl font-bold text-orange-600">
            ${status.estimated_cost_per_kg?.toFixed(2) || '--'}
          </p>
          <p className="text-sm text-gray-500">per kg H₂</p>
        </div>
      </div>

      {/* System Health */}
      <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200 mb-8">
        <h2 className="text-xl font-bold mb-4 text-gray-800">System Health</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-600 mb-1">Status</p>
            <p className={`font-semibold text-lg ${getHealthColor(status.system_health)}`}>
              {status.system_health.toUpperCase().replace('_', ' ')}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Temperature</p>
            <p className="font-semibold text-lg text-gray-800">
              {status.stack_temperature_c.toFixed(1)}°C
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Purity</p>
            <p className="font-semibold text-lg text-gray-800">
              {status.h2_purity_pct.toFixed(3)}%
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Pressure</p>
            <p className="font-semibold text-lg text-gray-800">
              {status.h2_pressure_bar.toFixed(1)} bar
            </p>
          </div>
        </div>
      </div>

      {/* Storage */}
      {status.storage_level_kg && (
        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <h2 className="text-xl font-bold mb-4 text-gray-800">Hydrogen Storage</h2>
          <div className="mb-4">
            <div className="flex justify-between mb-2">
              <span className="text-sm text-gray-600">Storage Level</span>
              <span className="text-sm font-semibold text-gray-800">
                {status.storage_level_kg.toFixed(0)} kg ({status.storage_percentage?.toFixed(0)}%)
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-6 overflow-hidden">
              <div
                className="bg-blue-600 h-6 rounded-full transition-all duration-300 flex items-center justify-end pr-2"
                style={{ width: `${status.storage_percentage}%` }}
              >
                {status.storage_percentage && status.storage_percentage > 10 && (
                  <span className="text-xs text-white font-semibold">
                    {status.storage_percentage.toFixed(0)}%
                  </span>
                )}
              </div>
            </div>
          </div>
          <p className="text-sm text-gray-600">
            Capacity: {status.storage_capacity_kg} kg
          </p>
        </div>
      )}

      {/* Last Updated */}
      <div className="mt-6 text-center text-sm text-gray-500">
        Last updated: {new Date(status.timestamp).toLocaleString()}
      </div>
    </div>
  );
}

function getHealthColor(health: string): string {
  switch (health) {
    case 'optimal':
      return 'text-green-600';
    case 'degraded':
      return 'text-yellow-600';
    case 'maintenance_required':
      return 'text-orange-600';
    case 'fault':
    case 'offline':
      return 'text-red-600';
    default:
      return 'text-gray-600';
  }
}
