/**
 * Optimization results visualization
 */
import { useQuery } from '@tanstack/react-query';
import { optimizationApi } from '../../api/optimization';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

export function OptimizationView() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['optimization', 'NH500-ONT-001'],
    queryFn: () => optimizationApi.quickOptimize('NH500-ONT-001'),
  });

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-screen">
        <div className="text-xl text-gray-600">Optimizing schedule...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 flex items-center justify-center min-h-screen">
        <div className="text-xl text-red-600">Optimization failed. Please try again.</div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">24-Hour Optimized Schedule</h1>
        <button
          onClick={() => refetch()}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-md"
        >
          Re-optimize
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <p className="text-sm text-gray-600 mb-1">Total Production</p>
          <p className="text-2xl font-bold text-blue-600">
            {data.summary.total_production_kg.toFixed(0)} kg
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <p className="text-sm text-gray-600 mb-1">Avg Cost</p>
          <p className="text-2xl font-bold text-purple-600">
            ${data.summary.average_cost_per_kg.toFixed(2)}/kg
          </p>
        </div>

        <div className="bg-green-50 p-6 rounded-lg shadow-md border border-green-200">
          <p className="text-sm text-gray-600 mb-1">Savings vs Baseline</p>
          <p className="text-2xl font-bold text-green-600">
            ${Math.abs(data.summary.savings_usd).toFixed(0)}
          </p>
          <p className="text-sm text-gray-500">
            {data.summary.savings_percentage.toFixed(1)}% {data.summary.savings_usd >= 0 ? 'reduction' : 'increase'}
          </p>
        </div>

        <div className="bg-blue-50 p-6 rounded-lg shadow-md border border-blue-200">
          <p className="text-sm text-gray-600 mb-1">Renewable Energy</p>
          <p className="text-2xl font-bold text-blue-600">
            {data.summary.renewable_percentage.toFixed(0)}%
          </p>
        </div>
      </div>

      {/* Schedule Chart */}
      <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200 mb-8">
        <h2 className="text-xl font-bold mb-4 text-gray-800">Production Schedule & Pricing</h2>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={data.schedule}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="hour"
              label={{ value: 'Hour', position: 'insideBottom', offset: -5 }}
            />
            <YAxis
              yAxisId="left"
              label={{ value: 'Operating Point (%)', angle: -90, position: 'insideLeft' }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              label={{ value: 'Price ($/MWh)', angle: 90, position: 'insideRight' }}
            />
            <Tooltip />
            <Legend />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="operating_point_pct"
              stroke="#3b82f6"
              name="Operating Point (%)"
              strokeWidth={2}
            />
            <Line
              yAxisId="right"
              type="stepAfter"
              dataKey="electricity_price_per_mwh"
              stroke="#10b981"
              name="Electricity Price ($/MWh)"
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Cost Breakdown */}
      <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
        <h2 className="text-xl font-bold mb-4 text-gray-800">Cost Analysis</h2>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <p className="text-sm text-gray-600 mb-1">Optimized Cost</p>
            <p className="text-2xl font-bold text-blue-600">
              ${data.summary.total_cost_usd.toFixed(2)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">Baseline Cost (60% constant)</p>
            <p className="text-2xl font-bold text-gray-600">
              ${data.summary.baseline_cost_usd.toFixed(2)}
            </p>
          </div>
        </div>
        <div className={`mt-4 p-4 rounded-lg ${data.summary.savings_usd >= 0 ? 'bg-green-50' : 'bg-red-50'}`}>
          <p className={`text-sm ${data.summary.savings_usd >= 0 ? 'text-green-800' : 'text-red-800'}`}>
            {data.summary.savings_usd >= 0 ? (
              <>
                By optimizing production around electricity prices, you save{' '}
                <strong>${data.summary.savings_usd.toFixed(2)}</strong> per day, or{' '}
                <strong>${(data.summary.savings_usd * 365).toFixed(0)}</strong> per year.
              </>
            ) : (
              <>
                The optimized schedule costs{' '}
                <strong>${Math.abs(data.summary.savings_usd).toFixed(2)}</strong> more per day than baseline.
                This may be due to meeting demand requirements or renewable energy targets.
              </>
            )}
          </p>
        </div>
        <div className="mt-4 text-sm text-gray-600">
          <p>Computation time: {data.computation_time_seconds.toFixed(2)}s</p>
          <p>Solver status: {data.solver_status}</p>
        </div>
      </div>
    </div>
  );
}
