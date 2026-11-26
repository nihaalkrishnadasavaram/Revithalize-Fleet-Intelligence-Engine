import { useState } from "react";
import DistributionBar from "../components/DistributionBar.jsx";
import KpiCard from "../components/KpiCard.jsx";
import PageHeader from "../components/PageHeader.jsx";
import Badge from "../components/Badge.jsx";
import { EmptyState, ErrorState, LoadingState } from "../components/StateMessages.jsx";
import VehicleTable from "../components/VehicleTable.jsx";
import { useApi } from "../hooks/useApi.js";
import { generateData, getSummary } from "../services/api.js";
import {
  formatCompactCurrency,
  formatCurrency,
  formatNumber,
  formatPercent,
  formatPercentValue,
  formatScore,
} from "../utils/format.js";
import { priorityTone } from "../utils/tones.js";

function GenerateDataPrompt({ onGenerated }) {
  const [generating, setGenerating] = useState(false);
  const [message, setMessage] = useState(null);

  const handleGenerate = async () => {
    setGenerating(true);
    setMessage(null);
    try {
      await generateData();
      onGenerated();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <EmptyState
      title="No fleet data yet"
      message="The database is empty. Generate the synthetic fleet dataset to populate the dashboard."
    >
      <button
        type="button"
        className="button button-primary"
        disabled={generating}
        onClick={handleGenerate}
      >
        {generating ? "Generating…" : "Generate synthetic data"}
      </button>
      {message && <p className="form-error">{message}</p>}
    </EmptyState>
  );
}

function SummaryList({ title, note, actionLabel, onAction, isEmpty, emptyMessage, children }) {
  return (
    <article className="card">
      <div className="card-header">
        <h2 className="card-title">{title}</h2>
        <button type="button" className="link-button" onClick={onAction}>
          {actionLabel}
        </button>
      </div>
      {note && <p className="summary-note">{note}</p>}
      {isEmpty ? <p className="muted">{emptyMessage}</p> : <ul className="summary-list">{children}</ul>}
    </article>
  );
}

export default function OverviewPage({ onSelectVehicle, onNavigate }) {
  const { data: summary, loading, error, reload } = useApi(getSummary);

  if (loading && !summary) {
    return (
      <>
        <PageHeader title="Fleet Overview" subtitle="Key indicators across the whole fleet" />
        <LoadingState message="Loading fleet summary…" />
      </>
    );
  }
  if (error) {
    return (
      <>
        <PageHeader title="Fleet Overview" subtitle="Key indicators across the whole fleet" />
        <ErrorState message={error} onRetry={reload} />
      </>
    );
  }
  if (summary.total_vehicles === 0) {
    return (
      <>
        <PageHeader title="Fleet Overview" subtitle="Key indicators across the whole fleet" />
        <GenerateDataPrompt onGenerated={reload} />
      </>
    );
  }

  const {
    health_distribution: health,
    risk_distribution: risk,
    type_distribution: types,
  } = summary;
  const averageMaintenance = summary.total_maintenance_cost_inr / summary.total_vehicles;

  return (
    <>
      <PageHeader title="Fleet Overview" subtitle="Key indicators across the whole fleet" />

      <section className="kpi-grid">
        <KpiCard
          label="Total Vehicles"
          value={formatNumber(summary.total_vehicles)}
          hint={`${formatNumber(types.Scooter)} scooters · ${formatNumber(types.Motorcycle)} motorcycles`}
        />
        <KpiCard
          label="Avg. Vehicle Health"
          value={formatScore(summary.average_health_score)}
          hint={`Avg. battery health ${formatPercentValue(summary.average_battery_health_pct)}`}
          tone="green"
        />
        <KpiCard
          label="Fleet Efficiency"
          value={formatScore(summary.fleet_efficiency_score)}
          hint="Score out of 100"
          tone="green"
        />
        <KpiCard
          label="High-Risk Vehicles"
          value={formatNumber(summary.high_risk_vehicles)}
          hint={`${formatPercent(summary.high_risk_vehicles, summary.total_vehicles)} of the fleet`}
          tone="red"
        />
        <KpiCard
          label="Total Maintenance Cost"
          value={formatCompactCurrency(summary.total_maintenance_cost_inr)}
          hint={`${formatCurrency(averageMaintenance)} per vehicle`}
        />
      </section>

      <section className="two-column">
        <DistributionBar
          title="Vehicle health status"
          segments={[
            { label: "Good", value: health.Good, tone: "success" },
            { label: "Needs Attention", value: health["Needs Attention"], tone: "warning" },
            { label: "Critical", value: health.Critical, tone: "danger" },
          ]}
        />
        <DistributionBar
          title="Operational risk status"
          segments={[
            { label: "Low", value: risk.Low, tone: "success" },
            { label: "Medium", value: risk.Medium, tone: "warning" },
            { label: "High", value: risk.High, tone: "danger" },
          ]}
        />
      </section>

      <section className="card">
        <div className="card-header">
          <h2 className="card-title">Recent vehicle records</h2>
          <button type="button" className="link-button" onClick={() => onNavigate("vehicles")}>
            View all vehicles
          </button>
        </div>
        <VehicleTable vehicles={summary.recent_vehicles} onSelectVehicle={onSelectVehicle} compact />
      </section>

      <section className="two-column">
        <SummaryList
          title="Recent recommendations"
          note={
            summary.estimated_annual_savings_inr > 0
              ? `Potential saving ${formatCompactCurrency(summary.estimated_annual_savings_inr)} per year`
              : null
          }
          actionLabel="View all"
          onAction={() => onNavigate("recommendations")}
          isEmpty={summary.recent_recommendations.length === 0}
          emptyMessage="No recommendations have been generated."
        >
          {summary.recent_recommendations.map((item) => (
            <li key={item.id}>
              <div className="summary-item-top">
                <Badge tone={priorityTone(item.priority)}>{item.priority}</Badge>
                <button type="button" className="link-button" onClick={() => onSelectVehicle(item.vehicle_id)}>
                  {item.vehicle_id}
                </button>
              </div>
              <p className="summary-item-title">{item.title}</p>
              <p className="muted">{item.category}</p>
            </li>
          ))}
        </SummaryList>

        <SummaryList
          title="Important alerts"
          actionLabel="View all"
          onAction={() => onNavigate("alerts")}
          isEmpty={summary.important_alerts.length === 0}
          emptyMessage="No high-risk vehicles right now."
        >
          {summary.important_alerts.map((alert) => (
            <li key={alert.id}>
              <div className="summary-item-top">
                <Badge tone="danger">Risk {formatScore(alert.risk_score)}</Badge>
                <button type="button" className="link-button" onClick={() => onSelectVehicle(alert.vehicle_id)}>
                  {alert.vehicle_id}
                </button>
              </div>
              <p className="summary-item-title">{alert.reason}</p>
            </li>
          ))}
        </SummaryList>
      </section>
    </>
  );
}
