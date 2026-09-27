import { useEffect } from "react";
import { NavLink } from "react-router-dom";
import styles from "./MobileNav.module.css";

interface MobileNavProps {
  items: { label: string; to: string }[];
  onClose: () => void;
}

export function MobileNav({ items, onClose }: MobileNavProps) {
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <nav className={styles["mobile-nav__panel"]} aria-label="Navegación móvil">
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          onClick={onClose}
          className={({ isActive }) =>
            `${styles["mobile-nav__link"]} ${isActive ? styles["mobile-nav__link--active"] : ""}`
          }
        >
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}
