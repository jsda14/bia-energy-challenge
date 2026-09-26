import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../client";
import { anomalyDetailResponseSchema } from "../schemas";

interface UpdateTriageStatusInput {
  anomalyId: string;
  status: "NEW" | "ACKNOWLEDGED" | "DISMISSED";
}

export function useUpdateTriageStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ anomalyId, status }: UpdateTriageStatusInput) => {
      const data = await apiClient.patch(`/anomalies/${anomalyId}/triage-status`, { status });
      return anomalyDetailResponseSchema.parse(data);
    },
    onSuccess: (result) => {
      queryClient.setQueryData(["anomalies", result.id], result);
      queryClient.invalidateQueries({ queryKey: ["anomalies"] });
    },
  });
}
