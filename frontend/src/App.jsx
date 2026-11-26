import { useState } from "react";
import Sidebar from "./components/Sidebar.jsx";
import VehicleDetailPanel from "./components/VehicleDetailPanel.jsx";
import AlertsPage from "./pages/AlertsPage.jsx";
import OverviewPage from "./pages/OverviewPage.jsx";
import RecommendationsPage from "./pages/RecommendationsPage.jsx";
import VehiclesPage from "./pages/VehiclesPage.jsx";

const PAGES = {
  overview: OverviewPage,
  vehicles: VehiclesPage,
  recommendations: RecommendationsPage,
  alerts: AlertsPage,
};

export default function App() {
  const [activePage, setActivePage] = useState("overview");
  const [selectedVehicleId, setSelectedVehicleId] = useState(null);
  const ActivePage = PAGES[activePage];

  return (
    <div className="app-shell">
      <Sidebar activePage={activePage} onNavigate={setActivePage} />
      <main className="main-content">
        <ActivePage onSelectVehicle={setSelectedVehicleId} onNavigate={setActivePage} />
      </main>
      {selectedVehicleId && (
        <VehicleDetailPanel
          vehicleId={selectedVehicleId}
          onClose={() => setSelectedVehicleId(null)}
        />
      )}
    </div>
  );
}
