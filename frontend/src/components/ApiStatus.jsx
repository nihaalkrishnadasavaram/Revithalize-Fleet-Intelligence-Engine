import { getHealth } from "../services/api.js";
import { useApi } from "../hooks/useApi.js";

export default function ApiStatus() {
  const { data, loading, error } = useApi(getHealth);

  if (loading && !data) {
    return <p className="api-status">Checking API…</p>;
  }
  if (error) {
    return (
      <p className="api-status api-status-offline">
        <span className="status-dot" />
        API offline
      </p>
    );
  }
  return (
    <p className="api-status api-status-online">
      <span className="status-dot" />
      API connected
    </p>
  );
}
