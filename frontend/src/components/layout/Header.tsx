import { NavLink } from "react-router-dom";
import { useAnalysisStore } from "../../stores/useAnalysisStore";
import { ThemeToggle } from "../ui/ThemeToggle";
import styles from "./Header.module.css";

export default function Header() {
  const isRunning = useAnalysisStore((state) => state.isRunning);

  return (
    <header className={styles.header}>
      <div className={styles.header__container}>
        <div className={styles.header__brand}>Bia Energy</div>
        
        <nav className={styles.header__nav}>
          <NavLink 
            to="/" 
            className={({ isActive }) => 
              `${styles.header__link} ${isActive ? styles["header__link--active"] : ""}`
            }
          >
            Dashboard
          </NavLink>
          <NavLink 
            to="/meters" 
            className={({ isActive }) => 
              `${styles.header__link} ${isActive ? styles["header__link--active"] : ""}`
            }
          >
            Medidores
          </NavLink>
          <NavLink 
            to="/anomalies" 
            className={({ isActive }) => 
              `${styles.header__link} ${isActive ? styles["header__link--active"] : ""}`
            }
          >
            Anomalías
          </NavLink>
        </nav>

        <div className={styles.header__actions}>
          <div className={styles.header__status}>
            {isRunning && (
              <span className={styles["header__status-badge"]}>Analizando...</span>
            )}
          </div>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
