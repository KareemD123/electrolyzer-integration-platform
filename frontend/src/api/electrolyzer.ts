/**
 * Electrolyzer API methods
 */
import { apiClient } from './client';
import type { ElectrolyzerStatus, SetpointRequest, SetpointResponse } from './types';

const API_PREFIX = '/api/v1';

export const electrolyzerApi = {
  /**
   * Get current electrolyzer status
   */
  getStatus: async (electrolyzerId: string): Promise<ElectrolyzerStatus> => {
    const response = await apiClient.get<ElectrolyzerStatus>(
      `${API_PREFIX}/electrolyzer/${electrolyzerId}/status`
    );
    return response.data;
  },

  /**
   * Set production setpoint
   */
  setSetpoint: async (
    electrolyzerId: string,
    request: SetpointRequest
  ): Promise<SetpointResponse> => {
    const response = await apiClient.post<SetpointResponse>(
      `${API_PREFIX}/electrolyzer/${electrolyzerId}/setpoint`,
      request
    );
    return response.data;
  },

  /**
   * List all electrolyzers
   */
  listElectrolyzers: async () => {
    const response = await apiClient.get(`${API_PREFIX}/electrolyzer/list`);
    return response.data;
  },
};
