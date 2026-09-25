import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../client";
import { anomalyDetailResponseSchema } from "../schemas";

export function useRegenerateExplanation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (anomalyId: string) => {
      const data = await apiClient.post(`/anomalies/${anomalyId}/regenerate-explanation`);
      return anomalyDetailResponseSchema.parse(data);
    },
    onSuccess: (result) => {
      queryClient.setQueryData(["anomalies", result.id], result);
    },
  });
}
