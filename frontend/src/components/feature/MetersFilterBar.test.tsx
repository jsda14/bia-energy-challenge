import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { MetersFilterBar } from "./MetersFilterBar";

describe("MetersFilterBar", () => {
  it("renders search input and triggers onSearchChange", async () => {
    const onSearchChange = vi.fn();
    render(
      <MetersFilterBar
        statusOptions={["Activo"]}
        severityOptions={["Alta"]}
        selectedStatus={null}
        selectedSeverity={null}
        searchQuery=""
        onStatusChange={() => {}}
        onSeverityChange={() => {}}
        onSearchChange={onSearchChange}
      />
    );

    const searchInput = screen.getByPlaceholderText("Buscar por ID o nombre...");
    expect(searchInput).toBeInTheDocument();

    const user = userEvent.setup();
    await user.type(searchInput, "1");
    expect(onSearchChange).toHaveBeenCalledWith("1");
  });
});
