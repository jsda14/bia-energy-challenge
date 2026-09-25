import { useQuery } from "@tanstack/react-query";
import { z } from "zod";
import { apiClient } from "../client";
import { meterSummaryResponseSchema } from "../schemas";
import type { MeterSummary } from "../../domain/types";

export function useMeters() {
  return useQuery<MeterSummary[]>({
    queryKey: ["meters"],
    queryFn: async () => {
      const data = await apiClient.get("/meters");
      return z.array(meterSummaryResponseSchema).parse(data);
    },
  });
}
