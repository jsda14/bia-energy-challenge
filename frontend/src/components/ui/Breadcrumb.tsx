import { Link } from "react-router-dom";
import styles from "./Breadcrumb.module.css";

interface BreadcrumbProps {
  items: Array<{ label: string; to?: string }>;
}

export function Breadcrumb({ items }: BreadcrumbProps) {
  return (
    <nav className={styles.breadcrumb} aria-label="Breadcrumb">
      {items.map((item, index) => {
        const isLast = index === items.length - 1;
        return (
          <span key={index} className={styles.itemWrapper}>
            {item.to ? (
              <Link to={item.to} className={styles.link}>
                {item.label}
              </Link>
            ) : (
              <span className={styles.current} aria-current={isLast ? "page" : undefined}>
                {item.label}
              </span>
            )}
            {!isLast && <span className={styles.separator}>/</span>}
          </span>
        );
      })}
    </nav>
  );
}
