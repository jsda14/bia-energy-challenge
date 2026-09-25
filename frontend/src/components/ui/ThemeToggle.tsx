import { useThemeStore } from "../../stores/useThemeStore";
import styles from "./ThemeToggle.module.css";

export function ThemeToggle(): JSX.Element {
  const { theme, toggleTheme } = useThemeStore();
  
  return (
    <button 
      type="button" 
      onClick={toggleTheme} 
      className={styles.toggle}
      aria-label={`Cambiar a modo ${theme === "light" ? "oscuro" : "claro"}`}
    >
      {theme === "light" ? "🌙" : "☀️"}
    </button>
  );
}
