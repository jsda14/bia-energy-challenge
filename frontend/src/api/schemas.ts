import { z } from "zod";

export const analysisRunResponseSchema = z.object({
  id: z.string(),
  requested_meter_id: z.string().nullable(),
  status: z.string(),
  started_at: z.string(),
  finished_at: z.string(),
  anomalies_detected_count: z.number(),
  error_message: z.string().nullable(),
});

export const dashboardSummaryResponseSchema = z.object({
  anomalies_detected: z.number(),
  high_priority_count: z.number(),
  average_confidence: z.number().nullable(),
  last_analysis_at: z.string().nullable(),
});

export const meterSummaryResponseSchema = z.object({
  meter_id: z.string(),
  name: z.string(),
  status: z.string(),
  consumption_kwh: z.number(),
  variation_pct: z.number().nullable(),
  anomaly_severity: z.string().nullable(),
});

export const readingResponseSchema = z.object({
  timestamp: z.string(),
  consumption_kwh: z.number(),
  voltage_v: z.number(),
  current_a: z.number(),
  power_factor: z.number(),
  status: z.string(),
});

export const meterDetailResponseSchema = z.object({
  meter_id: z.string(),
  name: z.string(),
  location: z.string(),
  status: z.string(),
  consumption_kwh: z.number(),
  baseline_kwh: z.number().nullable(),
  variation_pct: z.number().nullable(),
  readings: z.array(readingResponseSchema),
});

export const anomalySummaryResponseSchema = z.object({
  id: z.string(),
  meter_id: z.string(),
  type: z.string(),
  severity: z.string(),
  confidence: z.number(),
  recommended_action: z.string(),
  detected_at: z.string(),
});

export const anomalyDetailResponseSchema = z.object({
  id: z.string(),
  meter_id: z.string(),
  type: z.string(),
  severity: z.string(),
  confidence: z.number(),
  reason: z.string(),
  recommended_action: z.string(),
  baseline_kwh: z.number(),
  observed_kwh: z.number(),
  variation_pct: z.number(),
  affected_variables: z.array(z.string()),
  correlated_event: z.string().nullable(),
  window_start: z.string(),
  window_end: z.string(),
  explanation_source: z.string(),
});
