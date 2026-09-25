import { useQuery } from "@tanstack/react-query";
import { z } from "zod";
import { apiClient } from "../client";
import { anomalySummaryResponseSchema } from "../schemas";
import type { AnomalySummary } from "../../domain/types";

export function useAnomalies() {
  return useQuery<AnomalySummary[]>({
    queryKey: ["anomalies"],
    queryFn: async () => {
      const data = await apiClient.get("/anomalies");
      return z.array(anomalySummaryResponseSchema).parse(data);
    },
  });
}
