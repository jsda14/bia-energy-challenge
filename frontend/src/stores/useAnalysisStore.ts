import { create } from "zustand";

interface AnalysisState {
  isRunning: boolean;
  lastRunId: string | null;
  startRun: () => void;
  finishRun: (runId: string | null) => void;
}

export const useAnalysisStore = create<AnalysisState>((set) => ({
  isRunning: false,
  lastRunId: null,
  startRun: () => set({ isRunning: true }),
  finishRun: (runId: string | null) => set({ isRunning: false, lastRunId: runId }),
}));
