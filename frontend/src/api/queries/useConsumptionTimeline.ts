import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../client";
import { consumptionTimelineResponseSchema } from "../schemas";
import type { ConsumptionTimelineResponse } from "../../domain/types";

export function useConsumptionTimeline() {
  return useQuery<ConsumptionTimelineResponse, Error>({
    queryKey: ["dashboard", "consumption-timeline"],
    queryFn: async () => {
      const data = await apiClient.get("/dashboard/consumption-timeline");
      return consumptionTimelineResponseSchema.parse(data);
    },
    staleTime: 60 * 1000,
  });
}
