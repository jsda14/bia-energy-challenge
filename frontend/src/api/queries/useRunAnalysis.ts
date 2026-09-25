import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../client";
import { analysisRunResponseSchema } from "../schemas";
import { useAnalysisStore } from "../../stores/useAnalysisStore";

export function useRunAnalysis() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (meterId: string | null) => {
      const data = await apiClient.post("/ai/analyze", { meter_id: meterId });
      return analysisRunResponseSchema.parse(data);
    },
    onMutate: () => {
      useAnalysisStore.getState().startRun();
    },
    onSettled: (result) => {
      if (result) {
        useAnalysisStore.getState().finishRun(result.id);
      } else {
        useAnalysisStore.getState().finishRun(null);
      }
      queryClient.invalidateQueries({ queryKey: ["dashboard-summary"] });
      queryClient.invalidateQueries({ queryKey: ["meters"] });
      queryClient.invalidateQueries({ queryKey: ["anomalies"] });
    },
  });
}
