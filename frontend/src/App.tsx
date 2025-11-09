import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';
import { SimpleDashboard } from './features/dashboard/SimpleDashboard';
import { OptimizationView } from './features/optimization/OptimizationView';

const queryClient = new QueryClient();

function App() {
  const [view, setView] = useState<'status' | 'optimize'>('status');

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-100">
        <nav className="bg-white shadow-md mb-8">
          <div className="max-w-7xl mx-auto px-8 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-800">
                  Electrolyzer Integration Toolkit
                </h1>
                <p className="text-sm text-gray-600">Next Hydrogen NH-500 Monitoring & Optimization</p>
              </div>
              <div className="flex space-x-4">
                <button
                  onClick={() => setView('status')}
                  className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                    view === 'status'
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  Status
                </button>
                <button
                  onClick={() => setView('optimize')}
                  className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                    view === 'optimize'
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  Optimization
                </button>
              </div>
            </div>
          </div>
        </nav>

        {view === 'status' ? <SimpleDashboard /> : <OptimizationView />}
      </div>
    </QueryClientProvider>
  );
}

export default App;
