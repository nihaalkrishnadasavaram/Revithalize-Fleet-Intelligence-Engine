import { formatNumber } from "../utils/format.js";

export default function DistributionBar({ title, segments }) {
  const total = segments.reduce((sum, segment) => sum + segment.value, 0);

  return (
    <article className="card distribution-card">
      <h2 className="card-title">{title}</h2>
      <div className="distribution-bar" role="img" aria-label={title}>
        {segments.map((segment) =>
          segment.value > 0 ? (
            <div
              key={segment.label}
              className={`distribution-segment fill-${segment.tone}`}
              style={{ width: `${(segment.value / total) * 100}%` }}
            />
          ) : null
        )}
      </div>
      <ul className="distribution-legend">
        {segments.map((segment) => (
          <li key={segment.label}>
            <span className={`legend-dot fill-${segment.tone}`} />
            <span className="legend-label">{segment.label}</span>
            <span className="legend-value">
              {formatNumber(segment.value)}
              <span className="legend-percent">
                {total > 0 ? ` (${Math.round((segment.value / total) * 100)}%)` : ""}
              </span>
            </span>
          </li>
        ))}
      </ul>
    </article>
  );
}
