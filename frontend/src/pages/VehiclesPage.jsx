import { useState } from "react";
import PageHeader from "../components/PageHeader.jsx";
import Pagination from "../components/Pagination.jsx";
import { EmptyState, ErrorState, LoadingState } from "../components/StateMessages.jsx";
import VehicleTable from "../components/VehicleTable.jsx";
import { useApi } from "../hooks/useApi.js";
import { useDebouncedValue } from "../hooks/useDebouncedValue.js";
import { exportUrl, getVehicles } from "../services/api.js";
import { VEHICLE_STATUS_OPTIONS, VEHICLE_TYPE_OPTIONS } from "../utils/labels.js";

const PAGE_SIZE = 15;

export default function VehiclesPage({ onSelectVehicle }) {
  const [searchText, setSearchText] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const search = useDebouncedValue(searchText.trim());

  const { data, loading, error, reload } = useApi(
    () =>
      getVehicles({
        search,
        vehicle_type: typeFilter,
        status: statusFilter,
        page,
        page_size: PAGE_SIZE,
      }),
    [search, typeFilter, statusFilter, page]
  );

  const handleSearchChange = (event) => {
    setSearchText(event.target.value);
    setPage(1);
  };

  const handleTypeChange = (event) => {
    setTypeFilter(event.target.value);
    setPage(1);
  };

  const handleStatusChange = (event) => {
    setStatusFilter(event.target.value);
    setPage(1);
  };

  return (
    <>
      <PageHeader title="Vehicles" subtitle="Search the electric motorcycles and scooters and open one for full details">
        <a className="button" href={exportUrl} download="synthetic_fleet_data.csv">
          Export CSV
        </a>
      </PageHeader>

      <section className="card">
        <div className="toolbar">
          <input
            type="search"
            className="input"
            placeholder="Search by vehicle ID or type"
            value={searchText}
            onChange={handleSearchChange}
            aria-label="Search vehicles"
          />
          <select
            className="input"
            value={typeFilter}
            onChange={handleTypeChange}
            aria-label="Filter by vehicle type"
          >
            <option value="">All vehicle types</option>
            {VEHICLE_TYPE_OPTIONS.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
          <select
            className="input"
            value={statusFilter}
            onChange={handleStatusChange}
            aria-label="Filter by status"
          >
            <option value="">All statuses</option>
            {VEHICLE_STATUS_OPTIONS.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </div>

        {loading && !data && <LoadingState message="Loading vehicles…" />}
        {error && <ErrorState message={error} onRetry={reload} />}
        {data && data.items.length === 0 && (
          <EmptyState
            title="No vehicles found"
            message="Try a different search term or filter."
          />
        )}
        {data && data.items.length > 0 && (
          <>
            <div className={loading ? "table-loading" : undefined}>
              <VehicleTable vehicles={data.items} onSelectVehicle={onSelectVehicle} />
            </div>
            <Pagination
              page={page}
              pageSize={PAGE_SIZE}
              total={data.total}
              onPageChange={setPage}
            />
          </>
        )}
      </section>
    </>
  );
}
