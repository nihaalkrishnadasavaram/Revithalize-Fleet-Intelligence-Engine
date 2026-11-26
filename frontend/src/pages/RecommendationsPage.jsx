import { useState } from "react";
import PageHeader from "../components/PageHeader.jsx";
import Pagination from "../components/Pagination.jsx";
import RecommendationCard from "../components/RecommendationCard.jsx";
import { EmptyState, ErrorState, LoadingState } from "../components/StateMessages.jsx";
import { useApi } from "../hooks/useApi.js";
import { getRecommendations } from "../services/api.js";
import { formatCurrency } from "../utils/format.js";
import { RECOMMENDATION_CATEGORIES } from "../utils/labels.js";

const PAGE_SIZE = 12;
const PRIORITY_OPTIONS = ["High", "Medium", "Low"];

export default function RecommendationsPage({ onSelectVehicle }) {
  const [category, setCategory] = useState("");
  const [priority, setPriority] = useState("");
  const [page, setPage] = useState(1);

  const { data, loading, error, reload } = useApi(
    () => getRecommendations({ category, priority, page, page_size: PAGE_SIZE }),
    [category, priority, page]
  );

  const selectCategory = (value) => {
    setCategory(value);
    setPage(1);
  };

  const handlePriorityChange = (event) => {
    setPriority(event.target.value);
    setPage(1);
  };

  const savingNote =
    data && data.total_estimated_annual_saving_inr > 0
      ? ` · Estimated annual saving ${formatCurrency(data.total_estimated_annual_saving_inr)}`
      : "";

  return (
    <>
      <PageHeader
        title="Recommendations"
        subtitle={`Rule-based actions generated from vehicle data and scores${savingNote}`}
      />

      <div className="toolbar toolbar-spread">
        <div className="chip-group" role="group" aria-label="Filter by category">
          {["", ...RECOMMENDATION_CATEGORIES].map((option) => (
            <button
              key={option || "all"}
              type="button"
              className={option === category ? "chip chip-active" : "chip"}
              onClick={() => selectCategory(option)}
            >
              {option || "All categories"}
            </button>
          ))}
        </div>
        <select
          className="input"
          value={priority}
          onChange={handlePriorityChange}
          aria-label="Filter by priority"
        >
          <option value="">All priorities</option>
          {PRIORITY_OPTIONS.map((option) => (
            <option key={option} value={option}>
              {option} priority
            </option>
          ))}
        </select>
      </div>

      {loading && !data && <LoadingState message="Loading recommendations…" />}
      {error && <ErrorState message={error} onRetry={reload} />}
      {data && data.items.length === 0 && (
        <EmptyState
          title="No recommendations found"
          message="No recommendations match the selected filters."
        />
      )}
      {data && data.items.length > 0 && (
        <>
          <section className={loading ? "recommendation-grid table-loading" : "recommendation-grid"}>
            {data.items.map((item) => (
              <RecommendationCard
                key={item.id}
                recommendation={item}
                onSelectVehicle={onSelectVehicle}
              />
            ))}
          </section>
          <div className="card pagination-card">
            <Pagination page={page} pageSize={PAGE_SIZE} total={data.total} onPageChange={setPage} />
          </div>
        </>
      )}
    </>
  );
}
