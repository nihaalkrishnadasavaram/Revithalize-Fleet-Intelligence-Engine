import { useState } from "react";
import Badge from "../components/Badge.jsx";
import PageHeader from "../components/PageHeader.jsx";
import Pagination from "../components/Pagination.jsx";
import ScoreBar from "../components/ScoreBar.jsx";
import { EmptyState, ErrorState, LoadingState } from "../components/StateMessages.jsx";
import { useApi } from "../hooks/useApi.js";
import { getAlerts } from "../services/api.js";
import { formatNumber } from "../utils/format.js";
import { riskLevelTone } from "../utils/tones.js";

const PAGE_SIZE = 10;

export default function AlertsPage({ onSelectVehicle }) {
  const [page, setPage] = useState(1);
  const { data, loading, error, reload } = useApi(
    () => getAlerts({ page, page_size: PAGE_SIZE }),
    [page]
  );

  const subtitle = data
    ? `${formatNumber(data.total)} vehicles with an operational risk score of 70 or higher`
    : "Vehicles with an operational risk score of 70 or higher";

  return (
    <>
      <PageHeader title="Risk Alerts" subtitle={subtitle} />

      {loading && !data && <LoadingState message="Loading risk alerts…" />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {data && data.items.length === 0 && (
        <EmptyState
          title="No active risk alerts"
          message="No vehicle currently exceeds the high-risk threshold."
        />
      )}
      {data && data.items.length > 0 && (
        <section className="card">
          <div className={loading ? "table-wrapper table-loading" : "table-wrapper"}>
            <table className="data-table alerts-table">
              <thead>
                <tr>
                  <th>Vehicle ID</th>
                  <th>Risk Score</th>
                  <th>Risk Level</th>
                  <th>Reason for Alert</th>
                  <th>Recommended Action</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((alert) => (
                  <tr
                    key={alert.id}
                    className="clickable-row"
                    onClick={() => onSelectVehicle(alert.vehicle_id)}
                  >
                    <td>
                      <button
                        type="button"
                        className="link-button"
                        onClick={(event) => {
                          event.stopPropagation();
                          onSelectVehicle(alert.vehicle_id);
                        }}
                      >
                        {alert.vehicle_id}
                      </button>
                    </td>
                    <td>
                      <ScoreBar value={alert.risk_score} inverse />
                    </td>
                    <td>
                      <Badge tone={riskLevelTone(alert.risk_level)}>{alert.risk_level}</Badge>
                    </td>
                    <td className="wrap-cell">{alert.reason}</td>
                    <td className="wrap-cell">{alert.recommended_action}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page} pageSize={PAGE_SIZE} total={data.total} onPageChange={setPage} />
        </section>
      )}
    </>
  );
}
