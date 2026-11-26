import { formatCurrency } from "../utils/format.js";
import { priorityTone } from "../utils/tones.js";
import Badge from "./Badge.jsx";

export default function RecommendationCard({ recommendation, onSelectVehicle }) {
  return (
    <article className="card recommendation-card">
      <div className="recommendation-top">
        <div className="badge-row">
          <Badge tone={priorityTone(recommendation.priority)}>{recommendation.priority}</Badge>
          <Badge tone="blue">{recommendation.category}</Badge>
        </div>
        <button
          type="button"
          className="link-button"
          onClick={() => onSelectVehicle(recommendation.vehicle_id)}
        >
          {recommendation.vehicle_id}
        </button>
      </div>
      <h3>{recommendation.title}</h3>
      <p className="recommendation-reason">{recommendation.reason}</p>
      {recommendation.estimated_annual_saving_inr > 0 && (
        <p className="recommendation-saving">
          Estimated saving{" "}
          <strong>{formatCurrency(recommendation.estimated_annual_saving_inr)}</strong> per year
        </p>
      )}
      <p className="recommendation-action">
        <span>Suggested action</span>
        {recommendation.suggested_action}
      </p>
    </article>
  );
}
