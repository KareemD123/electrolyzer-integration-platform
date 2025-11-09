/**
 * Optimization API methods
 */
import { apiClient } from './client';
import type { OptimizationResponse } from './types';

const API_PREFIX = '/api/v1';

export const optimizationApi = {
  /**
   * Quick optimize using default Ontario prices
   */
  quickOptimize: async (electrolyzerId: string): Promise<OptimizationResponse> => {
    const response = await apiClient.get<OptimizationResponse>(
      `${API_PREFIX}/optimize/quick-optimize/${electrolyzerId}`
    );
    return response.data;
  },
};
