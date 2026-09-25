import { Outlet } from "react-router-dom";
import Header from "./Header";
import styles from "./AppLayout.module.css";

export default function AppLayout() {
  return (
    <div className={styles["app-layout"]}>
      <Header />
      <main className={styles["app-layout__main"]}>
        <Outlet />
      </main>
    </div>
  );
}
