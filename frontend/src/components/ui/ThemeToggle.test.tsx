import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, beforeEach } from "vitest";
import { ThemeToggle } from "./ThemeToggle";
import { useThemeStore } from "../../stores/useThemeStore";

describe("ThemeToggle", () => {
  beforeEach(() => {
    useThemeStore.setState({ theme: "light" });
  });

  it("renders light mode initially", () => {
    render(<ThemeToggle />);
    const button = screen.getByRole("button", { name: "Cambiar a modo oscuro" });
    expect(button).toBeInTheDocument();
    expect(button.querySelector("svg")).toBeInTheDocument();
  });

  it("toggles theme on click", async () => {
    const user = userEvent.setup();
    render(<ThemeToggle />);

    const button = screen.getByRole("button", { name: "Cambiar a modo oscuro" });
    await user.click(button);

    expect(useThemeStore.getState().theme).toBe("dark");

    const darkButton = screen.getByRole("button", { name: "Cambiar a modo claro" });
    expect(darkButton).toBeInTheDocument();
    expect(darkButton.querySelector("svg")).toBeInTheDocument();
  });
});
