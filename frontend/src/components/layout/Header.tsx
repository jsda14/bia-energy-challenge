import { useState } from "react";
import { NavLink } from "react-router-dom";
import { useAnalysisStore } from "../../stores/useAnalysisStore";
import { ThemeToggle } from "../ui/ThemeToggle";
import { MobileNav } from "../ui/MobileNav";
import biaIcon from "../../assets/img/bia-icon.jpg";
import styles from "./Header.module.css";

const NAV_ITEMS = [
  { label: "Dashboard", to: "/" },
  { label: "Medidores", to: "/meters" },
  { label: "Anomalías", to: "/anomalies" },
];

export default function Header() {
  const isRunning = useAnalysisStore((state) => state.isRunning);
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);

  return (
    <header className={styles.header}>
      <div className={styles.header__container}>
        <div className={styles.header__brand}>
          <img src={biaIcon} alt="Bia Energy" className={styles.header__logo} />
          Bia Energy
        </div>

        <nav className={styles.header__nav}>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `${styles.header__link} ${isActive ? styles["header__link--active"] : ""}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <button
          type="button"
          className={styles.header__menuButton}
          aria-expanded={isMobileNavOpen}
          aria-controls="mobile-nav-panel"
          aria-label={isMobileNavOpen ? "Cerrar menú" : "Abrir menú"}
          onClick={() => setIsMobileNavOpen((open) => !open)}
        >
          <span
            className={`${styles.header__menuIcon} ${isMobileNavOpen ? styles["header__menuIcon--open"] : ""}`}
            aria-hidden="true"
          >
            <span className={styles.header__menuIconMiddle} />
          </span>
        </button>

        <div className={styles.header__actions}>
          <div className={`${styles.header__status} pulse--pulse ${isRunning ? styles["header__status--live"] : ""}`}>
            {isRunning && (
              <span className={styles["header__status-badge"]}>Analizando...</span>
            )}
          </div>
          <ThemeToggle />
        </div>
      </div>

      {isMobileNavOpen && (
        <div id="mobile-nav-panel">
          <MobileNav items={NAV_ITEMS} onClose={() => setIsMobileNavOpen(false)} />
        </div>
      )}
    </header>
  );
}
