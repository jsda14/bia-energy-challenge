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
        selectedMeterId={null}
        selectedType={null}
        selectedSeverity={null}
        onMeterIdChange={onMeterIdChange}
        onTypeChange={() => {}}
        onSeverityChange={() => {}}
      />
    );

    const select = screen.getByLabelText("Medidor:");
    expect(select).toBeInTheDocument();

    const user = userEvent.setup();
    await user.selectOptions(select, "METER-1");
    expect(onMeterIdChange).toHaveBeenCalledWith("METER-1");
  });
});
