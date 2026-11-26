import ApiStatus from "./ApiStatus.jsx";
import Icon from "./Icons.jsx";

const NAVIGATION_ITEMS = [
  { id: "overview", label: "Overview" },
  { id: "vehicles", label: "Vehicles" },
  { id: "recommendations", label: "Recommendations" },
  { id: "alerts", label: "Risk Alerts" },
];

export default function Sidebar({ activePage, onNavigate }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark">R</span>
        <div>
          <p className="brand-name">RFIE</p>
          <p className="brand-subtitle">Fleet Intelligence</p>
        </div>
      </div>
      <nav className="nav-list" aria-label="Main navigation">
        {NAVIGATION_ITEMS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={item.id === activePage ? "nav-item nav-item-active" : "nav-item"}
            aria-current={item.id === activePage ? "page" : undefined}
            onClick={() => onNavigate(item.id)}
          >
            <Icon name={item.id} />
            <span>{item.label}</span>
          </button>
        ))}
      </nav>
      <div className="sidebar-footer">
        <ApiStatus />
      </div>
    </aside>
  );
}
