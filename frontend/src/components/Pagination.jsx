import { formatNumber } from "../utils/format.js";

export default function Pagination({ page, pageSize, total, onPageChange }) {
  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  const firstItem = total === 0 ? 0 : (page - 1) * pageSize + 1;
  const lastItem = Math.min(page * pageSize, total);

  return (
    <div className="pagination">
      <p>
        Showing {formatNumber(firstItem)}–{formatNumber(lastItem)} of {formatNumber(total)}
      </p>
      <div className="pagination-controls">
        <button
          type="button"
          className="button"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          Previous
        </button>
        <span className="pagination-page">
          Page {page} of {formatNumber(pageCount)}
        </span>
        <button
          type="button"
          className="button"
          disabled={page >= pageCount}
          onClick={() => onPageChange(page + 1)}
        >
          Next
        </button>
      </div>
    </div>
  );
}
