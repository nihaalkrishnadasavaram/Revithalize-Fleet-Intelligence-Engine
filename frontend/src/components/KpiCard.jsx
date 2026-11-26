export default function KpiCard({ label, value, hint, tone = "blue" }) {
  return (
    <article className={`card kpi-card kpi-${tone}`}>
      <p className="kpi-label">{label}</p>
      <p className="kpi-value">{value}</p>
      {hint && <p className="kpi-hint">{hint}</p>}
    </article>
  );
}
