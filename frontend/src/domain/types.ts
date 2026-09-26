import { z } from "zod";
import {
  analysisRunResponseSchema,
  dashboardSummaryResponseSchema,
  meterSummaryResponseSchema,
  readingResponseSchema,
  meterDetailResponseSchema,
  anomalySummaryResponseSchema,
  anomalyDetailResponseSchema,
  consumptionTimelinePointSchema,
  consumptionTimelineResponseSchema,
  eventResponseSchema,
} from "../api/schemas";

export type AnalysisRun = z.infer<typeof analysisRunResponseSchema>;
export type DashboardSummary = z.infer<typeof dashboardSummaryResponseSchema>;
export type MeterSummary = z.infer<typeof meterSummaryResponseSchema>;
export type Reading = z.infer<typeof readingResponseSchema>;
export type MeterDetail = z.infer<typeof meterDetailResponseSchema>;
export type AnomalySummary = z.infer<typeof anomalySummaryResponseSchema>;
export type AnomalyDetail = z.infer<typeof anomalyDetailResponseSchema>;
export type ConsumptionTimelinePoint = z.infer<typeof consumptionTimelinePointSchema>;
export type ConsumptionTimelineResponse = z.infer<typeof consumptionTimelineResponseSchema>;
export type Event = z.infer<typeof eventResponseSchema>;
