import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { AnomaliesFilterBar } from "./AnomaliesFilterBar";

describe("AnomaliesFilterBar", () => {
  it("renders selects and triggers changes", async () => {
    const onMeterIdChange = vi.fn();
    render(
      <AnomaliesFilterBar
        meterIdOptions={["METER-1"]}
        typeOptions={["VOLTAGE_DROP"]}
        severityOptions={["Alta"]}
        triageStatusOptions={["NEW"]}
        selectedMeterId={null}
        selectedType={null}
        selectedSeverity={null}
        selectedTriageStatus={null}
        onMeterIdChange={onMeterIdChange}
        onTypeChange={() => {}}
        onSeverityChange={() => {}}
        onTriageStatusChange={() => {}}
      />
    );

    const select = screen.getByLabelText("Medidor:");
    expect(select).toBeInTheDocument();

    const user = userEvent.setup();
    await user.selectOptions(select, "METER-1");
    expect(onMeterIdChange).toHaveBeenCalledWith("METER-1");
  });

  it("triggers onTriageStatusChange and defaults to 'Todas'", async () => {
    const onTriageStatusChange = vi.fn();
    render(
      <AnomaliesFilterBar
        meterIdOptions={["METER-1"]}
        typeOptions={["VOLTAGE_DROP"]}
        severityOptions={["HIGH"]}
        triageStatusOptions={["NEW", "ACKNOWLEDGED", "DISMISSED"]}
        selectedMeterId={null}
        selectedType={null}
        selectedSeverity={null}
        selectedTriageStatus={null}
        onMeterIdChange={() => {}}
        onTypeChange={() => {}}
        onSeverityChange={() => {}}
        onTriageStatusChange={onTriageStatusChange}
      />
    );

    const select = screen.getByLabelText("Estado de Triage:");
    // "Todas" es el default — no oculta DISMISSED por defecto.
    expect((select as HTMLSelectElement).value).toBe("");

    const user = userEvent.setup();
    await user.selectOptions(select, "DISMISSED");
    expect(onTriageStatusChange).toHaveBeenCalledWith("DISMISSED");
  });
});
