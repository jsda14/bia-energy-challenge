import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../client";
import { meterDetailResponseSchema } from "../schemas";
import type { MeterDetail } from "../../domain/types";

export function useMeterDetail(meterId: string) {
  return useQuery<MeterDetail>({
    queryKey: ["meters", meterId],
    queryFn: async () => {
      const data = await apiClient.get(`/meters/${meterId}`);
      return meterDetailResponseSchema.parse(data);
    },
    enabled: !!meterId,
  });
}
