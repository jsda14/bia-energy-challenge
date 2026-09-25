import { useEffect } from "react";
import { Outlet } from "react-router-dom";
import Header from "./Header";
import { useThemeStore } from "../../stores/useThemeStore";
import styles from "./AppLayout.module.css";

export default function AppLayout() {
  const theme = useThemeStore((state) => state.theme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  return (
    <div className={styles["app-layout"]}>
      <Header />
      <main className={styles["app-layout__main"]}>
        <Outlet />
      </main>
    </div>
  );
}
