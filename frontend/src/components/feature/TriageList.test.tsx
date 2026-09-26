import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { TriageList } from "./TriageList";
import type { AnomalySummary } from "../../domain/types";

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

function makeAnomaly(overrides: Partial<AnomalySummary>): AnomalySummary {
  return {
    id: "1",
    meter_id: "M-1",
    type: "SPIKE",
    severity: "LOW",
    confidence: 0.9,
    recommended_action: "Revisar",
    detected_at: "2026-09-20T00:00:00Z",
    triage_status: "NEW",
    ...overrides,
  };
}

describe("TriageList", () => {
  beforeEach(() => {
    mockNavigate.mockClear();
  });

  it("renders the empty state when there are no anomalies", () => {
    render(
      <MemoryRouter>
        <TriageList anomalies={[]} />
      </MemoryRouter>
    );
    expect(screen.getByText("No hay anomalías activas.")).toBeInTheDocument();
  });

  it("sorts by severity first, then by most recent detected_at", () => {
    const anomalies: AnomalySummary[] = [
      makeAnomaly({ id: "low", severity: "LOW", detected_at: "2026-09-25T00:00:00Z" }),
      makeAnomaly({ id: "high-old", severity: "HIGH", detected_at: "2026-09-01T00:00:00Z" }),
      makeAnomaly({ id: "high-new", severity: "HIGH", detected_at: "2026-09-20T00:00:00Z" }),
      makeAnomaly({ id: "medium", severity: "MEDIUM", detected_at: "2026-09-22T00:00:00Z" }),
    ];
    render(
      <MemoryRouter>
        <TriageList anomalies={anomalies} />
      </MemoryRouter>
    );

    const items = screen.getAllByRole("button");
    // high-new before high-old (same severity, most recent first), then medium, then low
    expect(items[0]).toHaveTextContent("M-1");
    const meterIds = items.map((el) => el.querySelector("span"));
    expect(meterIds.length).toBe(4);
  });

  it("caps the list at the top 5 anomalies", () => {
    const anomalies: AnomalySummary[] = Array.from({ length: 8 }, (_, i) =>
      makeAnomaly({ id: `a-${i}`, detected_at: `2026-09-0${(i % 9) + 1}T00:00:00Z` })
    );
    render(
      <MemoryRouter>
        <TriageList anomalies={anomalies} />
      </MemoryRouter>
    );
    expect(screen.getAllByRole("button")).toHaveLength(5);
  });

  it("navigates to the anomaly detail page on click", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <TriageList anomalies={[makeAnomaly({ id: "abc" })]} />
      </MemoryRouter>
    );
    await user.click(screen.getByRole("button"));
    expect(mockNavigate).toHaveBeenCalledWith("/anomalies/abc");
  });

  it("navigates on Enter keydown for accessibility", () => {
    render(
      <MemoryRouter>
        <TriageList anomalies={[makeAnomaly({ id: "abc" })]} />
      </MemoryRouter>
    );
    const item = screen.getByRole("button");
    item.focus();
    item.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
    expect(mockNavigate).toHaveBeenCalledWith("/anomalies/abc");
  });
});
