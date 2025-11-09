/**
 * React hook for electrolyzer status and control
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { electrolyzerApi } from '../api/electrolyzer';
import type { SetpointRequest } from '../api/types';

export function useElectrolyzerStatus(electrolyzerId: string) {
  return useQuery({
    queryKey: ['electrolyzer', electrolyzerId, 'status'],
    queryFn: () => electrolyzerApi.getStatus(electrolyzerId),
    refetchInterval: 5000, // Poll every 5 seconds
  });
}

export function useSetSetpoint(electrolyzerId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: SetpointRequest) =>
      electrolyzerApi.setSetpoint(electrolyzerId, request),
    onSuccess: () => {
      // Invalidate status query to refetch
      queryClient.invalidateQueries({
        queryKey: ['electrolyzer', electrolyzerId, 'status'],
      });
    },
  });
}
