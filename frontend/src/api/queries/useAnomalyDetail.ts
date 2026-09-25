import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../client";
import { anomalyDetailResponseSchema } from "../schemas";
import type { AnomalyDetail } from "../../domain/types";

export function useAnomalyDetail(anomalyId: string) {
  return useQuery<AnomalyDetail>({
    queryKey: ["anomalies", anomalyId],
    queryFn: async () => {
      const data = await apiClient.get(`/anomalies/${anomalyId}`);
      return anomalyDetailResponseSchema.parse(data);
    },
    enabled: !!anomalyId,
  });
}
