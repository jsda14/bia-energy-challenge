import { describe, it, expect, beforeEach, vi } from "vitest";
import { useThemeStore } from "./useThemeStore";

describe("useThemeStore", () => {
  beforeEach(() => {
    // Limpiar localStorage
    localStorage.clear();
    useThemeStore.setState({ theme: "light" });
  });

  it("should initialize with light theme by default", () => {
    const { theme } = useThemeStore.getState();
    expect(theme).toBe("light");
  });

  it("should toggle theme to dark", () => {
    useThemeStore.getState().toggleTheme();
    expect(useThemeStore.getState().theme).toBe("dark");
    expect(localStorage.getItem("bia-energy-theme")).toBe("dark");
  });

  it("should toggle theme back to light", () => {
    useThemeStore.getState().toggleTheme();
    useThemeStore.getState().toggleTheme();
    expect(useThemeStore.getState().theme).toBe("light");
    expect(localStorage.getItem("bia-energy-theme")).toBe("light");
  });

  it("should handle localStorage being unavailable gracefully", () => {
    const setItemSpy = vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("Quota exceeded");
    });

    useThemeStore.getState().toggleTheme();
    expect(useThemeStore.getState().theme).toBe("dark");

    setItemSpy.mockRestore();
  });
});
