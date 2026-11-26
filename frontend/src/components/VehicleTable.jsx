import { formatCurrency, formatKilometres, formatKilowattHours } from "../utils/format.js";
import { statusTone } from "../utils/tones.js";
import Badge from "./Badge.jsx";
import ScoreBar from "./ScoreBar.jsx";

export default function VehicleTable({ vehicles, onSelectVehicle, compact = false }) {
  return (
    <div className="table-wrapper">
      <table className={compact ? "data-table" : "data-table data-table-wide"}>
        <thead>
          <tr>
            <th>Vehicle ID</th>
            <th>Type</th>
            <th>Total Distance</th>
            {!compact && <th>Energy (kWh/100 km)</th>}
            {!compact && <th>Battery Health (%)</th>}
            {!compact && <th>Maintenance Cost</th>}
            <th>Health</th>
            <th>Efficiency</th>
            <th>Risk</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {vehicles.map((vehicle) => (
            <tr
              key={vehicle.vehicle_id}
              className="clickable-row"
              onClick={() => onSelectVehicle(vehicle.vehicle_id)}
            >
              <td>
                <button
                  type="button"
                  className="link-button"
                  onClick={(event) => {
                    event.stopPropagation();
                    onSelectVehicle(vehicle.vehicle_id);
                  }}
                >
                  {vehicle.vehicle_id}
                </button>
              </td>
              <td>{vehicle.vehicle_type}</td>
              <td>{formatKilometres(vehicle.total_distance_km)}</td>
              {!compact && <td>{vehicle.energy_consumption_kwh_per_100km.toFixed(2)}</td>}
              {!compact && (
                <td>
                  <ScoreBar value={vehicle.battery_health_pct} />
                  <span className="cell-note">{formatKilowattHours(vehicle.battery_capacity_kwh)}</span>
                </td>
              )}
              {!compact && <td>{formatCurrency(vehicle.maintenance_cost_inr)}</td>}
              <td>
                <ScoreBar value={vehicle.health_score} />
              </td>
              <td>
                <ScoreBar value={vehicle.efficiency_score} />
              </td>
              <td>
                <ScoreBar value={vehicle.risk_score} inverse />
              </td>
              <td>
                <Badge tone={statusTone(vehicle.status)}>{vehicle.status}</Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
