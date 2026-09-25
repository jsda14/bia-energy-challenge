import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { Breadcrumb } from "./Breadcrumb";

describe("Breadcrumb", () => {
  it("renders links and text correctly", () => {
    render(
      <MemoryRouter>
        <Breadcrumb
          items={[
            { label: "Home", to: "/" },
            { label: "Medidores", to: "/meters" },
            { label: "METER-1" },
          ]}
        />
      </MemoryRouter>
    );

    const homeLink = screen.getByRole("link", { name: "Home" });
    expect(homeLink).toBeInTheDocument();
    expect(homeLink).toHaveAttribute("href", "/");

    const metersLink = screen.getByRole("link", { name: "Medidores" });
    expect(metersLink).toBeInTheDocument();
    expect(metersLink).toHaveAttribute("href", "/meters");

    const currentText = screen.getByText("METER-1");
    expect(currentText).toBeInTheDocument();
    expect(currentText.tagName).toBe("SPAN"); // No debe ser enlace
  });
});
