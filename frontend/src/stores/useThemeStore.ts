import { create } from "zustand";

type Theme = "light" | "dark";

interface ThemeState {
  theme: Theme;
  toggleTheme: () => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
  theme: (typeof localStorage !== "undefined" &&
    (localStorage.getItem("bia-energy-theme") as Theme | null)) || "light",
  toggleTheme: () =>
    set((state) => {
      const next: Theme = state.theme === "light" ? "dark" : "light";
      try {
        localStorage.setItem("bia-energy-theme", next);
      } catch {
        // localStorage puede no estar disponible
      }
      return { theme: next };
    }),
}));
