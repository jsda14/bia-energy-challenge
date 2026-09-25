import { createBrowserRouter } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout";
import DashboardPage from "./pages/DashboardPage";
import MeterListPage from "./pages/MeterListPage";
import MeterDetailPage from "./pages/MeterDetailPage";
import AnomaliesPage from "./pages/AnomaliesPage";
import AnomalyDetailPage from "./pages/AnomalyDetailPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "meters", element: <MeterListPage /> },
      { path: "meters/:meterId", element: <MeterDetailPage /> },
      { path: "anomalies", element: <AnomaliesPage /> },
      { path: "anomalies/:id", element: <AnomalyDetailPage /> },
    ],
  },
]);
