import { useEffect } from "react";
import { useApi } from "../hooks/useApi.js";
import { getVehicle } from "../services/api.js";
import {
  formatCurrency,
  formatDate,
  formatEnergyPer100Km,
  formatKilometres,
  formatKilowattHours,
  formatMonth,
  formatNumber,
  formatPercentValue,
} from "../utils/format.js";
import { SCORE_COMPONENT_LABELS } from "../utils/labels.js";
import { priorityTone, riskLevelTone, statusTone } from "../utils/tones.js";
import Badge from "./Badge.jsx";
import Icon from "./Icons.jsx";
import ScoreBar from "./ScoreBar.jsx";
import { ErrorState, LoadingState } from "./StateMessages.jsx";

function ScoreSection({ title, value, inverse, kind, components }) {
  const labels = SCORE_COMPONENT_LABELS[kind];
  return (
    <section className="score-section">
      <h3>{title}</h3>
      <ScoreBar value={value} inverse={inverse} />
      <ul className="component-list">
        {Object.entries(components).map(([name, componentValue]) => (
          <li key={name}>
            <span>{labels[name] ?? name}</span>
            <span className="component-value">{componentValue.toFixed(1)}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function FactList({ vehicle }) {
  const facts = [
    ["Manufacturing year", `${vehicle.manufacturing_year} (${vehicle.age_years} years)`],
    ["Retrofit date", `${formatDate(vehicle.retrofit_date)} (${vehicle.retrofit_age_years} years ago)`],
    ["Distance since retrofit", formatKilometres(vehicle.total_distance_km)],
    ["Monthly distance", formatKilometres(vehicle.monthly_distance_km)],
    ["Battery capacity", formatKilowattHours(vehicle.battery_capacity_kwh)],
    ["Battery health", formatPercentValue(vehicle.battery_health_pct)],
    ["Motor health", formatPercentValue(vehicle.motor_health_pct)],
    ["Electrical system health", formatPercentValue(vehicle.electrical_health_pct)],
    ["Energy consumption", formatEnergyPer100Km(vehicle.energy_consumption_kwh_per_100km)],
    ["Charge cycles", formatNumber(vehicle.charge_cycles)],
    ["Fast charging share", formatPercentValue(vehicle.fast_charge_pct)],
    ["Utilization", formatPercentValue(vehicle.utilization_pct)],
    ["Maintenance cost", formatCurrency(vehicle.maintenance_cost_inr)],
    ["Monthly operating cost", formatCurrency(vehicle.operating_cost_inr)],
    ["Breakdowns", formatNumber(vehicle.breakdowns)],
    ["Accidents", formatNumber(vehicle.accidents)],
    ["Maintenance status", vehicle.maintenance_status],
    ["Condition", vehicle.vehicle_condition],
  ];
  return (
    <dl className="fact-grid">
      {facts.map(([label, value]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function VehicleDetailContent({ vehicle }) {
  return (
    <>
      <div className="score-grid">
        <ScoreSection
          title="Health score"
          kind="health"
          value={vehicle.health_score}
          components={vehicle.score_breakdown.health}
        />
        <ScoreSection
          title="Efficiency score"
          kind="efficiency"
          value={vehicle.efficiency_score}
          components={vehicle.score_breakdown.efficiency}
        />
        <ScoreSection
          title="Risk score"
          kind="risk"
          inverse
          value={vehicle.risk_score}
          components={vehicle.score_breakdown.risk}
        />
      </div>

      <h3 className="detail-heading">Vehicle information</h3>
      <FactList vehicle={vehicle} />

      <h3 className="detail-heading">Recommendations</h3>
      {vehicle.recommendations.length === 0 ? (
        <p className="muted">No recommendations. This vehicle meets all rule thresholds.</p>
      ) : (
        <ul className="detail-list">
          {vehicle.recommendations.map((item) => (
            <li key={item.id}>
              <div className="badge-row">
                <Badge tone={priorityTone(item.priority)}>{item.priority}</Badge>
                <Badge tone="blue">{item.category}</Badge>
              </div>
              <p className="detail-list-title">{item.title}</p>
              <p className="muted">{item.reason}</p>
              <p>{item.suggested_action}</p>
              {item.estimated_annual_saving_inr > 0 && (
                <p className="recommendation-saving">
                  Estimated saving <strong>{formatCurrency(item.estimated_annual_saving_inr)}</strong> per year
                </p>
              )}
            </li>
          ))}
        </ul>
      )}

      {vehicle.risk_alerts.length > 0 && (
        <>
          <h3 className="detail-heading">Risk alert</h3>
          <ul className="detail-list">
            {vehicle.risk_alerts.map((alert) => (
              <li key={alert.id}>
                <Badge tone={riskLevelTone(alert.risk_level)}>{alert.risk_level} risk</Badge>
                <p className="detail-list-title">{alert.reason}</p>
                <p>{alert.recommended_action}</p>
              </li>
            ))}
          </ul>
        </>
      )}

      <h3 className="detail-heading">Maintenance history</h3>
      <div className="table-wrapper detail-table">
        <table className="data-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Service</th>
              <th>Cost</th>
            </tr>
          </thead>
          <tbody>
            {vehicle.maintenance_records.map((record, index) => (
              <tr key={`${record.service_date}-${index}`}>
                <td>{formatDate(record.service_date)}</td>
                <td>
                  {record.service_type}
                  {record.is_breakdown_repair && <span className="inline-tag">Breakdown</span>}
                </td>
                <td>{formatCurrency(record.cost_inr)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h3 className="detail-heading">Monthly trips</h3>
      <div className="table-wrapper detail-table">
        <table className="data-table">
          <thead>
            <tr>
              <th>Month</th>
              <th>Trips</th>
              <th>Distance</th>
              <th>Energy used</th>
              <th>Energy cost</th>
            </tr>
          </thead>
          <tbody>
            {vehicle.trips.map((trip) => (
              <tr key={trip.trip_month}>
                <td>{formatMonth(trip.trip_month)}</td>
                <td>{formatNumber(trip.trips_count)}</td>
                <td>{formatKilometres(trip.distance_km)}</td>
                <td>{formatKilowattHours(trip.energy_consumed_kwh)}</td>
                <td>{formatCurrency(trip.energy_cost_inr)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

export default function VehicleDetailPanel({ vehicleId, onClose }) {
  const { data: vehicle, loading, error, reload } = useApi(() => getVehicle(vehicleId), [vehicleId]);

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div className="overlay" onClick={onClose}>
      <aside
        className="detail-panel"
        role="dialog"
        aria-modal="true"
        aria-label={`Details for ${vehicleId}`}
        onClick={(event) => event.stopPropagation()}
      >
        <header className="detail-header">
          <div>
            <h2>{vehicleId}</h2>
            {vehicle && (
              <p className="muted">
                Electric {vehicle.vehicle_type.toLowerCase()} · {vehicle.vehicle_condition} condition
              </p>
            )}
          </div>
          <div className="detail-header-actions">
            {vehicle && <Badge tone={statusTone(vehicle.status)}>{vehicle.status}</Badge>}
            <button type="button" className="icon-button" aria-label="Close details" onClick={onClose}>
              <Icon name="close" />
            </button>
          </div>
        </header>
        <div className="detail-body">
          {loading && !vehicle && <LoadingState message="Loading vehicle details…" />}
          {error && <ErrorState message={error} onRetry={reload} />}
          {vehicle && <VehicleDetailContent vehicle={vehicle} />}
        </div>
      </aside>
    </div>
  );
}
