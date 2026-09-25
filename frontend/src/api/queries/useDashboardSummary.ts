import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../client";
import { dashboardSummaryResponseSchema } from "../schemas";
import type { DashboardSummary } from "../../domain/types";

export function useDashboardSummary() {
  return useQuery<DashboardSummary>({
    queryKey: ["dashboard-summary"],
    queryFn: async () => {
      const data = await apiClient.get("/dashboard/summary");
      return dashboardSummaryResponseSchema.parse(data);
    },
  });
}
